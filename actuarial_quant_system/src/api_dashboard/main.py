"""
main.py
=======
FastAPI orchestration layer for the Actuarial Quant System.

Exposes the read-only / informational endpoints the Next.js visual portal calls
on demand. The heavy 24/7 work (feed ingestion) runs in the background lifespan
task; the HTTP layer just reads computed state and runs the actuarial math.

Endpoints
---------
  GET  /health                         liveness
  GET  /api/v1/daily-briefing          morning executive report payload
  GET  /api/v1/fund-allocation         per-asset capital role breakdown
  GET  /api/v1/regime                  HMM/GARCH regime + vol snapshot
  GET  /api/v1/risk/ruin               Cramer-Lundberg ruin probability
  POST /api/v1/reallocate              propose reallocation / deposit advice
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from datetime import datetime, timezone
from typing import List, Optional

import numpy as np
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ..config import settings
from ..data_pipeline.stream_bus import StreamBus
from ..models.actuarial_engine import (
    TradeMetrics,
    compute_loss_reserve,
    fit_gpd_tail_risk,
    simulate_ruin_probability,
)
from ..models.regime_models import detect_regime, fit_garch
from ..risk_gate.pre_trade_check import (
    AccountState,
    TradeIntent,
    check_trade,
    kill_switch_status,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api_dashboard")

app = FastAPI(title="Actuarial Quant System", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origin],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Shared bus instance, wired up in the lifespan.
bus = StreamBus(settings.redis_url)


# ---------------------------------------------------------------------------
# Lifespan: launch the 24/7 background pipeline.
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def _startup() -> None:
    await bus.connect()
    # The feed consumer runs forever; it is supervised here and restarted by
    # systemd if the whole process dies. ws_url is illustrative.
    app.state.feed_task = asyncio.create_task(
        bus.consume_feed("wss://sandbox.exchange.local/stream")
    )
    logger.info("Actuarial engine online (paper_only=%s).", settings.paper_trading_only)


@app.on_event("shutdown")
async def _shutdown() -> None:
    task = getattr(app.state, "feed_task", None)
    if task:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
    await bus.aclose()


# ---------------------------------------------------------------------------
# Demo state helpers
# ---------------------------------------------------------------------------
# In production these come from Redis (live) / Postgres (history). For a runnable
# scaffold we synthesize a plausible book so every endpoint returns real numbers.
def _demo_returns(seed: int = 1, n: int = 1500) -> np.ndarray:
    rng = np.random.default_rng(seed)
    # Mixture: calm regime + occasional stress bursts (fat tails).
    calm = rng.normal(0.0003, 0.01, n)
    shocks = rng.normal(-0.01, 0.05, n) * (rng.random(n) < 0.05)
    return calm + shocks


def _demo_account() -> AccountState:
    return AccountState(
        equity_usd=180_000.0,
        open_gross_notional_usd=120_000.0,
        frozen_reserve_usd=42_000.0,
        start_of_day_equity_usd=182_500.0,
    )


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class ReallocateRequest(BaseModel):
    asset: str
    target_yield_layer_usd: float
    target_reserve_layer_usd: float
    target_hedge_layer_usd: float


class ReallocateResponse(BaseModel):
    asset: str
    accepted: bool
    available_free_capital_usd: float
    shortfall_usd: float
    deposit_advice: Optional[str]
    notes: List[str]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "paper_trading_only": settings.paper_trading_only,
        "kill_switch_engaged": kill_switch_status(),
        "ts": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/v1/regime")
async def regime() -> dict:
    r = _demo_returns()
    garch = fit_garch(r)
    reg = detect_regime(r, n_states=3)
    return {"garch": garch.as_dict(), "regime": reg.as_dict()}


@app.get("/api/v1/risk/ruin")
async def ruin() -> dict:
    account = _demo_account()
    metrics = TradeMetrics(
        trades_per_step=1.0, win_rate=0.56, avg_win=420.0, avg_loss=510.0
    )
    result = simulate_ruin_probability(
        surplus=account.equity_usd - account.frozen_reserve_usd,
        metrics=metrics,
        horizon=10_000,
        n_paths=1_500,
    )
    return result.as_dict()


@app.get("/api/v1/daily-briefing")
async def daily_briefing() -> dict:
    """
    Structured payload for the user's morning executive report (Tab 1).
    Combines surplus health, regime state, ruin probability and tail risk into
    a single narrative + metrics object the frontend renders directly.
    """
    account = _demo_account()
    free_capital = account.equity_usd - account.frozen_reserve_usd

    returns = _demo_returns()
    losses = -returns[returns < 0]  # positive loss magnitudes
    tail = fit_gpd_tail_risk(losses, confidence=0.99, threshold_quantile=0.95)
    regime_snapshot = detect_regime(returns, n_states=3)

    metrics = TradeMetrics(
        trades_per_step=1.0, win_rate=0.56, avg_win=420.0, avg_loss=510.0
    )
    ruin_result = simulate_ruin_probability(
        surplus=free_capital, metrics=metrics, horizon=10_000, n_paths=1_500
    )

    # Surplus Health Index: 0-100, blends drawdown headroom and ruin safety.
    dd_headroom = max(0.0, 1.0 - ruin_result.ruin_probability)
    reserve_health = min(1.0, free_capital / max(account.equity_usd, 1e-9))
    surplus_health_index = round(100 * (0.6 * dd_headroom + 0.4 * reserve_health), 1)

    pnl_24h = account.equity_usd - account.start_of_day_equity_usd

    narrative = [
        f"Active market regime classified as {regime_snapshot.current_regime}.",
        f"99% one-step Expected Shortfall (CVaR) on losses is "
        f"{tail.cvar:.2%} of notional; tail index xi={tail.xi:.2f}.",
        f"Modelled ruin probability over a 10,000-step horizon is "
        f"{ruin_result.ruin_probability:.3%}.",
        f"Free (unfrozen) capital is ${free_capital:,.0f}; "
        f"${account.frozen_reserve_usd:,.0f} is locked as loss reserves.",
        "Underwriting posture: informational/paper only — no live execution."
        if settings.paper_trading_only else "Underwriting posture: live, risk-gated.",
    ]

    return {
        "as_of": datetime.now(timezone.utc).isoformat(),
        "surplus_health_index": surplus_health_index,
        "net_earnings_24h_usd": round(pnl_24h, 2),
        "regime": regime_snapshot.current_regime,
        "regime_probabilities": dict(
            zip(regime_snapshot.regime_labels, regime_snapshot.state_probabilities)
        ),
        "ruin_probability": ruin_result.ruin_probability,
        "expected_shortfall_99": tail.cvar,
        "value_at_risk_99": tail.var,
        "free_capital_usd": round(free_capital, 2),
        "frozen_reserve_usd": round(account.frozen_reserve_usd, 2),
        "kill_switch_engaged": kill_switch_status(),
        "executive_narrative": narrative,
    }


@app.get("/api/v1/fund-allocation")
async def fund_allocation() -> dict:
    """
    Per-asset capital broken into its three functional roles (Tab 2):
      * yield_generation : capital deployed in active derivative positions
      * loss_reserve     : frozen cash backing margin (from compute_loss_reserve)
      * delta_hedge      : spot holdings keeping directional risk neutral
    """
    book = [
        {"asset": "BTC", "notional": 90_000.0, "margin_rate": 0.10, "spot_hedge": 38_000.0},
        {"asset": "ETH", "notional": 60_000.0, "margin_rate": 0.12, "spot_hedge": 21_000.0},
        {"asset": "EQUITIES", "notional": 40_000.0, "margin_rate": 0.20, "spot_hedge": 15_000.0},
    ]
    # CVaR fraction reused from the global tail fit as the actuarial claim size.
    returns = _demo_returns()
    losses = -returns[returns < 0]
    cvar_fraction = fit_gpd_tail_risk(losses, 0.99, 0.95).cvar

    allocations = []
    for pos in book:
        reserve = compute_loss_reserve(
            notional=pos["notional"],
            margin_rate=pos["margin_rate"],
            cvar_fraction=cvar_fraction,
        )
        allocations.append({
            "asset": pos["asset"],
            "yield_generation_usd": round(pos["notional"], 2),
            "loss_reserve_usd": round(reserve.required_reserve, 2),
            "delta_hedge_usd": round(pos["spot_hedge"], 2),
            "reserve_ratio": round(reserve.reserve_ratio, 4),
        })

    return {"as_of": datetime.now(timezone.utc).isoformat(), "allocations": allocations}


@app.post("/api/v1/reallocate", response_model=ReallocateResponse)
async def reallocate(req: ReallocateRequest) -> ReallocateResponse:
    """
    Propose a reallocation across the three layers for one asset. If the internal
    free-cash pool cannot fund the target, the system issues DEPOSIT ADVICE
    rather than auto-borrowing or breaching reserve floors.

    This endpoint NEVER moves external money. It only computes whether the
    requested internal split is fundable and, if not, advises the human how much
    to deposit manually.
    """
    account = _demo_account()
    free_capital = account.equity_usd - account.frozen_reserve_usd
    requested = (
        req.target_yield_layer_usd
        + req.target_reserve_layer_usd
        + req.target_hedge_layer_usd
    )

    notes: List[str] = []
    shortfall = max(0.0, requested - free_capital)

    if shortfall <= 0:
        notes.append("Reallocation fully funded from internal free capital.")
        advice = None
        accepted = True
    else:
        advice = (
            f"Internal cash pool fully utilized. Manually deposit "
            f"${shortfall:,.0f} to {req.asset} to fund the requested allocation. "
            f"(Automated deposits are disabled by design — no bank rails.)"
        )
        notes.append("Reserve floors protected: refused to auto-fund the shortfall.")
        accepted = False

    return ReallocateResponse(
        asset=req.asset,
        accepted=accepted,
        available_free_capital_usd=round(free_capital, 2),
        shortfall_usd=round(shortfall, 2),
        deposit_advice=advice,
        notes=notes,
    )
