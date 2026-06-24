from src.models.regime_models import (
    detect_regime,
    fit_garch,
    simulate_clustered_returns,
)


def test_garch_converges_on_clustered_data():
    r = simulate_clustered_returns(n=1000, seed=3, stress_at=None)
    g = fit_garch(r)
    assert g.converged
    assert 0.0 <= g.persistence < 1.0
    assert g.current_vol > 0 and g.forecast_vol > 0


def test_regime_labels_complete():
    r = simulate_clustered_returns(n=1000, seed=4)
    reg = detect_regime(r, n_states=3)
    assert set(reg.regime_labels) == {"TAIL_STRESS", "CHOPPY_MEAN_REVERT", "TRENDING"}
    assert reg.current_regime in reg.regime_labels


def test_state_probabilities_sum_to_one():
    r = simulate_clustered_returns(n=800, seed=5)
    reg = detect_regime(r, n_states=3)
    assert abs(sum(reg.state_probabilities) - 1.0) < 1e-6
