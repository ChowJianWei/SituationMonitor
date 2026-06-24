import numpy as np

from src.models.signals import (
    Action,
    generate_signal,
    realized_vol_close_to_close,
    variance_risk_premium,
)


def test_realized_vol_positive():
    rng = np.random.default_rng(0)
    rv = realized_vol_close_to_close(rng.normal(0, 0.01, 500))
    assert rv > 0


def test_vrp_flags_rich_insurance():
    v = variance_risk_premium(implied_vol=0.40, realized_vol=0.20)
    assert v.insurance_is_rich and v.richness_ratio == 2.0
    assert v.vrp_variance > 0


def test_vrp_not_rich_when_fair():
    v = variance_risk_premium(implied_vol=0.21, realized_vol=0.20)
    assert not v.insurance_is_rich


def test_tail_stress_forces_defensive():
    v = variance_risk_premium(0.40, 0.20)
    sig = generate_signal("TAIL_STRESS", v)
    assert sig.action is Action.DEFENSIVE


def test_choppy_rich_sells_vol():
    v = variance_risk_premium(0.40, 0.20)
    sig = generate_signal("CHOPPY_MEAN_REVERT", v, regime_confidence=0.7)
    assert sig.action is Action.SELL_VOL


def test_trending_cheap_buys_spot():
    v = variance_risk_premium(0.21, 0.20)
    sig = generate_signal("TRENDING", v)
    assert sig.action is Action.BUY_SPOT
