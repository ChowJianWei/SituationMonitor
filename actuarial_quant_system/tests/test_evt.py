import numpy as np
import pytest

from src.models.actuarial_engine import compute_loss_reserve, fit_gpd_tail_risk


def _heavy_tailed_losses(seed=0, n=2000):
    rng = np.random.default_rng(seed)
    # Mixture of normal + occasional large losses -> fat right tail.
    base = np.abs(rng.normal(0.005, 0.01, n))
    spikes = np.abs(rng.normal(0.05, 0.03, n)) * (rng.random(n) < 0.05)
    return base + spikes


def test_cvar_at_least_var():
    losses = _heavy_tailed_losses()
    t = fit_gpd_tail_risk(losses, confidence=0.99, threshold_quantile=0.95)
    assert t.cvar >= t.var > 0


def test_too_few_observations_raises():
    with pytest.raises(ValueError):
        fit_gpd_tail_risk(np.array([0.01, 0.02, 0.03]))


def test_higher_confidence_raises_var():
    losses = _heavy_tailed_losses(seed=2)
    t95 = fit_gpd_tail_risk(losses, confidence=0.95, threshold_quantile=0.90)
    t99 = fit_gpd_tail_risk(losses, confidence=0.99, threshold_quantile=0.90)
    assert t99.var >= t95.var


def test_loss_reserve_takes_max_of_margin_and_tail():
    # Large CVaR fraction should dominate a small margin rate.
    r = compute_loss_reserve(notional=100_000, margin_rate=0.05, cvar_fraction=0.20)
    assert r.tail_buffer > r.initial_margin
    assert r.required_reserve > r.tail_buffer  # prudence load adds on top
    assert 0 < r.reserve_ratio < 1
