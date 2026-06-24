import numpy as np

from src.models.actuarial_engine import (
    TradeMetrics,
    lundberg_adjustment_coefficient,
    simulate_ruin_probability,
)


def test_net_drift_sign():
    profitable = TradeMetrics(1.0, 0.6, 500.0, 400.0)
    assert profitable.net_drift > 0
    losing = TradeMetrics(1.0, 0.4, 400.0, 500.0)
    assert losing.net_drift < 0


def test_zero_surplus_is_certain_ruin():
    m = TradeMetrics(1.0, 0.55, 400.0, 500.0)
    res = simulate_ruin_probability(surplus=0.0, metrics=m, horizon=100, n_paths=50)
    assert res.ruin_probability == 1.0


def test_ruin_probability_in_unit_interval():
    m = TradeMetrics(1.0, 0.55, 420.0, 510.0)
    res = simulate_ruin_probability(surplus=50_000, metrics=m, horizon=1000, n_paths=400)
    assert 0.0 <= res.ruin_probability <= 1.0


def test_more_surplus_lowers_ruin():
    m = TradeMetrics(1.0, 0.56, 420.0, 500.0)
    low = simulate_ruin_probability(2_000, m, horizon=2000, n_paths=600, seed=1)
    high = simulate_ruin_probability(80_000, m, horizon=2000, n_paths=600, seed=1)
    assert high.ruin_probability <= low.ruin_probability


def test_lundberg_coefficient_positive_for_profitable_book():
    m = TradeMetrics(1.0, 0.6, 500.0, 400.0)
    R = lundberg_adjustment_coefficient(m)
    assert R is not None and R > 0


def test_lundberg_none_for_unprofitable_book():
    # Premium below expected claims -> no positive adjustment coefficient.
    m = TradeMetrics(1.0, 0.3, 100.0, 1000.0)
    assert lundberg_adjustment_coefficient(m) is None
