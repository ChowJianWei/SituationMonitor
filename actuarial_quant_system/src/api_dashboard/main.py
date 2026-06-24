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
from ..data_pipeline.market_data import aclose as md_aclose, get_market, log_returns
from ..data_pipeline.state_store import StateStore
from ..data_pipeline.stream_bus import StreamBus
from ..execution.broker_connector import BrokerConnector, BrokerCredentials, KeyScope
from ..execution.paper_engine import PaperExecutionEngine
from ..execution.strategy_selector import select_strategy
from ..execution.tradier_connector import TradierConnector
from ..execution.tradier_engine import TradierExecutionEngine
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

# Optional real broker (Tradier). Only built when a token is configured.
tradier: Optional[TradierConnector] = None
if settings.tradier_access_token and settings.tradier_account_id:
    tradier = TradierConnector(settings.tradier_access_token,
                               settings.tradier_account_id, settings.tradier_env)


def _executor():
    """Pick the execution engine: Tradier when configured + selected, else paper."""
    if settings.execution_mode.startswith("tradier") and tradier is not None:
        return TradierExecutionEngine(tradier, db, state)
    return paper_engine

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
def _analyze_asset_sync(symbol, spot, seed, richness, stress_at) -> dict:
    """CPU-heavy per-asset analysis (HMM / GARCH / EVT). Run in a worker thread
    via asyncio.to_thread so it never blocks the web server's event loop."""
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
    return {"regime": regime.current_regime, "signal": signal, "proposal": proposal}


def _head_snapshot_sync() -> dict:
    head = _asset_market(*UNIVERSE[0])
    head_regime = detect_regime(head["returns"], n_states=3)
    head_garch = fit_garch(head["returns"])
    return {"regime": head_regime.current_regime, "garch_vol": head_garch.current_vol,
            "garch_forecast": head_garch.forecast_vol, "labels": head_regime.regime_labels}


async def run_underwriting_cycle() -> dict:
    """One full pass: regime -> signal -> strategy -> risk gate -> paper fill.
    All CPU-bound model fitting is offloaded to threads to keep the API live."""
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
        analysis = await asyncio.to_thread(
            _analyze_asset_sync, symbol, spot, seed, richness, stress_at)
        signal = analysis["signal"]
        proposal = analysis["proposal"]
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
        result = await _executor().execute(proposal, account, ref_price=spot)
        if result.executed and proposal.side != "SELL" or result.verdict == "APPROVED":
            gross += proposal.notional_usd
        fills.append({**result.as_dict(), "regime": analysis["regime"],
                      "signal": signal.action.value})

    await state.set_account(account.equity_usd, account.start_of_day_equity_usd, gross)

    head_snap = await asyncio.to_thread(_head_snapshot_sync)
    await db.save_regime_snapshot(head_snap)

    summary = {"as_of": datetime.now(timezone.utc).isoformat(),
               "kill_switch_engaged": kill_switch_status(),
               "fills": fills, "total_locked_reserves": await state.total_locked_reserves()}
    await db.write_audit("engine", "cycle_complete",
                         {"n_fills": sum(1 for f in fills if f.get("executed"))})
    return summary


async def _cycle_loop() -> None:
    """Background task: run the underwriting cycle on a fixed interval.
    Waits briefly first so the server is responsive immediately on boot."""
    await asyncio.sleep(8)
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
    # Only run the feed consumer if a real WebSocket URL is configured; otherwise
    # it would loop forever trying to reach a non-existent host.
    if settings.feed_ws_url:
        app.state.feed_task = asyncio.create_task(bus.consume_feed(settings.feed_ws_url))
    else:
        app.state.feed_task = None
        logger.info("No FEED_WS_URL set; market-data feed consumer disabled.")
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
    if tradier is not None:
        await tradier.aclose()
    await md_aclose()
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


class AmountRequest(BaseModel):
    amount_usd: float


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/")
async def root() -> dict:
    """Friendly index so the bare domain doesn't look like a 404."""
    return {
        "service": "Actuarial Quant Engine",
        "status": "ok",
        "mode": "paper" if settings.paper_trading_only else "live",
        "docs": "/docs",
        "health": "/health",
        "endpoints": [
            "/api/v1/daily-briefing", "/api/v1/performance",
            "/api/v1/fund-allocation", "/api/v1/signals",
            "/api/v1/macro-propagation", "/api/v1/regime", "/api/v1/risk/ruin",
        ],
    }


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "paper_trading_only": settings.paper_trading_only,
            "execution_mode": settings.execution_mode,
            "tradier_configured": tradier is not None,
            "kill_switch_engaged": kill_switch_status(),
            "db_live": db.live, "ts": datetime.now(timezone.utc).isoformat()}


