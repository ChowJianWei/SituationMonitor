from src.risk_gate.pre_trade_check import (
    MAX_SINGLE_TRADE_NOTIONAL_USD,
    AccountState,
    TradeIntent,
    Verdict,
    check_trade,
    kill_switch_status,
)


def _healthy_account():
    return AccountState(
        equity_usd=200_000, open_gross_notional_usd=50_000,
        frozen_reserve_usd=20_000, start_of_day_equity_usd=200_000,
    )


def test_approves_within_limits():
    intent = TradeIntent("BTC", "BUY", 10_000)
    d = check_trade(intent, _healthy_account())
    assert d.approved and d.verdict is Verdict.APPROVED


def test_rejects_oversize_single_trade():
    intent = TradeIntent("BTC", "BUY", MAX_SINGLE_TRADE_NOTIONAL_USD + 1)
    d = check_trade(intent, _healthy_account())
    assert not d.approved


def test_kill_switch_trips_on_drawdown_and_latches():
    drawn = AccountState(
        equity_usd=180_000, open_gross_notional_usd=0,
        frozen_reserve_usd=0, start_of_day_equity_usd=200_000,  # -10% > 5% limit
    )
    d = check_trade(TradeIntent("BTC", "BUY", 1_000), drawn)
    assert not d.approved and d.kill_switch_engaged
    assert kill_switch_status() is True
    # Latches: even a healthy account is now blocked until manual reset.
    d2 = check_trade(TradeIntent("BTC", "BUY", 1_000), _healthy_account())
    assert not d2.approved


def test_fail_closed_on_bad_input():
    d = check_trade(TradeIntent("BTC", "SIDEWAYS", -5), _healthy_account())
    assert not d.approved


def test_leverage_cap_enforced():
    acct = AccountState(
        equity_usd=50_000, open_gross_notional_usd=140_000,
        frozen_reserve_usd=0, start_of_day_equity_usd=50_000,
    )
    # Adding even a small ticket pushes gross/equity past the 3x cap.
    d = check_trade(TradeIntent("BTC", "BUY", 20_000), acct)
    assert not d.approved
