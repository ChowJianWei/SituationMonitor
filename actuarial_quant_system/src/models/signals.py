"""
signals.py
==========
Edge-detection: realized volatility estimators and the Variance Risk Premium.

The system underwrites when the market PAYS too much for insurance — i.e. when
option-implied volatility is rich relative to how the asset actually moves
(realized volatility). This module quantifies that gap (the Variance Risk
Premium, VRP) and turns it, together with the detected regime, into an
actionable underwriting signal. Pure numpy.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional

import numpy as np

TRADING_DAYS = 252


# ---------------------------------------------------------------------------
# Realized volatility estimators
# ---------------------------------------------------------------------------
def realized_vol_close_to_close(returns: np.ndarray, annualize: bool = True) -> float:
    """Standard close-to-close realized volatility."""
    r = np.asarray(returns, dtype=float)
    r = r[np.isfinite(r)]
    if r.size < 2:
        return float("nan")
    vol = float(np.std(r, ddof=1))
    return vol * np.sqrt(TRADING_DAYS) if annualize else vol


def parkinson_vol(high: np.ndarray, low: np.ndarray, annualize: bool = True) -> float:
    """
    Parkinson high-low range estimator — more efficient than close-to-close
    because it uses intraday range. sigma^2 = 1/(4 ln 2) * mean(ln(H/L)^2).
    """
    high = np.asarray(high, dtype=float)
    low = np.asarray(low, dtype=float)
    mask = np.isfinite(high) & np.isfinite(low) & (low > 0)
    if mask.sum() < 1:
        return float("nan")
    log_hl = np.log(high[mask] / low[mask]) ** 2
    var = log_hl.mean() / (4.0 * np.log(2.0))
    vol = float(np.sqrt(var))
    return vol * np.sqrt(TRADING_DAYS) if annualize else vol


# ---------------------------------------------------------------------------
# Variance Risk Premium
# ---------------------------------------------------------------------------
@dataclass
class VRPResult:
    implied_vol: float
    realized_vol: float
    vrp_vol_points: float       # IV - RV (annualized vol points)
    vrp_variance: float         # IV^2 - RV^2 (variance terms)
    richness_ratio: float       # IV / RV
    insurance_is_rich: bool     # True => options overpriced => sell premium

    def as_dict(self) -> dict:
        return asdict(self)


def variance_risk_premium(implied_vol: float, realized_vol: float,
                          rich_threshold: float = 1.10) -> VRPResult:
    """
    VRP = implied variance - realized variance. Positive & large => the market is
    overpaying for protection, the classic short-volatility underwriting edge.
    `rich_threshold` is the IV/RV ratio above which we treat options as rich.
    """
    iv = float(implied_vol)
    rv = float(realized_vol)
    ratio = iv / rv if rv > 0 else float("inf")
    return VRPResult(
        implied_vol=iv,
        realized_vol=rv,
        vrp_vol_points=iv - rv,
        vrp_variance=iv ** 2 - rv ** 2,
        richness_ratio=ratio,
        insurance_is_rich=ratio >= rich_threshold,
    )


# ---------------------------------------------------------------------------
# Signal generation (regime-aware)
# ---------------------------------------------------------------------------
class Action(str, Enum):
    SELL_VOL = "SELL_VOL"          # collect premium (short-vol structures)
    BUY_SPOT = "BUY_SPOT"          # directional long via cash/future
    DEFENSIVE = "DEFENSIVE"        # de-risk, raise reserves
    STAND_ASIDE = "STAND_ASIDE"    # no edge / no trade


@dataclass
class Signal:
    action: Action
    confidence: float              # 0..1
    rationale: str
    vrp: VRPResult

    def as_dict(self) -> dict:
        d = asdict(self)
        d["action"] = self.action.value
        return d


def generate_signal(regime: str, vrp: VRPResult,
                    regime_confidence: float = 0.6) -> Signal:
    """
    Map (regime, VRP) -> an underwriting action.

      TAIL_STRESS              -> DEFENSIVE   (survival first, ignore edge)
      CHOPPY_MEAN_REVERT + rich-> SELL_VOL    (harvest overpriced premium)
      TRENDING + cheap vol     -> BUY_SPOT    (directional, vol not overpriced)
      otherwise                -> STAND_ASIDE
    """
    if regime == "TAIL_STRESS":
        return Signal(Action.DEFENSIVE, max(regime_confidence, 0.8),
                      "Tail-stress regime: prioritize capital survival, raise reserves.", vrp)

    if regime == "CHOPPY_MEAN_REVERT" and vrp.insurance_is_rich:
        conf = min(1.0, regime_confidence * min(vrp.richness_ratio / 1.5, 1.0))
        return Signal(Action.SELL_VOL, conf,
                      f"Choppy/mean-reverting with rich vol (IV/RV={vrp.richness_ratio:.2f}): "
                      "sell premium, delta-hedge.", vrp)

    if regime == "TRENDING" and not vrp.insurance_is_rich:
        return Signal(Action.BUY_SPOT, regime_confidence,
                      "Trending with fairly-priced vol: take directional spot/future exposure.", vrp)

    return Signal(Action.STAND_ASIDE, 0.3,
                  "No statistical edge for current regime/VRP combination.", vrp)