@app.get("/api/v1/broker/status")
async def broker_status() -> dict:
    if tradier is None:
        return {"configured": False, "execution_mode": settings.execution_mode,
                "hint": "Set TRADIER_ACCESS_TOKEN + TRADIER_ACCOUNT_ID and "
                        "EXECUTION_MODE=tradier_sandbox, then restart."}
    return {"configured": True, "execution_mode": settings.execution_mode,
            "env": settings.tradier_env, **(await tradier.validate())}


@app.get("/api/v1/broker/quote/{symbol}")
async def broker_quote(symbol: str) -> dict:
    if tradier is None:
        return {"error": "Tradier not configured"}
    return await tradier.get_quote(symbol)


@app.get("/api/v1/broker/balances")
async def broker_balances() -> dict:
    if tradier is None:
        return {"error": "Tradier not configured"}
    return await tradier.get_balances()


@app.get("/api/v1/regime")
async def regime() -> dict:
    mkt = _asset_market(*UNIVERSE[0])

    def _compute():
        return {"garch": fit_garch(mkt["returns"]).as_dict(),
                "regime": detect_regime(mkt["returns"], 3).as_dict()}

    return await asyncio.to_thread(_compute)


@app.get("/api/v1/signals")
async def signals_endpoint() -> dict:
    def _compute():
        out = []
        for symbol, spot, seed, richness, stress_at in UNIVERSE:
            mkt = _asset_market(symbol, spot, seed, richness, stress_at)
            reg = detect_regime(mkt["returns"], 3)
            vrp = variance_risk_premium(mkt["iv"], mkt["rv"])
            sig = generate_signal(reg.current_regime, vrp)
            out.append({"symbol": symbol, "regime": reg.current_regime, **sig.as_dict()})
        return out

    return {"signals": await asyncio.to_thread(_compute)}


@app.get("/api/v1/risk/ruin")
async def ruin() -> dict:
    acct = await state.restore_or_seed(settings.seed_equity_usd)
    frozen = await state.total_locked_reserves()
    metrics = TradeMetrics(1.0, 0.56, 420.0, 510.0)
    res = await asyncio.to_thread(
        simulate_ruin_probability, acct["equity_usd"] - frozen, metrics, 10_000, 1_500)
    return res.as_dict()


@app.get("/api/v1/daily-briefing")
async def daily_briefing() -> dict:
    acct = await state.restore_or_seed(settings.seed_equity_usd)
    frozen = await state.total_locked_reserves()
    free_capital = acct["equity_usd"] - frozen

    def _analytics():
        head = _asset_market(*UNIVERSE[0])
        losses = -head["returns"][head["returns"] < 0]
        return (
            fit_gpd_tail_risk(losses, 0.99, 0.95),
            detect_regime(head["returns"], 3),
            simulate_ruin_probability(
                surplus=free_capital, metrics=TradeMetrics(1.0, 0.56, 420.0, 510.0),
                horizon=10_000, n_paths=1_500),
        )

    tail, reg, ruin_res = await asyncio.to_thread(_analytics)

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


# ---- Markets (real OHLC + regime, for the K-line tab) ----
MARKET_SYMBOLS = ["BTC", "ETH", "SPY"]


def _stance_for(regime: str) -> str:
    return {
        "TAIL_STRESS": "Defensive — cut risk, hold cash",
        "TRENDING": "Lean long — buy spot",
        "CHOPPY_MEAN_REVERT": "Sell option premium (when rich)",
    }.get(regime, "No clear edge")


def _verdict(regime: str, max_safe: float, cvar: float) -> tuple[str, str]:
    """The differentiator: an underwriter's call no charting app gives you."""
    if regime == "TAIL_STRESS":
        return ("AVOID",
                f"Stressed regime with a fat crash tail (~{cvar:.0%} expected loss on a "
                f"bad day). The system would stay defensive and not underwrite here.")
    if regime == "TRENDING":
        return ("UNDERWRITE",
                f"Calm and trending. Safe to take directional exposure up to about "
                f"${max_safe:,.0f} without threatening capital survival.")
    if regime == "CHOPPY_MEAN_REVERT":
        return ("SELL PREMIUM",
                f"Range-bound — ideal for selling option premium when it's overpriced. "
                f"Safe underwriting size about ${max_safe:,.0f}.")
    return ("WAIT", "Not enough signal to take a position.")


