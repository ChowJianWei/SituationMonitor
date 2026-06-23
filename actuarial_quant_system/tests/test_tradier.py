import asyncio

import httpx

from src.execution.tradier_connector import (
    TradierConnector,
    contracts_for_notional,
    pick_otm_put,
    shares_for_notional,
)


def _connector(handler):
    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport,
                               base_url="https://sandbox.tradier.com/v1",
                               headers={"Accept": "application/json"})
    return TradierConnector("tok", "acct123", "sandbox", client=client)


def test_get_quote_single():
    def h(req):
        assert req.url.params["symbols"] == "AAPL"
        return httpx.Response(200, json={"quotes": {"quote": {"symbol": "AAPL", "last": 150.0}}})
    q = asyncio.run(_connector(h).get_quote("AAPL"))
    assert q["symbol"] == "AAPL" and q["last"] == 150.0


def test_place_equity_order_builds_payload_and_parses_id():
    seen = {}

    def h(req):
        if req.url.path.endswith("/orders"):
            seen["body"] = req.content.decode()
            return httpx.Response(200, json={"order": {"id": 987, "status": "ok"}})
        return httpx.Response(404, json={})

    res = asyncio.run(_connector(h).place_equity_order("AAPL", "buy", 10))
    assert res.ok and res.order_id == 987
    for token in ("class=equity", "symbol=AAPL", "side=buy", "quantity=10",
                  "type=market", "duration=day"):
        assert token in seen["body"]


def test_validate_reports_paper_and_no_withdrawal():
    out = asyncio.run(_connector(lambda r: httpx.Response(200, json={"profile": {"id": "x"}})).validate())
    assert out["valid"] and out["paper"] is True and out["withdrawal_enabled"] is False


def test_option_order_uses_sell_to_open():
    seen = {}

    def h(req):
        seen["body"] = req.content.decode()
        return httpx.Response(200, json={"order": {"id": 5, "status": "ok"}})

    res = asyncio.run(_connector(h).place_option_order("AAPL", "AAPL240119P00150000",
                                                       "sell_to_open", 1))
    assert res.ok
    assert "class=option" in seen["body"] and "side=sell_to_open" in seen["body"]
    assert "option_symbol=AAPL240119P00150000" in seen["body"]


def test_pick_otm_put_selects_below_spot():
    chain = [
        {"option_type": "put", "strike": 140, "symbol": "P140"},
        {"option_type": "put", "strike": 145, "symbol": "P145"},
        {"option_type": "put", "strike": 155, "symbol": "P155"},  # ITM, excluded
        {"option_type": "call", "strike": 145, "symbol": "C145"},
    ]
    put = pick_otm_put(chain, spot=150, otm_pct=0.05)  # target 142.5
    assert put["option_type"] == "put" and put["strike"] in (140, 145)


def test_pick_otm_put_none_when_no_puts():
    assert pick_otm_put([{"option_type": "call", "strike": 100, "symbol": "C"}], 100) is None


def test_sizing_helpers():
    assert contracts_for_notional(20_000, 100) == 2    # 100*100 = 10k per contract
    assert contracts_for_notional(500, 100) == 1       # floor to >= 1
    assert shares_for_notional(1_000, 250) == 4
    assert shares_for_notional(1_000, 0) == 0
