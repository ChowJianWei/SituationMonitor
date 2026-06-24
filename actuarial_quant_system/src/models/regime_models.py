"""
regime_models.py
================
Market-regime and volatility mathematics, implemented in pure numpy / scipy.

    * GARCH(1,1)  -> conditional volatility & one-step forecast (clustering).
    * GaussianHMM -> latent regime classification (Trending / Choppy / Tail-Stress).

These feed the Risk Gate and the Daily Briefing. They never place trades.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List

import numpy as np
from scipy.optimize import minimize
from scipy.special import logsumexp


# ---------------------------------------------------------------------------
# GARCH(1,1)
# ---------------------------------------------------------------------------
#
#   sigma^2_t = omega + alpha * eps^2_{t-1} + beta * sigma^2_{t-1}
#
# Fitted by Gaussian quasi-maximum-likelihood. alpha + beta < 1 enforces
# stationarity (mean-reverting variance).
# ---------------------------------------------------------------------------


@dataclass
class GarchResult:
    omega: float
    alpha: float
    beta: float
    persistence: float            # alpha + beta
    long_run_vol: float           # unconditional sigma (per step)
    current_vol: float            # latest conditional sigma
    forecast_vol: float           # one-step-ahead sigma forecast
    converged: bool

    def as_dict(self) -> dict:
        return asdict(self)


def fit_garch(returns: np.ndarray) -> GarchResult:
    """Fit GARCH(1,1) to a 1-D return series by QMLE."""
    r = np.asarray(returns, dtype=float)
    r = r[np.isfinite(r)]
    if r.size < 50:
        raise ValueError("Need >= 50 returns to fit GARCH(1,1).")

    # Rescale to percentage points for numerical conditioning; undone at the end.
    scale = 100.0
    r = (r - r.mean()) * scale
    var0 = float(np.var(r))

    def neg_loglik(theta: np.ndarray) -> float:
        omega, alpha, beta = theta
        if omega <= 0 or alpha < 0 or beta < 0 or (alpha + beta) >= 1.0:
            return 1e12
        sigma2 = np.empty(r.size)
        sigma2[0] = var0
        for t in range(1, r.size):
            sigma2[t] = omega + alpha * r[t - 1] ** 2 + beta * sigma2[t - 1]
        # Gaussian log-likelihood (drop constants).
        ll = -0.5 * np.sum(np.log(sigma2) + r ** 2 / sigma2)
        return -ll

    # Sensible start: low ARCH, high GARCH persistence.
    theta0 = np.array([var0 * 0.05, 0.08, 0.90])
    bounds = [(1e-12, None), (0.0, 1.0), (0.0, 1.0)]
    cons = {"type": "ineq", "fun": lambda th: 0.999 - (th[1] + th[2])}

    res = minimize(
        neg_loglik, theta0, method="SLSQP", bounds=bounds,
        constraints=cons, options={"maxiter": 500, "ftol": 1e-9},
    )
    omega, alpha, beta = res.x

    # Rebuild the conditional variance path with fitted params.
    sigma2 = np.empty(r.size)
    sigma2[0] = var0
    for t in range(1, r.size):
        sigma2[t] = omega + alpha * r[t - 1] ** 2 + beta * sigma2[t - 1]

    persistence = alpha + beta
    long_run_var = omega / (1.0 - persistence) if persistence < 1 else float("nan")
    forecast_var = omega + alpha * r[-1] ** 2 + beta * sigma2[-1]

    return GarchResult(
        omega=float(omega) / scale ** 2,
        alpha=float(alpha),
        beta=float(beta),
        persistence=float(persistence),
        long_run_vol=float(np.sqrt(long_run_var)) / scale,
        current_vol=float(np.sqrt(sigma2[-1])) / scale,
        forecast_vol=float(np.sqrt(forecast_var)) / scale,
        converged=bool(res.success),
    )


# ---------------------------------------------------------------------------
# Gaussian Hidden Markov Model (univariate)
# ---------------------------------------------------------------------------
#
# A compact, self-contained Baum-Welch / Viterbi implementation in log-space.
# States are labelled by their (mean, vol) signature into market regimes.
# ---------------------------------------------------------------------------


REGIME_LABELS = ["TAIL_STRESS", "CHOPPY_MEAN_REVERT", "TRENDING"]


@dataclass
class RegimeResult:
    n_states: int
    means: List[float]
    vols: List[float]
    transition_matrix: List[List[float]]
    state_path: List[int]
    current_state: int
    current_regime: str
    regime_labels: List[str]
    state_probabilities: List[float]   # posterior of current observation
    log_likelihood: float
    converged: bool

    def as_dict(self) -> dict:
        return asdict(self)


class GaussianHMM:
    """Univariate Gaussian-emission HMM fitted with scaled Baum-Welch."""

    def __init__(self, n_states: int = 3, n_iter: int = 150,
                 tol: float = 1e-3, seed: int = 7):
        self.k = n_states
        self.n_iter = n_iter
        self.tol = tol
        self.rng = np.random.default_rng(seed)
        self.pi: np.ndarray | None = None
        self.A: np.ndarray | None = None
        self.mu: np.ndarray | None = None
        self.var: np.ndarray | None = None
        self.converged_ = False

    # -- emissions -------------------------------------------------------
    def _log_emission(self, x: np.ndarray) -> np.ndarray:
        """T x K matrix of Gaussian log-densities."""
        var = np.maximum(self.var, 1e-12)
        diff = x[:, None] - self.mu[None, :]
        return -0.5 * (np.log(2 * np.pi * var)[None, :] + diff ** 2 / var[None, :])

    # -- init ------------------------------------------------------------
    def _initialize(self, x: np.ndarray) -> None:
        # Seed state means at return quantiles so states are well separated.
        qs = np.linspace(0.1, 0.9, self.k)
        self.mu = np.quantile(x, qs)
        self.var = np.full(self.k, np.var(x) + 1e-8)
        self.pi = np.full(self.k, 1.0 / self.k)
        # Sticky transition matrix (regimes persist).
        self.A = np.full((self.k, self.k), 0.1 / max(self.k - 1, 1))
        np.fill_diagonal(self.A, 0.9)

    # -- forward/backward (log space) ------------------------------------
    def _forward_backward(self, log_B: np.ndarray):
        T = log_B.shape[0]
        log_pi = np.log(self.pi + 1e-300)
        log_A = np.log(self.A + 1e-300)

        log_alpha = np.empty((T, self.k))
        log_alpha[0] = log_pi + log_B[0]
        for t in range(1, T):
            log_alpha[t] = log_B[t] + logsumexp(
                log_alpha[t - 1][:, None] + log_A, axis=0
            )

        log_beta = np.zeros((T, self.k))
        for t in range(T - 2, -1, -1):
            log_beta[t] = logsumexp(
                log_A + log_B[t + 1][None, :] + log_beta[t + 1][None, :], axis=1
            )

        ll = logsumexp(log_alpha[-1])
        log_gamma = log_alpha + log_beta - ll
        return log_alpha, log_beta, log_gamma, log_A, ll

    # -- fit -------------------------------------------------------------
    def fit(self, x: np.ndarray) -> "GaussianHMM":
        x = np.asarray(x, dtype=float)
        x = x[np.isfinite(x)]
        if x.size < 30:
            raise ValueError("Need >= 30 observations to fit the HMM.")
        self._initialize(x)
        T = x.size
        prev_ll = -np.inf

        for _ in range(self.n_iter):
            log_B = self._log_emission(x)
            log_alpha, log_beta, log_gamma, log_A, ll = self._forward_backward(log_B)
            gamma = np.exp(log_gamma)

            # xi: T-1 x K x K joint posteriors.
            log_xi = (
                log_alpha[:-1, :, None]
                + log_A[None, :, :]
                + log_B[1:, None, :]
                + log_beta[1:, None, :]
                - ll
            )
            xi = np.exp(log_xi)

            # M-step.
            self.pi = gamma[0] / gamma[0].sum()
            A_num = xi.sum(axis=0)
            A_den = gamma[:-1].sum(axis=0)[:, None]
            self.A = A_num / np.maximum(A_den, 1e-300)
            self.A /= self.A.sum(axis=1, keepdims=True)

            gsum = gamma.sum(axis=0)
            self.mu = (gamma * x[:, None]).sum(axis=0) / np.maximum(gsum, 1e-300)
            self.var = (gamma * (x[:, None] - self.mu[None, :]) ** 2).sum(axis=0)
            self.var = self.var / np.maximum(gsum, 1e-300)
            self.var = np.maximum(self.var, 1e-10)

            if abs(ll - prev_ll) < self.tol * (1.0 + abs(ll)):
                self.converged_ = True
                break
            prev_ll = ll

        self._last_ll = float(ll)
        return self

    # -- viterbi ---------------------------------------------------------
    def viterbi(self, x: np.ndarray) -> np.ndarray:
        x = np.asarray(x, dtype=float)
        log_B = self._log_emission(x)
        T = x.size
        log_pi = np.log(self.pi + 1e-300)
        log_A = np.log(self.A + 1e-300)

        delta = np.empty((T, self.k))
        psi = np.zeros((T, self.k), dtype=int)
        delta[0] = log_pi + log_B[0]
        for t in range(1, T):
            scores = delta[t - 1][:, None] + log_A
            psi[t] = np.argmax(scores, axis=0)
            delta[t] = log_B[t] + np.max(scores, axis=0)

        path = np.empty(T, dtype=int)
        path[-1] = int(np.argmax(delta[-1]))
        for t in range(T - 2, -1, -1):
            path[t] = psi[t + 1, path[t + 1]]
        return path

    # -- regime labelling ------------------------------------------------
    def _label_states(self) -> List[str]:
        """
        Map raw HMM states to human regime names by their (vol, mean) signature:
            highest variance         -> TAIL_STRESS
            of the remaining, the one with mean closest to 0 -> CHOPPY_MEAN_REVERT
            the other                -> TRENDING
        Generalizes gracefully if k != 3.
        """
        order_by_vol = np.argsort(self.var)          # ascending vol
        labels = [""] * self.k
        # Highest-vol state is tail stress.
        labels[order_by_vol[-1]] = "TAIL_STRESS"
        remaining = list(order_by_vol[:-1])
        if remaining:
            # Among remaining, smallest |mean| is choppy/mean-reverting.
            choppy = min(remaining, key=lambda s: abs(self.mu[s]))
            labels[choppy] = "CHOPPY_MEAN_REVERT"
            for s in remaining:
                if labels[s] == "":
                    labels[s] = "TRENDING"
        return labels

    def describe(self, x: np.ndarray) -> RegimeResult:
        path = self.viterbi(x)
        labels = self._label_states()
        # Posterior of the most recent observation.
        log_B = self._log_emission(np.asarray(x, dtype=float))
        _, _, log_gamma, _, ll = self._forward_backward(log_B)
        post_now = np.exp(log_gamma[-1])
        cur = int(path[-1])
        return RegimeResult(
            n_states=self.k,
            means=self.mu.tolist(),
            vols=np.sqrt(self.var).tolist(),
            transition_matrix=self.A.tolist(),
            state_path=path.tolist(),
            current_state=cur,
            current_regime=labels[cur],
            regime_labels=labels,
            state_probabilities=post_now.tolist(),
            log_likelihood=float(ll),
            converged=self.converged_,
        )


def detect_regime(returns: np.ndarray, n_states: int = 3) -> RegimeResult:
    """Convenience wrapper: fit HMM and return a labelled regime snapshot."""
    hmm = GaussianHMM(n_states=n_states).fit(returns)
    return hmm.describe(returns)


def simulate_clustered_returns(n: int = 1500, seed: int = 1,
                               stress_at: float | None = 0.85) -> np.ndarray:
    """
    Generate a realistic return series with genuine volatility CLUSTERING
    (a GARCH(1,1) data-generating process) plus an optional late tail-stress
    burst. Used to seed demos so GARCH/HMM fits converge to meaningful regimes
    instead of collapsing on i.i.d. noise.
    """
    rng = np.random.default_rng(seed)
    omega, alpha, beta = 2e-6, 0.09, 0.89
    r = np.zeros(n)
    sigma2 = np.full(n, omega / (1.0 - alpha - beta))
    stress_idx = int(n * stress_at) if stress_at is not None else n + 1
    for t in range(1, n):
        sigma2[t] = omega + alpha * r[t - 1] ** 2 + beta * sigma2[t - 1]
        shock = 3.0 if stress_idx <= t < stress_idx + 30 else 1.0  # tail burst
        r[t] = rng.normal(0.0004, np.sqrt(sigma2[t]) * shock)
    return r
