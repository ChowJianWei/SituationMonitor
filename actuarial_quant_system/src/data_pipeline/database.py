"""
database.py
===========
Durable historical / audit store (PostgreSQL via asyncpg).

Fail-soft by design: if asyncpg is not installed or the database is unreachable,
the layer degrades to an in-memory store so the whole system still boots and runs
(useful for local dev, demos, and tests). Production deployments point
POSTGRES_DSN at a real instance and run db/schema.sql first.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("database")

try:
    import asyncpg  # type: ignore
except Exception:  # pragma: no cover
    asyncpg = None  # type: ignore

_SCHEMA_PATH = Path(__file__).resolve().parents[2] / "db" / "schema.sql"


class Database:
    """Thin async repository over PostgreSQL with an in-memory fallback."""

    def __init__(self, dsn: str):
        self._dsn = dsn
        self._pool: Optional["asyncpg.Pool"] = None
        # In-memory mirrors used when Postgres is unavailable.
        self._mem: dict[str, list[dict[str, Any]]] = {
            "trades": [], "positions": [], "daily_briefings": [],
            "regime_snapshots": [], "audit_log": [],
        }

    @property
    def live(self) -> bool:
        return self._pool is not None

    async def connect(self) -> None:
        if asyncpg is None:
            logger.warning("asyncpg not installed; using in-memory store.")
            return
        try:
            self._pool = await asyncpg.create_pool(self._dsn, min_size=1, max_size=5)
            await self._ensure_schema()
            logger.info("PostgreSQL connected.")
        except Exception as exc:  # pragma: no cover
            logger.warning("Postgres unavailable (%s); using in-memory store.", exc)
            self._pool = None

    async def _ensure_schema(self) -> None:
        if self._pool is None or not _SCHEMA_PATH.exists():
            return
        ddl = _SCHEMA_PATH.read_text()
        async with self._pool.acquire() as conn:
            await conn.execute(ddl)

    # ----- writes -------------------------------------------------------
    async def write_audit(self, actor: str, event: str, detail: dict | None = None) -> None:
        row = {"ts": datetime.now(timezone.utc).isoformat(), "actor": actor,
               "event": event, "detail": detail or {}}
        if self._pool is None:
            self._mem["audit_log"].append(row)
            return
        async with self._pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO audit_log(actor, event, detail) VALUES($1,$2,$3)",
                actor, event, json.dumps(detail or {}),
            )

    async def save_trade(self, trade: dict) -> None:
        if self._pool is None:
            self._mem["trades"].append(trade)
            return
        async with self._pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO trades(account_id, symbol, structure, side, notional_usd,
                       fill_price, slippage_usd, fee_usd, paper, risk_verdict, rationale)
                   VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)""",
                trade.get("account_id"), trade["symbol"], trade["structure"], trade["side"],
                trade["notional_usd"], trade["fill_price"], trade.get("slippage_usd", 0),
                trade.get("fee_usd", 0), trade.get("paper", True),
                trade["risk_verdict"], trade.get("rationale", ""),
            )

    async def upsert_position(self, pos: dict) -> None:
        if self._pool is None:
            self._mem["positions"].append(pos)
            return
        async with self._pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO positions(account_id, symbol, structure, side, notional_usd,
                       entry_price, delta, gamma, vega, theta, loss_reserve_usd, status)
                   VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,'OPEN')""",
                pos.get("account_id"), pos["symbol"], pos["structure"], pos["side"],
                pos["notional_usd"], pos.get("entry_price"), pos.get("delta", 0),
                pos.get("gamma", 0), pos.get("vega", 0), pos.get("theta", 0),
                pos.get("loss_reserve_usd", 0),
            )

    async def save_briefing(self, account_id: Optional[int], briefing: dict) -> None:
        if self._pool is None:
            self._mem["daily_briefings"].append(briefing)
            return
        async with self._pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO daily_briefings(account_id, surplus_health_index,
                       net_earnings_24h_usd, regime, ruin_probability, expected_shortfall_99,
                       free_capital_usd, frozen_reserve_usd, payload)
                   VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9)""",
                account_id, briefing.get("surplus_health_index"),
                briefing.get("net_earnings_24h_usd"), briefing.get("regime"),
                briefing.get("ruin_probability"), briefing.get("expected_shortfall_99"),
                briefing.get("free_capital_usd"), briefing.get("frozen_reserve_usd"),
                json.dumps(briefing),
            )

    async def save_regime_snapshot(self, snap: dict) -> None:
        if self._pool is None:
            self._mem["regime_snapshots"].append(snap)
            return
        async with self._pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO regime_snapshots(regime, garch_vol, garch_forecast, payload)
                   VALUES($1,$2,$3,$4)""",
                snap.get("regime"), snap.get("garch_vol"),
                snap.get("garch_forecast"), json.dumps(snap),
            )

    # ----- reads --------------------------------------------------------
    async def get_open_positions(self, account_id: Optional[int] = None) -> list[dict]:
        if self._pool is None:
            return [p for p in self._mem["positions"] if p.get("status", "OPEN") == "OPEN"]
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM positions WHERE status='OPEN' "
                "AND ($1::bigint IS NULL OR account_id=$1)", account_id,
            )
            return [dict(r) for r in rows]

    async def get_recent_trades(self, limit: int = 50) -> list[dict]:
        if self._pool is None:
            return self._mem["trades"][-limit:]
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM trades ORDER BY executed_at DESC LIMIT $1", limit
            )
            return [dict(r) for r in rows]

    async def get_latest_briefing(self) -> Optional[dict]:
        if self._pool is None:
            return self._mem["daily_briefings"][-1] if self._mem["daily_briefings"] else None
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT payload FROM daily_briefings ORDER BY as_of DESC LIMIT 1"
            )
            return json.loads(row["payload"]) if row else None

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
