"""
pre_trade_check.py
==================
HARDCODED ISOLATION FIREWALL.

This module is deliberately *dumb, independent, and AI-free*. It is the last
line of defence and must keep working even if every model, feed, or LLM upstream
is wrong or compromised. Design rules enforced here:

    1. Limits are HARDCODED constants in this file, not pulled from config,
       a database, or any network source. Tampering requires a code change +
       redeploy, which is auditable.
    2. The gate is FAIL-CLOSED: any exception, missing field, or ambiguity
       results in REJECTION, never approval.
    3. No imports from models/, execution/, or any AI module. Zero side effects.
    4. A breached daily-drawdown threshold trips a system-wide KILL SWITCH that
       blocks ALL further trades until a human resets it.

Nothing in this file talks to a broker. It only returns an allow/deny verdict.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List


# ===========================================================================
# HARDCODED RISK LIMITS  --  change only via reviewed code edit + redeploy.
# ===========================================================================
MAX_SINGLE_TRADE_NOTIONAL_USD: float = 25_000.0     # cap on any one ticket
MAX_TOTAL_GROSS_LEVERAGE: float = 3.0               # gross notional / equity
MAX_PORTFOLIO_NOTIONAL_USD: float = 250_000.0       # total open exposure cap
DAILY_DRAWDOWN_KILL_PCT: float = 0.05               # 5% day loss => kill switch
MIN_FREE_RESERVE_RATIO: float = 0.20                # keep >=20% equity unfrozen
# ===========================================================================


class Verdict(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class TradeIntent:
    """Immutable description of a single proposed ticket."""
    symbol: str
    side: str                  # "BUY" | "SELL"
    notional_usd: float        # absolute notional of THIS ticket


@dataclass(frozen=True)
class AccountState:
    """Snapshot of the account at the moment of the check."""
    equity_usd: float                  # current total equity (mark-to-market)
    open_gross_notional_usd: float     # sum of |notional| of open positions
    frozen_reserve_usd: float          # cash already locked as loss reserves
    start_of_day_equity_usd: float     # equity at session open (for drawdown)


@dataclass
class RiskDecision:
    verdict: Verdict
    reasons: List[str] = field(default_factory=list)
    kill_switch_engaged: bool = False

    @property
    def approved(self) -> bool:
        return self.verdict is Verdict.APPROVED


# Module-level latch. Once tripped it stays tripped until reset_kill_switch()
# is called by an explicit human/operator action.
_KILL_SWITCH_ENGAGED: bool = False


def kill_switch_status() -> bool:
    return _KILL_SWITCH_ENGAGED


def engage_kill_switch() -> None:
    global _KILL_SWITCH_ENGAGED
    _KILL_SWITCH_ENGAGED = True


def reset_kill_switch() -> None:
    """Operator-only. Call manually after reviewing why the switch tripped."""
    global _KILL_SWITCH_ENGAGED
    _KILL_SWITCH_ENGAGED = False


def _daily_drawdown(account: AccountState) -> float:
    """Fractional loss vs start-of-day equity. Positive number == a loss."""
    if account.start_of_day_equity_usd <= 0:
        return 1.0  # unknown baseline -> treat as fully drawn down (fail closed)
    dd = (account.start_of_day_equity_usd - account.equity_usd) / account.start_of_day_equity_usd
    return max(dd, 0.0)


def check_trade(intent: TradeIntent, account: AccountState) -> RiskDecision:
    """
    Run every hardcoded guard. Returns APPROVED only if ALL pass.
    Any error path returns REJECTED (fail-closed).
    """
    try:
        reasons: List[str] = []

        # --- 0. Global kill switch (checked first, before anything else) ----
        # Re-evaluate the drawdown each call so a fresh breach trips the latch.
        dd = _daily_drawdown(account)
        if dd >= DAILY_DRAWDOWN_KILL_PCT:
            engage_kill_switch()
        if kill_switch_status():
            return RiskDecision(
                verdict=Verdict.REJECTED,
                reasons=[
                    f"KILL SWITCH ENGAGED: daily drawdown {dd:.2%} "
                    f">= {DAILY_DRAWDOWN_KILL_PCT:.2%}. Human reset required."
                ],
                kill_switch_engaged=True,
            )

        # --- 1. Sanity / input validation (fail closed) --------------------
        if intent.side not in ("BUY", "SELL"):
            reasons.append(f"Invalid side '{intent.side}'.")
        if not (intent.notional_usd > 0):
            reasons.append("Trade notional must be a positive number.")
        if account.equity_usd <= 0:
            reasons.append("Non-positive account equity.")
        if reasons:
            return RiskDecision(Verdict.REJECTED, reasons)

        # --- 2. Single-trade notional cap ----------------------------------
        if intent.notional_usd > MAX_SINGLE_TRADE_NOTIONAL_USD:
            reasons.append(
                f"Single-trade notional ${intent.notional_usd:,.0f} exceeds "
                f"cap ${MAX_SINGLE_TRADE_NOTIONAL_USD:,.0f}."
            )

        # --- 3. Portfolio notional cap -------------------------------------
        projected_gross = account.open_gross_notional_usd + intent.notional_usd
        if projected_gross > MAX_PORTFOLIO_NOTIONAL_USD:
            reasons.append(
                f"Projected gross notional ${projected_gross:,.0f} exceeds "
                f"portfolio cap ${MAX_PORTFOLIO_NOTIONAL_USD:,.0f}."
            )

        # --- 4. Gross leverage cap -----------------------------------------
        projected_leverage = projected_gross / account.equity_usd
        if projected_leverage > MAX_TOTAL_GROSS_LEVERAGE:
            reasons.append(
                f"Projected gross leverage {projected_leverage:.2f}x exceeds "
                f"cap {MAX_TOTAL_GROSS_LEVERAGE:.2f}x."
            )

        # --- 5. Free-reserve floor -----------------------------------------
        # After freezing reserves we must keep a minimum unencumbered buffer.
        free_after = account.equity_usd - account.frozen_reserve_usd
        min_free = account.equity_usd * MIN_FREE_RESERVE_RATIO
        if free_after < min_free:
            reasons.append(
                f"Free reserve ${free_after:,.0f} below floor ${min_free:,.0f} "
                f"({MIN_FREE_RESERVE_RATIO:.0%} of equity)."
            )

        if reasons:
            return RiskDecision(Verdict.REJECTED, reasons)
        return RiskDecision(Verdict.APPROVED, ["All hardcoded risk checks passed."])

    except Exception as exc:  # noqa: BLE001 - intentional catch-all, fail closed
        return RiskDecision(
            verdict=Verdict.REJECTED,
            reasons=[f"FAIL-CLOSED: exception during risk check ({exc!r})."],
        )
