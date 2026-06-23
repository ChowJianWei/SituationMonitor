"""
macro_propagation.py
====================
Structural shock-propagation engine for the Global Intelligence tab.

Fits a first-order vector autoregression VAR(1) to a panel of macro/market
series, then traces how a one-off shock to a driver (e.g. central-bank rates)
propagates through intermediate channels (tech valuations, implied vol) into the
portfolio. A credibility score weights the trace by in-sample fit so the UI can
flag low-confidence (fake-pump) signals. Pure numpy (OLS), no statsmodels dep.

Model:  Y_t = c + A · Y_{t-1} + e_t
Shock propagation:  x_{h} = A^h · shock      (deterministic impulse response)
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List, Sequence

import numpy as np


@dataclass
class PropagationLink:
    source: str
    channel: str
    target: str
    impact_pct: float          # peak target response to a unit source shock
    credibility: float         # 0..1, from in-sample fit of the channel

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class MacroModel:
    names: List[str]
    coef: List[List[float]]    # A matrix (k x k)
    intercept: List[float]
    r_squared: List[float]     # per-equation in-sample R^2
    horizon: int

    def as_dict(self) -> dict:
        return asdict(self)


def fit_var1(panel: np.ndarray, names: Sequence[str]) -> MacroModel:
    """
    OLS fit of a VAR(1) to `panel` (T x k). Returns coefficient matrix A,
    intercept c, and per-equation R^2.
    """
    Y = np.asarray(panel, dtype=float)
    if Y.ndim != 2 or Y.shape[0] < 10:
        raise ValueError("panel must be (T x k) with T >= 10 rows.")
    T, k = Y.shape
    y_t = Y[1:]                       # (T-1) x k  targets
    x_t = Y[:-1]                      # (T-1) x k  lag-1 regressors
    X = np.hstack([np.ones((T - 1, 1)), x_t])   # add intercept column

    # Least-squares solve for each equation simultaneously: B = (X'X)^-1 X'y
    B, *_ = np.linalg.lstsq(X, y_t, rcond=None)   # (k+1) x k
    intercept = B[0]
    A = B[1:].T                       # k x k  (rows = target eqns)

    # Per-equation R^2.
    resid = y_t - X @ B
    ss_res = np.sum(resid ** 2, axis=0)
    ss_tot = np.sum((y_t - y_t.mean(axis=0)) ** 2, axis=0)
    r2 = 1.0 - np.divide(ss_res, ss_tot, out=np.zeros_like(ss_res),
                         where=ss_tot > 0)

    return MacroModel(
        names=list(names), coef=A.tolist(), intercept=intercept.tolist(),
        r_squared=r2.tolist(), horizon=0,
    )


def impulse_response(model: MacroModel, shock: dict[str, float],
                     horizon: int = 12) -> np.ndarray:
    """
    Deterministic impulse response: propagate a one-time shock vector through
    A for `horizon` steps. Returns an (horizon+1) x k array of responses.
    """
    names = model.names
    A = np.array(model.coef, dtype=float)
    k = len(names)
    x0 = np.zeros(k)
    for nm, mag in shock.items():
        if nm in names:
            x0[names.index(nm)] = mag

    path = np.zeros((horizon + 1, k))
    path[0] = x0
    for h in range(1, horizon + 1):
        path[h] = A @ path[h - 1]
    return path


def propagate(model: MacroModel, source: str, channel: str, target: str,
              shock_magnitude: float = 1.0, horizon: int = 12) -> PropagationLink:
    """
    Summarize source -> channel -> target propagation as a single link with a
    peak impact and a credibility score (min R^2 along the path).
    """
    names = model.names
    path = impulse_response(model, {source: shock_magnitude}, horizon)
    t_idx = names.index(target)
    # Peak (max abs) response of the target over the horizon.
    target_resp = path[:, t_idx]
    peak = float(target_resp[np.argmax(np.abs(target_resp))])

    r2 = model.r_squared
    cred_idx = [names.index(n) for n in (channel, target) if n in names]
    credibility = float(np.clip(min(r2[i] for i in cred_idx) if cred_idx else 0.0, 0, 1))

    return PropagationLink(
        source=source, channel=channel, target=target,
        impact_pct=round(peak * 100, 3), credibility=round(credibility, 3),
    )


def default_macro_trace(panel: np.ndarray, names: Sequence[str]) -> dict:
    """
    Convenience: fit the model and return the canonical
    rates -> valuations -> implied-vol -> portfolio trace for the UI.
    """
    model = fit_var1(panel, names)
    links = []
    chain = list(names)
    for i in range(len(chain) - 2):
        links.append(propagate(model, chain[i], chain[i + 1], chain[i + 2]).as_dict())
    return {"model": model.as_dict(), "links": links}
