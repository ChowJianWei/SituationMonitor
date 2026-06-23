"""
state_store.py
==============
Live, real-time portfolio state backed by Redis.

This is the component that fixes the "state preservation blindspot": loss
reserves and account surplus are written to Redis the instant they change, so a
daemon crash + restart restores the exact live picture within milliseconds
(reconciled against open positions in PostgreSQL). Built on top of StreamBus,
which already provides a Redis layer with an in-process fallback.
"""

from __future__ import annotations

import logging
from typing import Optional

from .stream_bus import KEY_LOSS_RESERVE, StreamBus

logger = logging.getLogger("state_store")

KEY_ACCOUNT = "state:account"
KEY_RESERVE_INDEX = "state:reserve_index"   # set of symbols with active reserves


class StateStore:
    """Loss-reserve and surplus state with durable Redis persistence."""

    def __init__(self, bus: StreamBus):
        self._bus = bus

    # ----- loss reserves -----------------------------------------------
    async def lock_loss_reserve(self, symbol: str, amount_usd: float) -> None:
        """Freeze cash as a loss reserve backing an active liability."""
        await self._bus.set_state(KEY_LOSS_RESERVE.format(symbol=symbol), amount_usd)
        idx = set(await self._bus.get_state(KEY_RESERVE_INDEX) or [])
        idx.add(symbol)
        await self._bus.set_state(KEY_RESERVE_INDEX, sorted(idx))
        logger.info("Locked loss reserve %s = $%.2f", symbol, amount_usd)

    async def release_loss_reserve(self, symbol: str) -> None:
        await self._bus.set_state(KEY_LOSS_RESERVE.format(symbol=symbol), 0.0)
        idx = set(await self._bus.get_state(KEY_RESERVE_INDEX) or [])
        idx.discard(symbol)
        await self._bus.set_state(KEY_RESERVE_INDEX, sorted(idx))

    async def get_loss_reserve(self, symbol: str) -> float:
        v = await self._bus.get_state(KEY_LOSS_RESERVE.format(symbol=symbol))
        return float(v or 0.0)

    async def total_locked_reserves(self) -> float:
        idx = await self._bus.get_state(KEY_RESERVE_INDEX) or []
        total = 0.0
        for symbol in idx:
            total += await self.get_loss_reserve(symbol)
        return total

    # ----- account surplus ---------------------------------------------
    async def set_account(self, equity_usd: float, start_of_day_equity_usd: float,
                          open_gross_notional_usd: float = 0.0) -> None:
        await self._bus.set_state(KEY_ACCOUNT, {
            "equity_usd": equity_usd,
            "start_of_day_equity_usd": start_of_day_equity_usd,
            "open_gross_notional_usd": open_gross_notional_usd,
        })

    async def get_account(self) -> Optional[dict]:
        return await self._bus.get_state(KEY_ACCOUNT)

    async def restore_or_seed(self, seed_equity: float) -> dict:
        """On boot: restore account state from Redis, or seed it if absent."""
        state = await self.get_account()
        if state is None:
            await self.set_account(seed_equity, seed_equity, 0.0)
            state = await self.get_account()
            logger.info("Seeded fresh account state at $%.2f", seed_equity)
        else:
            logger.info("Restored account state from Redis: $%.2f equity",
                        state.get("equity_usd", 0.0))
        return state  # type: ignore[return-value]