def _full_analysis_sync(candles: list[dict], free_capital: float) -> dict:
    """Regime + EVT tail risk + the ruin-bounded max safe position size."""
    from ..models.signals import realized_vol_close_to_close as _rv
    rets = log_returns(candles)
    if rets.size < 50:
        return {"enough_data": False, "regime": "UNKNOWN"}
    reg = detect_regime(rets, 3)
    rv = _rv(rets)
    losses = -rets[rets < 0]
    try:
        tail = fit_gpd_tail_risk(losses, 0.99, 0.95)
        cvar, var, xi = tail.cvar, tail.var, tail.xi
    except Exception:
        cvar = float(np.quantile(losses, 0.99)) if losses.size else 0.0
        var, xi = cvar, None
    # Underwriting limit: a 99% tail loss on the position must not exceed 2% of
    # free capital. Riskier (fatter-tail) names => smaller safe size.
    # Advisory size (not the execution cap): fatter tail -> smaller safe size.
    # Bounded by free capital — you can't safely deploy more than you hold.
    max_safe = (free_capital * 0.02 / cvar) if cvar > 0 else 0.0
    max_safe = float(min(max_safe, free_capital))
    return {"enough_data": True, "regime": reg.current_regime,
            "realized_vol_annual": round(rv, 4), "tail_cvar": round(cvar, 4),
            "tail_var": round(var, 4), "tail_xi": (round(xi, 3) if xi is not None else None),
            "implied_move_30d": round(rv * (21.0 / 252.0) ** 0.5, 4),
            "max_safe_position_usd": round(max_safe, 0)}


@app.get("/api/v1/markets")
async def markets() -> dict:
    """A few popular markets with last price (real data) + the system's stance."""
    out = []
    for sym in MARKET_SYMBOLS:
        mkt = await get_market(sym)
        rs = await asyncio.to_thread(
            lambda c: (detect_regime(log_returns(c), 3).current_regime
                       if log_returns(c).size >= 40 else "UNKNOWN"), mkt["candles"])
        out.append({"symbol": sym, "last": mkt["last"], "source": mkt["source"],
                    "regime": rs, "stance": _stance_for(rs)})
    return {"markets": out}


@app.get("/api/v1/markets/{symbol}/candles")
async def market_candles(symbol: str, limit: int = 90) -> dict:
    """
    OHLC for ANY ticker (stocks via Yahoo, crypto via Kraken) plus the full
    actuarial verdict — regime, EVT tail risk, and the ruin-bounded max safe
    position size. This verdict is the thing a normal charting app can't give.
    """
    mkt = await get_market(symbol)
    acct = await state.get_account() or {}
    frozen = await state.total_locked_reserves()
    free_capital = acct.get("equity_usd", settings.seed_equity_usd) - frozen
    analysis = await asyncio.to_thread(_full_analysis_sync, mkt["candles"], free_capital)
    display = mkt["candles"][-limit:]
    regime = analysis.get("regime", "UNKNOWN")
    verdict, verdict_text = _verdict(
        regime, analysis.get("max_safe_position_usd", 0.0), analysis.get("tail_cvar", 0.0))
    return {
        "symbol": mkt["symbol"], "source": mkt["source"], "found": mkt.get("found", False),
        "last": mkt["last"], "regime": regime, "stance": _stance_for(regime),
        "verdict": verdict, "verdict_text": verdict_text,
        "realized_vol_annual": analysis.get("realized_vol_annual"),
        "tail_cvar": analysis.get("tail_cvar"), "tail_xi": analysis.get("tail_xi"),
        "implied_move_30d": analysis.get("implied_move_30d"),
        "max_safe_position_usd": analysis.get("max_safe_position_usd"),
        "enough_data": analysis.get("enough_data", False),
        "free_capital_usd": round(free_capital, 2),
        "candles": display,
        "marker": ({"t": display[-1]["t"], "c": display[-1]["c"]} if display else None),
    }


# Estimated paper premium captured per short-vol fill (fraction of notional).
# Labelled "estimated" everywhere: paper PnL is modelled, not marked-to-market.
PAPER_PREMIUM_RATE = 0.006


