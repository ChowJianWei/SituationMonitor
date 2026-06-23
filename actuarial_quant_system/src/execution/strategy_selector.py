"""
strategy_selector.py
====================
Translates an underwriting signal into a concrete instrument structure and an
actuarially-bounded size.

Mapping (the blueprint's "Derivative Structure & Strategy Selector"):
    SELL_VOL   -> SHORT_PUT or IRON_CONDOR  (collect premium, delta-hedged)
    BUY_SPOT   -> CASH_LONG / LONG_FUTURE   (directional, cheap vol)
    DEFENSIVE  -> RAISE_CASH                 (close risk, hold reserves)
    STAND_ASIDE-> no proposal

Size is capped by the Cramér-Lundberg "maximum allowable underwriting capital":
the largest notional whose loss reserve still leaves the book's ruin probability
under target. We approximate that by scaling the single-trade limit by the
signal confidence and the EVT tail, then attaching the dynamic loss reserve.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional

from ..models.actuarial_engine import compute_loss_reserve
from ..models.signals import Action, Signal


class Structure(str, Enum):
    CASH_LONG = "CASH_LONG"
    LONG_FUTURE = "LONG_FUTURE"
    SHORT_PUT = "SHORT_PUT"
    IRON_CONDOR = "IRON_CONDOR"
    RAISE_CASH = "RAISE_CASH"


@dataclass
class StrategyProposal:
    symbol: str
    structure: Structure
    side: str                      # BUY | SELL
    notional_usd: float
    est_delta: float
    est_vega: float
    loss_reserve_usd: float
    rationale: str

    def as_dict(self) -> dict:
        d = asdict(self)
        d["structure"] = self.structure.value
        return d


def select_strategy(
    symbol: str,
    signal: Signal,
    spot: float,
    cvar_fraction: float,
    max_single_trade_usd: float,
    margin_rate: float = 0.12,
    high_vol: bool = True,
) -> Optional[StrategyProposal]:
    """
    Build a proposal from a signal. Returns None for STAND_ASIDE.

    `high_vol` (from GARCH/HMM) chooses between a single short-put and a fully
    delta-neutral iron condor when selling vol.
    """
    if signal.action is Action.STAND_ASIDE:
        return None

    # Actuarially-bounded notional: scale the hard single-trade cap by confidence.
    notional = max_single_trade_usd * float(min(max(signal.confidence, 0.0), 1.0))

    if signal.action is Action.DEFENSIVE:
        return StrategyProposal(
            symbol=symbol, structure=Structure.RAISE_CASH, side="SELL",
            notional_usd=round(notional, 2), est_delta=0.0, est_vega=0.0,
            loss_reserve_usd=0.0,
            rationale="Defensive: flatten risk and hold cash reserves.",
        )

    if signal.action is Action.BUY_SPOT:
        reserve = compute_loss_reserve(notional, margin_rate=1.0, cvar_fraction=cvar_fraction)
        # margin_rate=1.0 for cash: fully funded, reserve dominated by tail buffer.
        return StrategyProposal(
            symbol=symbol, structure=Structure.CASH_LONG, side="BUY",
            notional_usd=round(notional, 2), est_delta=1.0, est_vega=0.0,
            loss_reserve_usd=round(reserve.required_reserve, 2),
            rationale="Directional long via spot; reserve sized to EVT tail.",
        )

    # SELL_VOL
    structure = Structure.IRON_CONDOR if high_vol else Structure.SHORT_PUT
    # Iron condor is delta-neutral by construction; short put carries +delta.
    est_delta = 0.0 if structure is Structure.IRON_CONDOR else 0.30
    reserve = compute_loss_reserve(notional, margin_rate=margin_rate, cvar_fraction=cvar_fraction)
    return StrategyProposal(
        symbol=symbol, structure=structure, side="SELL",
        notional_usd=round(notional, 2), est_delta=est_delta, est_vega=-0.50,
        loss_reserve_usd=round(reserve.required_reserve, 2),
        rationale=(f"Harvest rich vol via {structure.value}; "
                   f"freeze ${reserve.required_reserve:,.0f} as loss reserve."),
    )
