import numpy as np

from src.execution.strategy_selector import Structure, select_strategy
from src.models.macro_propagation import fit_var1, propagate
from src.models.signals import Action, Signal, variance_risk_premium


def _signal(action, conf=0.8):
    return Signal(action, conf, "test", variance_risk_premium(0.4, 0.2))


def test_stand_aside_yields_no_proposal():
    p = select_strategy("ETH", _signal(Action.STAND_ASIDE), spot=3500,
                        cvar_fraction=0.1, max_single_trade_usd=25_000)
    assert p is None


def test_sell_vol_high_vol_picks_iron_condor():
    p = select_strategy("ETH", _signal(Action.SELL_VOL), spot=3500,
                        cvar_fraction=0.1, max_single_trade_usd=25_000, high_vol=True)
    assert p is not None and p.structure is Structure.IRON_CONDOR
    assert p.est_delta == 0.0           # delta-neutral
    assert p.loss_reserve_usd > 0       # reserve frozen


def test_buy_spot_is_cash_long_with_delta_one():
    p = select_strategy("BTC", _signal(Action.BUY_SPOT), spot=65000,
                        cvar_fraction=0.1, max_single_trade_usd=25_000)
    assert p.structure is Structure.CASH_LONG and p.est_delta == 1.0


def test_var1_fit_and_propagation():
    rng = np.random.default_rng(0)
    n = 300
    a = np.cumsum(rng.normal(0, 0.1, n))
    b = np.zeros(n); c = np.zeros(n)
    for t in range(1, n):
        b[t] = 0.7 * b[t - 1] - 0.5 * a[t - 1] + rng.normal(0, 0.1)
        c[t] = 0.6 * c[t - 1] + 0.4 * b[t - 1] + rng.normal(0, 0.1)
    panel = np.column_stack([a, b, c])
    model = fit_var1(panel, ["A", "B", "C"])
    assert len(model.coef) == 3 and len(model.coef[0]) == 3
    link = propagate(model, "A", "B", "C")
    assert 0.0 <= link.credibility <= 1.0