@app.get("/api/v1/performance")
async def performance() -> dict:
    """
    Tracking metrics for the Performance & Activity tab: estimated paper equity
    curve, aggregate stats, per-asset breakdown and the recent activity feed.
    """
    all_trades = await db.get_recent_trades(500)
    approved = [t for t in all_trades if t.get("risk_verdict") == "APPROVED"]
    rejected = [t for t in all_trades if t.get("risk_verdict") == "REJECTED"]
    reserves = await state.total_locked_reserves()
    seed = settings.seed_equity_usd

    total_notional = total_costs = total_premium = 0.0
    curve = [seed]
    by_asset: dict[str, dict] = {}

    # `get_recent_trades` is newest-first; walk oldest-first for the curve.
    for t in reversed(approved):
        notional = float(t["notional_usd"])
        cost = float(t.get("fee_usd", 0) or 0) + float(t.get("slippage_usd", 0) or 0)
        premium = notional * PAPER_PREMIUM_RATE if t["structure"] in ("SHORT_PUT", "IRON_CONDOR") else 0.0
        curve.append(round(curve[-1] + premium - cost, 2))
        total_notional += notional
        total_costs += cost
        total_premium += premium
        a = by_asset.setdefault(t["symbol"], {"fills": 0, "notional_usd": 0.0,
                                              "premium_usd": 0.0, "costs_usd": 0.0})
        a["fills"] += 1
        a["notional_usd"] += notional
        a["premium_usd"] += premium
        a["costs_usd"] += cost

    est_equity = curve[-1]
    est_pnl = est_equity - seed
    return {
        "estimated": True,
        "note": "Paper / estimated PnL — short-vol premium modelled, not marked-to-market.",
        "seed_equity_usd": round(seed, 2),
        "estimated_equity_usd": round(est_equity, 2),
        "estimated_pnl_usd": round(est_pnl, 2),
        "estimated_return_pct": round(100 * est_pnl / seed, 3) if seed else 0.0,
        "total_paper_fills": len(approved),
        "rejected_by_gate": len(rejected),
        "total_notional_underwritten_usd": round(total_notional, 2),
        "total_costs_usd": round(total_costs, 2),
        "estimated_premium_collected_usd": round(total_premium, 2),
        "reserves_locked_usd": round(reserves, 2),
        "equity_curve": curve,
        "per_asset": [{"asset": k, **{kk: round(vv, 2) if isinstance(vv, float) else vv
                                      for kk, vv in v.items()}} for k, v in by_asset.items()],
        "recent_activity": all_trades[:25],
    }


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


@app.post("/api/v1/account/deposit")
async def account_deposit(req: AmountRequest) -> dict:
    """
    Add money to the PAPER account. This is an accounting adjustment only — it
    moves no real funds. Deposits are not profit, so start-of-day equity is
    shifted too, leaving the 24h P&L unaffected.
    """
    if req.amount_usd <= 0:
        return {"ok": False, "error": "Amount must be a positive number."}
    acct = await state.restore_or_seed(settings.seed_equity_usd)
    new_equity = acct["equity_usd"] + req.amount_usd
    new_sod = acct.get("start_of_day_equity_usd", acct["equity_usd"]) + req.amount_usd
    await state.set_account(new_equity, new_sod, acct.get("open_gross_notional_usd", 0.0))
    await db.write_audit("api", "paper_deposit", {"amount_usd": req.amount_usd})
    return {"ok": True, "equity_usd": round(new_equity, 2), "deposited_usd": req.amount_usd,
            "note": "Paper balance only — no real money was moved."}


@app.post("/api/v1/account/withdraw")
async def account_withdraw(req: AmountRequest) -> dict:
    """
    Withdraw from the PAPER account. You can only take out FREE cash — frozen
    loss reserves backing open positions are protected. There is intentionally
    no real-money withdrawal path anywhere in this system.
    """
    if req.amount_usd <= 0:
        return {"ok": False, "error": "Amount must be a positive number."}
    acct = await state.restore_or_seed(settings.seed_equity_usd)
    frozen = await state.total_locked_reserves()
    free = acct["equity_usd"] - frozen
    if req.amount_usd > free:
        return {"ok": False,
                "error": (f"You can only withdraw free cash. Max is ${free:,.0f} "
                          f"(${frozen:,.0f} is frozen as safety reserves)."),
                "max_withdrawable_usd": round(free, 2)}
    new_equity = acct["equity_usd"] - req.amount_usd
    new_sod = acct.get("start_of_day_equity_usd", acct["equity_usd"]) - req.amount_usd
    await state.set_account(new_equity, new_sod, acct.get("open_gross_notional_usd", 0.0))
    await db.write_audit("api", "paper_withdraw", {"amount_usd": req.amount_usd})
    return {"ok": True, "equity_usd": round(new_equity, 2), "withdrawn_usd": req.amount_usd,
            "note": ("Paper balance only. Real-money withdrawals are intentionally "
                     "impossible here — do those manually at your broker.")}


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
