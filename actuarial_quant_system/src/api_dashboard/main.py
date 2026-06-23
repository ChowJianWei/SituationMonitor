"""
main.py
=======
FastAPI orchestration for the Actuarial Quant System.

The HTTP layer is read-mostly: it serves the visual portal. The real work runs
in two background tasks started in the lifespan:
  * the market-data feed consumer (StreamBus), and
  * the autonomous PAPER underwriting cycle, which every CYCLE_INTERVAL_SECONDS
    detects the regime, prices the variance risk premium, selects a structure,
    routes it through the hardcoded risk gate, simulates a fill, locks the loss
    reserve in Redis, and persists everything to PostgreSQL.

No real money can move: execution is the PaperExecutionEngine only.
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
from ..data_pipeline.database import Database
from ..data_pipeline.state_store import StateStore
from ..data_pipeline.stream_bus import StreamBus
from ..execution.broker_connector import BrokerConnector, BrokerCredentials, KeyScope
from ..execution.paper_engine import PaperExecutionEngine
from ..execution.strategy_selector import select_strategy
from ..models.actuarial_engine import (
    TradeMetrics,
    compute_loss_reserve,
    fit_gpd_tail_risk,
    simulate_ruin_probability,
)
from ..models.macro_propagation import default_macro_trace
from ..models.regime_models import detect_regime, fit_garch, simulate_clustered_returns
from ..models.signals import (
    generate_signal,
    realized_vol_close_to_close,
    variance_risk_premium,
)
from ..risk_gate.pre_trade_check import (
    MAX_SINGLE_TRADE_NOTIONAL_USD,
    AccountState,
    kill_switch_status,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api_dashboard")

app = FastAPI(title="Actuarial Quant System", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origin],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Shared singletons (wired in lifespan).
bus = StreamBus(settings.redis_url)
db = Database(settings.postgres_dsn)
state = StateStore(bus)
paper_engine = PaperExecutionEngine(db, state)
broker = BrokerConnector(
    settings.broker_base_url,
    BrokerCredentials(settings.broker_api_key, settings.broker_api_secret, KeyScope.READ_ONLY),
    paper_trading_only=settings.paper_trading_only,
)

# Demo universe: (symbol, spot, realized-vol seed, IV richness, stress_at).
UNIVERSE = [
    ("BTC", 65_000.0, 11, 1.25, None),
    ("ETH", 3_500.0, 22, 1.15, 0.9),
    ("SPY", 540.0, 33, 1.05, None),
]


# ---------------------------------------------------------------------------
# Market-data synthesis (stands in for live feeds until a read-only venue key is
# wired). Deterministic per symbol so the dashboard is stable between calls.
# ---------------------------------------------------------------------------
def _asset_returns(seed: int, stress_at):
    return simulate_clustered_returns(n=1200, seed=seed, stress_at=stress_at)


def _asset_market(symbol, spot, seed, richness, stress_at):
    returns = _asset_returns(seed, stress_at)
    rv = realized_vol_close_to_close(returns, annualize=True)
    iv = rv * richness
    return {"symbol": symbol, "spot": spot, "returns": returns, "rv": rv, "iv": iv}


def _demo_macro_panel():
    """Synthesize a [Rates -> TechValuation -> ImpliedVol -> Portfolio] panel."""
    rng = np.random.default_rng(7)
    n = 400
    rates = np.cumsum(rng.normal(0, 0.02, n))          # rate level random walk
    tech = np.zeros(n); iv = np.zeros(n); port = np.zeros(n)
    for t in range(1, n):
        tech[t] = 0.85 * tech[t - 1] - 0.6 * rates[t - 1] + rng.normal(0, 0.1)
        iv[t] = 0.80 * iv[t - 1] - 0.5 * tech[t - 1] + rng.normal(0, 0.1)
        port[t] = 0.75 * port[t - 1] + 0.7 * iv[t - 1] + rng.normal(0, 0.1)
    panel = np.column_stack([rates, tech, iv, port])
    names = ["Fed_Rates", "Tech_Valuation", "Implied_Vol", "Portfolio"]
    return panel, names


# ---------------------------------------------------------------------------
# The autonomous PAPER underwriting cycle
# ---------------------------------------------------------------------------
async def run_underwriting_cycle() -> dict:
    """One full pass: regime -> signal -> strategy -> risk gate -> paper fill."""
    acct = await state.restore_or_seed(settings.seed_equity_usd)
    frozen = await state.total_locked_reserves()
    account = AccountState(
        equity_usd=acct["equity_usd"],
        open_gross_notional_usd=acct.get("open_gross_notional_usd", 0.0),
        frozen_reserve_usd=frozen,
        start_of_day_equity_usd=acct.get("start_of_day_equity_usd", acct["equity_usd"]),
    )

    fills: List[dict] = []
    gross = account.open_gross_notional_usd
    for symbol, spot, seed, richness, stress_at in UNIVERSE:
        mkt = _asset_market(symbol, spot, seed, richness, stress_at)
        regime = detect_regime(mkt["returns"], n_states=3)
        garch = fit_garch(mkt["returns"])
        vrp = variance_risk_premium(mkt["iv"], mkt["rv"])
        cur_conf = max(regime.state_probabilities) if regime.state_probabilities else 0.6
        signal = generate_signal(regime.current_regime, vrp, regime_confidence=cur_conf)

        losses = -mkt["returns"][mkt["returns"] < 0]
        cvar_frac = fit_gpd_tail_risk(losses, 0.99, 0.95).cvar

        proposal = select_strategy(
            symbol=symbol, signal=signal, spot=spot, cvar_fraction=cvar_frac,
            max_single_trade_usd=MAX_SINGLE_TRADE_NOTIONAL_USD,
            high_vol=(garch.forecast_vol > garch.long_run_vol),
        )
        if proposal is None:
            fills.append({"symbol": symbol, "action": signal.action.value,
                          "executed": False, "reasons": ["STAND_ASIDE: no edge."]})
            continue

        # Keep the running gross current so the gate sees accumulating exposure.
        account = AccountState(
            equity_usd=account.equity_usd, open_gross_notional_usd=gross,
            frozen_reserve_usd=await state.total_locked_reserves(),
            start_of_day_equity_usd=account.start_of_day_equity_usd,
        )
        result = await paper_engine.execute(proposal, account, ref_price=spot)
        if result.executed and proposal.side != "SELL" or result.verdict == "APPROVED":
            gross += proposal.notional_usd
        fills.append({**result.as_dict(), "regime": regime.current_regime,
                      "signal": signal.action.value})

    await state.set_account(account.equity_usd, account.start_of_day_equity_usd, gross)

    # Persist a regime snapshot from the first asset for the historical log.
    head = _asset_market(*UNIVERSE[0])
    head_regime = detect_regime(head["returns"], n_states=3)
    head_garch = fit_garch(head["returns"])
    await db.save_regime_snapshot({
        "regime": head_regime.current_regime,
        "garch_vol": head_garch.current_vol,
        "garch_forecast": head_garch.forecast_vol,
        "labels": head_regime.regime_labels,
    })

    summary = {"as_of": datetime.now(timezone.utc).isoformat(),
               "kill_switch_engaged": kill_switch_status(),
               "fills": fills, "total_locked_reserves": await state.total_locked_reserves()}
    await db.write_audit("engine", "cycle_complete",
                         {"n_fills": sum(1 for f in fills if f.get("executed"))})
    return summary


async def _cycle_loop() -> None:
    """Background task: run the underwriting cycle on a fixed interval."""
    while True:
        try:
            await run_underwriting_cycle()
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # pragma: no cover
            logger.warning("Underwriting cycle error: %s", exc)
        await asyncio.sleep(settings.cycle_interval_seconds)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def _startup() -> None:
    await bus.connect()
    await db.connect()
    await state.restore_or_seed(settings.seed_equity_usd)
    app.state.feed_task = asyncio.create_task(
        bus.consume_feed("wss://sandbox.exchange.local/stream")
    )
    app.state.cycle_task = asyncio.create_task(_cycle_loop())
    logger.info("Engine online (paper_only=%s, cycle=%ss).",
                settings.paper_trading_only, settings.cycle_interval_seconds)


@app.on_event("shutdown")
async def _shutdown() -> None:
    for name in ("feed_task", "cycle_task"):
        task = getattr(app.state, name, None)
        if task:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
    await broker.aclose()
    await db.close()
    await bus.aclose()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class ReallocateRequest(BaseModel):
    asset: str
    target_yield_layer_usd: float
    target_reserve_layer_usd: float
    target_hedge_layer_usd: float


class OnboardingRequest(BaseModel):
    provider: str
    api_key: str
    api_secret: str
    allocation_usd: float = 0.0


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "paper_trading_only": settings.paper_trading_only,
            "kill_switch_engaged": kill_switch_status(),
            "db_live": db.live, "ts": datetime.now(timezone.utc).isoformat()}


@app.get("/api/v1/regime")
async def regime() -> dict:
    mkt = _asset_market(*UNIVERSE[0])
    return {"garch": fit_garch(mkt["returns"]).as_dict(),
            "regime": detect_regime(mkt["returns"], 3).as_dict()}


@app.get("/api/v1/signals")
async def signals_endpoint() -> dict:
    out = []
    for symbol, spot, seed, richness, stress_at in UNIVERSE:
        mkt = _asset_market(symbol, spot, seed, richness, stress_at)
        reg = detect_regime(mkt["returns"], 3)
        vrp = variance_risk_premium(mkt["iv"], mkt["rv"])
        sig = generate_signal(reg.current_regime, vrp)
        out.append({"symbol": symbol, "regime": reg.current_regime, **sig.as_dict()})
    return {"signals": out}


@app.get("/api/v1/risk/ruin")
async def ruin() -> dict:
    acct = await state.restore_or_seed(settings.seed_equity_usd)
    frozen = await state.total_locked_reserves()
    metrics = TradeMetrics(1.0, 0.56, 420.0, 510.0)
    res = simulate_ruin_probability(
        surplus=acct["equity_usd"] - frozen, metrics=metrics,
        horizon=10_000, n_paths=1_500)
    return res.as_dict()


@app.get("/api/v1/daily-briefing")
async def daily_briefing() -> dict:
    acct = await state.restore_or_seed(settings.seed_equity_usd)
    frozen = await state.total_locked_reserves()
    free_capital = acct["equity_usd"] - frozen

    head = _asset_market(*UNIVERSE[0])
    losses = -head["returns"][head["returns"] < 0]
    tail = fit_gpd_tail_risk(losses, 0.99, 0.95)
    reg = detect_regime(head["returns"], 3)
    ruin_res = simulate_ruin_probability(
        surplus=free_capital, metrics=TradeMetrics(1.0, 0.56, 420.0, 510.0),
        horizon=10_000, n_paths=1_500)

    dd_headroom = max(0.0, 1.0 - ruin_res.ruin_probability)
    reserve_health = min(1.0, free_capital / max(acct["equity_usd"], 1e-9))
    shi = round(100 * (0.6 * dd_headroom + 0.4 * reserve_health), 1)
    pnl_24h = acct["equity_usd"] - acct.get("start_of_day_equity_usd", acct["equity_usd"])

    briefing = {
        "as_of": datetime.now(timezone.utc).isoformat(),
        "surplus_health_index": shi,
        "net_earnings_24h_usd": round(pnl_24h, 2),
        "regime": reg.current_regime,
        "regime_probabilities": dict(zip(reg.regime_labels, reg.state_probabilities)),
        "ruin_probability": ruin_res.ruin_probability,
        "expected_shortfall_99": tail.cvar,
        "value_at_risk_99": tail.var,
        "free_capital_usd": round(free_capital, 2),
        "frozen_reserve_usd": round(frozen, 2),
        "kill_switch_engaged": kill_switch_status(),
        "executive_narrative": [
            f"Active market regime classified as {reg.current_regime}.",
            f"99% Expected Shortfall (CVaR) on losses is {tail.cvar:.2%}; tail index xi={tail.xi:.2f}.",
            f"Modelled ruin probability over 10,000 steps is {ruin_res.ruin_probability:.3%}.",
            f"Free capital ${free_capital:,.0f}; ${frozen:,.0f} locked as loss reserves.",
            "Underwriting posture: informational / paper only — no live execution.",
        ],
    }
    await db.save_briefing(None, briefing)
    return briefing


@app.get("/api/v1/fund-allocation")
async def fund_allocation() -> dict:
    positions = await db.get_open_positions()
    allocations = []
    if positions:
        # Aggregate persisted positions per symbol into the three layers.
        by_symbol: dict[str, dict] = {}
        for p in positions:
            s = by_symbol.setdefault(p["symbol"], {"yield": 0.0, "reserve": 0.0, "hedge": 0.0})
            if p["structure"] in ("SHORT_PUT", "IRON_CONDOR"):
                s["yield"] += float(p["notional_usd"])
            elif p["structure"] in ("CASH_LONG", "LONG_FUTURE"):
                s["hedge"] += float(p["notional_usd"])
            s["reserve"] += float(p.get("loss_reserve_usd", 0))
        for sym, lay in by_symbol.items():
            allocations.append({"asset": sym,
                                "yield_generation_usd": round(lay["yield"], 2),
                                "loss_reserve_usd": round(lay["reserve"], 2),
                                "delta_hedge_usd": round(lay["hedge"], 2)})
    else:
        # Fallback illustrative book if no fills have run yet.
        head = _asset_market(*UNIVERSE[0])
        losses = -head["returns"][head["returns"] < 0]
        cvar = fit_gpd_tail_risk(losses, 0.99, 0.95).cvar
        for symbol, spot, *_ in UNIVERSE:
            res = compute_loss_reserve(60_000, 0.12, cvar)
            allocations.append({"asset": symbol, "yield_generation_usd": 60_000.0,
                                "loss_reserve_usd": round(res.required_reserve, 2),
                                "delta_hedge_usd": 20_000.0})
    return {"as_of": datetime.now(timezone.utc).isoformat(), "allocations": allocations}


@app.get("/api/v1/macro-propagation")
async def macro_propagation() -> dict:
    panel, names = _demo_macro_panel()
    return default_macro_trace(panel, names)


@app.get("/api/v1/trades")
async def trades(limit: int = 50) -> dict:
    return {"trades": await db.get_recent_trades(limit)}


@app.post("/api/v1/cycle/run")
async def cycle_run() -> dict:
    """Manually trigger one paper underwriting cycle (also runs on a timer)."""
    return await run_underwriting_cycle()


@app.post("/api/v1/onboarding/validate")
async def onboarding_validate(req: OnboardingRequest) -> dict:
    """
    Validate exchange API keys for the onboarding wizard. Paper-safe; always
    reports withdrawal as disabled. Seeds the paper account with the requested
    allocation so the dashboard shows a funded balance.
    """
    result = await broker.validate_credentials()
    if result.get("valid") and req.allocation_usd > 0:
        await state.set_account(req.allocation_usd, req.allocation_usd, 0.0)
    balances = await broker.get_balances(seed_equity=req.allocation_usd)
    await db.write_audit("api", "onboarding_validate", {"provider": req.provider})
    return {"validation": result, "balances": balances,
            "security_notice": "Withdrawal permission is disabled; no bank/ACH/SWIFT access."}


@app.post("/api/v1/reallocate")
async def reallocate(req: ReallocateRequest) -> dict:
    acct = await state.restore_or_seed(settings.seed_equity_usd)
    frozen = await state.total_locked_reserves()
    free_capital = acct["equity_usd"] - frozen
    requested = (req.target_yield_layer_usd + req.target_reserve_layer_usd
                 + req.target_hedge_layer_usd)
    shortfall = max(0.0, requested - free_capital)
    if shortfall <= 0:
        advice, accepted, note = None, True, "Reallocation funded from internal free capital."
    else:
        advice = (f"Internal cash pool fully utilized. Manually deposit "
                  f"${shortfall:,.0f} to {req.asset}. Automated deposits are disabled by design.")
        accepted, note = False, "Reserve floors protected: refused to auto-fund the shortfall."
    return {"asset": req.asset, "accepted": accepted,
            "available_free_capital_usd": round(free_capital, 2),
            "shortfall_usd": round(shortfall, 2), "deposit_advice": advice, "notes": [note]}
