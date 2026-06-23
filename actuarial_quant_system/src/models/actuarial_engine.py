"""
actuarial_engine.py
===================
Pure actuarial mathematics for capital-survival underwriting.

Every trade is treated as an *insurance liability*: we collect a "premium"
(expected edge) and are exposed to "claims" (losses). The job of this module is
to answer three questions an actuary would ask before underwriting a book:

    1. What is the probability of RUIN over the planning horizon?      (Cramer-Lundberg)
    2. How bad is the tail when a crash actually happens?              (EVT / GPD -> CVaR)
    3. How much cash must be FROZEN to back an active liability?       (Loss Reserve)

All math is numpy / scipy. No external trading or AI calls live here.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Optional

import numpy as np
from scipy import optimize
from scipy.stats import genpareto


# ---------------------------------------------------------------------------
# 1. CRAMER-LUNDBERG RUIN THEORY
# ---------------------------------------------------------------------------
#
# Surplus process (discrete approximation of the classical model):
#
#     U(t) = u + c * t - S(t),     S(t) = sum of claims up to t
#
# where claims arrive as a compound Poisson process. In trading terms:
#     u  = current surplus (free wallet balance)
#     c  = premium income per step  = trade_freq * win_rate * avg_win
#     claims  = losing trades, frequency lambda = trade_freq * (1 - win_rate),
#               severity ~ Exponential(mean = avg_loss)
#
# Ruin = the surplus path ever drops below zero.
# ---------------------------------------------------------------------------


@dataclass
class TradeMetrics:
    """Behavioural fingerprint of the strategy book, in per-step units."""
    trades_per_step: float      # expected number of trades per simulation step
    win_rate: float             # P(trade is a winner), in [0, 1]
    avg_win: float              # mean PnL of a winning trade (currency units)
    avg_loss: float             # mean magnitude of a losing trade (positive number)

    @property
    def loss_intensity(self) -> float:
        """Poisson arrival rate of LOSS events per step (lambda)."""
        return self.trades_per_step * (1.0 - self.win_rate)

    @property
    def premium_per_step(self) -> float:
        """Deterministic premium inflow per step (c) from winning trades."""
        return self.trades_per_step * self.win_rate * self.avg_win

    @property
    def net_drift(self) -> float:
        """Expected change in surplus per step. Negative => uninsurable book."""
        return self.premium_per_step - self.loss_intensity * self.avg_loss


@dataclass
class RuinResult:
    ruin_probability: float
    mean_time_to_ruin: Optional[float]      # in steps, over ruined paths only
    adjustment_coefficient: Optional[float]  # Lundberg R
    lundberg_upper_bound: Optional[float]    # analytic exp(-R*u) bound
    net_drift_per_step: float
    horizon: int
    n_paths: int

    def as_dict(self) -> dict:
        return asdict(self)


def lundberg_adjustment_coefficient(metrics: TradeMetrics) -> Optional[float]:
    """
    Solve the Lundberg equation for the adjustment coefficient R > 0:

        lambda * (M_X(r) - 1) - c * r = 0

    with exponential claim severities M_X(r) = beta / (beta - r), beta = 1/avg_loss.
    A larger R means a thinner ruin tail. Returns None if no positive R exists
    (i.e. the book has non-positive safety loading and ruin is asymptotically certain).
    """
    lam = metrics.loss_intensity
    c = metrics.premium_per_step
    if lam <= 0 or c <= 0 or metrics.avg_loss <= 0:
        return None
    beta = 1.0 / metrics.avg_loss

    # Net profit condition: premium must exceed expected claims, else no R > 0.
    if c <= lam / beta:
        return None

    def lundberg(r: float) -> float:
        # Valid only for r in (0, beta); M_X explodes at r = beta.
        return lam * (beta / (beta - r) - 1.0) - c * r

    lo, hi = 1e-9, beta * 0.999999
    # lundberg(0+) -> 0, derivative negative then positive: root sits in (0, beta).
    if lundberg(hi) <= 0:
        return None
    try:
        return float(optimize.brentq(lundberg, lo, hi, maxiter=200))
    except (ValueError, RuntimeError):
        return None


def simulate_ruin_probability(
    surplus: float,
    metrics: TradeMetrics,
    horizon: int = 10_000,
    n_paths: int = 2_000,
    seed: int = 12345,
) -> RuinResult:
    """
    Monte-Carlo estimate of ruin probability over `horizon` steps.

    The horizon defaults to the requested 10,000-step planning window. Each path
    accrues deterministic premium and is hit by Poisson(lambda) loss events per
    step, each loss Exponential(mean=avg_loss). The path is ruined the first time
    surplus < 0.
    """
    if surplus <= 0:
        return RuinResult(1.0, 0.0, None, None, metrics.net_drift, horizon, n_paths)

    rng = np.random.default_rng(seed)
    lam = metrics.loss_intensity
    c = metrics.premium_per_step

    surplus_paths = np.full(n_paths, float(surplus))
    ruined = np.zeros(n_paths, dtype=bool)
    time_to_ruin = np.full(n_paths, np.nan)

    for step in range(1, horizon + 1):
        alive = ~ruined
        if not alive.any():
            break

        # Number of loss events this step for each still-alive path.
        n_losses = rng.poisson(lam, size=n_paths)
        # Aggregate loss severity per path (sum of exponentials == Gamma).
        agg_loss = np.zeros(n_paths)
        active = alive & (n_losses > 0)
        if active.any():
            # Gamma(shape=n_losses, scale=avg_loss) is the sum of n exponentials.
            agg_loss[active] = rng.gamma(
                shape=n_losses[active], scale=metrics.avg_loss
            )

        surplus_paths[alive] += c - agg_loss[alive]

        newly_ruined = alive & (surplus_paths < 0.0)
        time_to_ruin[newly_ruined] = step
        ruined |= newly_ruined

    prob = float(ruined.mean())
    mean_ttr = float(np.nanmean(time_to_ruin)) if ruined.any() else None

    R = lundberg_adjustment_coefficient(metrics)
    bound = float(np.exp(-R * surplus)) if R is not None else None

    return RuinResult(
        ruin_probability=prob,
        mean_time_to_ruin=mean_ttr,
        adjustment_coefficient=R,
        lundberg_upper_bound=bound,
        net_drift_per_step=metrics.net_drift,
        horizon=horizon,
        n_paths=n_paths,
    )


# ---------------------------------------------------------------------------
# 2. EXTREME VALUE THEORY  ->  CVaR / Expected Shortfall
# ---------------------------------------------------------------------------
#
# Peaks-Over-Threshold (POT). We fit a Generalized Pareto Distribution to the
# losses that exceed a high threshold u, then read VaR and CVaR (Expected
# Shortfall) off the closed-form GPD tail (McNeil, Frey & Embrechts).
# ---------------------------------------------------------------------------


@dataclass
class TailRiskResult:
    threshold: float
    xi: float                 # GPD shape (tail index); xi >= 0 => heavy tail
    beta: float               # GPD scale
    n_exceedances: int
    var: float                # Value at Risk at `confidence`
    cvar: float               # Conditional VaR / Expected Shortfall
    confidence: float
    finite_mean_tail: bool    # False if xi >= 1 (ES undefined / infinite)

    def as_dict(self) -> dict:
        return asdict(self)


def fit_gpd_tail_risk(
    losses: np.ndarray,
    confidence: float = 0.99,
    threshold_quantile: float = 0.95,
) -> TailRiskResult:
    """
    Fit a GPD to the upper tail of the LOSS distribution and compute VaR/CVaR.

    `losses` must be a 1-D array of *positive-is-bad* loss magnitudes (e.g.
    -1 * negative PnL returns). Returns Expected Shortfall, the institutional
    measure of crash tail risk.
    """
    losses = np.asarray(losses, dtype=float)
    losses = losses[np.isfinite(losses)]
    n = losses.size
    if n < 30:
        raise ValueError("Need >= 30 loss observations for a stable GPD fit.")

    u = float(np.quantile(losses, threshold_quantile))
    excesses = losses[losses > u] - u
    nu = excesses.size
    if nu < 10:
        raise ValueError("Too few exceedances above threshold; lower the quantile.")

    # MLE fit of the GPD to the excesses, location fixed at 0 (POT convention).
    xi, _loc, beta = genpareto.fit(excesses, floc=0.0)

    # Closed-form tail risk (McNeil et al.). p = confidence.
    p = confidence
    ratio = (n / nu) * (1.0 - p)
    if abs(xi) < 1e-6:
        # Exponential-tail limit (xi -> 0).
        var = u + beta * (-np.log(ratio))
        cvar = var + beta
    else:
        var = u + (beta / xi) * (ratio ** (-xi) - 1.0)
        # ES finite only for xi < 1.
        cvar = (var + beta - xi * u) / (1.0 - xi) if xi < 1.0 else float("inf")

    return TailRiskResult(
        threshold=u,
        xi=float(xi),
        beta=float(beta),
        n_exceedances=int(nu),
        var=float(var),
        cvar=float(cvar),
        confidence=float(confidence),
        finite_mean_tail=bool(xi < 1.0),
    )


# ---------------------------------------------------------------------------
# 3. DYNAMIC LOSS RESERVE
# ---------------------------------------------------------------------------
#
# When a derivative contract is live it is an open liability. Like an insurer
# posting reserves against unpaid claims, we FREEZE cash so the book can absorb
# an adverse tail move without forced liquidation. The reserve is the max of:
#     * the exchange initial margin requirement, and
#     * a tail buffer sized off the EVT Expected Shortfall,
# plus an IBNR-style prudence load for model risk.
# ---------------------------------------------------------------------------


@dataclass
class LossReserve:
    notional: float
    initial_margin: float
    tail_buffer: float
    prudence_load: float
    required_reserve: float       # cash to FREEZE for this position
    reserve_ratio: float          # required_reserve / notional

    def as_dict(self) -> dict:
        return asdict(self)


def compute_loss_reserve(
    notional: float,
    margin_rate: float,
    cvar_fraction: float,
    prudence_load_pct: float = 0.15,
) -> LossReserve:
    """
    Determine the cash to lock against one active derivative liability.

    Parameters
    ----------
    notional         : position notional in currency units.
    margin_rate      : exchange initial-margin fraction of notional (e.g. 0.10).
    cvar_fraction    : Expected Shortfall expressed as a FRACTION of notional
                       (e.g. CVaR of returns at 99%). This is the actuarial
                       "expected claim" given a tail event.
    prudence_load_pct: extra margin for model risk / IBNR (defaults 15%).
    """
    notional = abs(float(notional))
    initial_margin = notional * max(margin_rate, 0.0)
    tail_buffer = notional * max(cvar_fraction, 0.0)

    base = max(initial_margin, tail_buffer)
    prudence = base * max(prudence_load_pct, 0.0)
    required = base + prudence

    return LossReserve(
        notional=notional,
        initial_margin=initial_margin,
        tail_buffer=tail_buffer,
        prudence_load=prudence,
        required_reserve=required,
        reserve_ratio=(required / notional) if notional > 0 else 0.0,
    )
