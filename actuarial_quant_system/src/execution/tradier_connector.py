"""
tradier_connector.py
====================
Real broker connector for Tradier (US equity options).

Two environments, selected by `env`:
  * "sandbox"    -> https://sandbox.tradier.com/v1   (PAPER money, real API)
  * "production" -> https://api.tradier.com/v1        (REAL money)

The sandbox is itself a paper-trading environment: you can place genuine API
orders that never risk real capital. That makes it the safe place to validate
the full execution loop before going live.

SECURITY (unchanged from the project's posture):
  * The access token must be created WITHOUT withdrawal/transfer scope. Tradier
    money movement (ACH) is a separate, manually-authenticated flow this token
    cannot trigger.
  * There is intentionally NO withdraw/transfer method in this class.
  * Funding the Tradier account (e.g. from your own bank) is a manual step you
    perform yourself, entirely outside this system.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import httpx

logger = logging.getLogger("tradier")

_BASES = {
    "sandbox": "https://sandbox.tradier.com/v1",
    "production": "https://api.tradier.com/v1",
}


@dataclass
class OrderResult:
    ok: bool
    order_id: Optional[int]
    status: Optional[str]
    raw: dict
    error: Optional[str] = None


class TradierConnector:
    """Read + order client for Tradier. Async, fail-soft."""

    def __init__(self, access_token: str, account_id: str, env: str = "sandbox",
                 client: Optional[httpx.AsyncClient] = None):
        self._token = access_token
        self._account_id = account_id
        self._env = env if env in _BASES else "sandbox"
        self._base = _BASES[self._env]
        self._client = client or httpx.AsyncClient(
            base_url=self._base,
            headers={"Authorization": f"Bearer {access_token}",
                     "Accept": "application/json"},
            timeout=12.0,
        )

    @property
    def configured(self) -> bool:
        return bool(self._token and self._account_id)

    @property
    def is_paper(self) -> bool:
        """Sandbox == paper money, even though orders hit a real API."""
        return self._env == "sandbox"

    # ----- READ ---------------------------------------------------------
    async def validate(self) -> dict:
        """Confirm the token works; report environment and paper status."""
        if not self.configured:
            return {"valid": False, "error": "TRADIER_ACCESS_TOKEN / ACCOUNT_ID not set"}
        try:
            r = await self._client.get("/user/profile")
            r.raise_for_status()
            return {"valid": True, "env": self._env, "paper": self.is_paper,
                    "withdrawal_enabled": False}
        except Exception as exc:  # pragma: no cover - network
            return {"valid": False, "error": str(exc), "withdrawal_enabled": False}

    async def get_quote(self, symbol: str) -> dict:
        r = await self._client.get("/markets/quotes", params={"symbols": symbol})
        r.raise_for_status()
        q = r.json().get("quotes", {}).get("quote")
        # Tradier returns a dict for one symbol, list for many.
        return q[0] if isinstance(q, list) else (q or {})

    async def get_expirations(self, symbol: str) -> list[str]:
        r = await self._client.get("/markets/options/expirations",
                                   params={"symbol": symbol})
        r.raise_for_status()
        data = r.json().get("expirations") or {}
        dates = data.get("date", [])
        return dates if isinstance(dates, list) else [dates]

    async def get_option_chain(self, symbol: str, expiration: str) -> list[dict]:
        r = await self._client.get("/markets/options/chains",
                                   params={"symbol": symbol, "expiration": expiration,
                                           "greeks": "true"})
        r.raise_for_status()
        opts = (r.json().get("options") or {}).get("option", [])
        return opts if isinstance(opts, list) else ([opts] if opts else [])

    async def get_balances(self) -> dict:
        r = await self._client.get(f"/accounts/{self._account_id}/balances")
        r.raise_for_status()
        return r.json().get("balances", {})

    async def get_positions(self) -> dict:
        r = await self._client.get(f"/accounts/{self._account_id}/positions")
        r.raise_for_status()
        return r.json().get("positions", {})

    # ----- ORDER (no withdrawal capability exists) ----------------------
    async def place_equity_order(self, symbol: str, side: str, quantity: int,
                                 order_type: str = "market",
                                 duration: str = "day",
                                 price: Optional[float] = None) -> OrderResult:
        """Place an equity order. side: buy|sell|buy_to_cover|sell_short."""
        payload = {"class": "equity", "symbol": symbol, "side": side,
                   "quantity": str(int(quantity)), "type": order_type,
                   "duration": duration}
        if order_type in ("limit", "stop_limit") and price is not None:
            payload["price"] = str(price)
        return await self._submit_order(payload)

    async def place_option_order(self, underlying: str, option_symbol: str,
                                 side: str, quantity: int,
                                 order_type: str = "market",
                                 duration: str = "day",
                                 price: Optional[float] = None) -> OrderResult:
        """side: buy_to_open | sell_to_open | buy_to_close | sell_to_close."""
        payload = {"class": "option", "symbol": underlying,
                   "option_symbol": option_symbol, "side": side,
                   "quantity": str(int(quantity)), "type": order_type,
                   "duration": duration}
        if order_type in ("limit", "stop_limit") and price is not None:
            payload["price"] = str(price)
        return await self._submit_order(payload)

    async def _submit_order(self, payload: dict) -> OrderResult:
        try:
            r = await self._client.post(f"/accounts/{self._account_id}/orders",
                                        data=payload)
            r.raise_for_status()
            body = r.json().get("order", {})
            return OrderResult(ok=body.get("status") == "ok",
                               order_id=body.get("id"), status=body.get("status"),
                               raw=body)
        except httpx.HTTPStatusError as exc:  # pragma: no cover - network
            return OrderResult(False, None, None, {}, error=f"{exc.response.status_code}: {exc.response.text}")
        except Exception as exc:  # pragma: no cover - network
            return OrderResult(False, None, None, {}, error=str(exc))

    # NOTE: no withdraw / transfer / ACH method exists, by design.

    async def aclose(self) -> None:
        await self._client.aclose()


# ---------------------------------------------------------------------------
# Pure helpers (unit-testable without a live token)
# ---------------------------------------------------------------------------
def pick_otm_put(chain: list[dict], spot: float, otm_pct: float = 0.05) -> Optional[dict]:
    """
    Choose an out-of-the-money put: the put whose strike is closest to
    spot*(1-otm_pct) among strikes at or below spot. Returns the chain row
    (which already carries Tradier's OCC `symbol`) or None.
    """
    puts = [o for o in chain
            if o.get("option_type") == "put" and float(o.get("strike", 0)) <= spot]
    if not puts:
        return None
    target = spot * (1.0 - otm_pct)
    return min(puts, key=lambda o: abs(float(o["strike"]) - target))


def contracts_for_notional(notional_usd: float, strike: float) -> int:
    """Number of option contracts (x100 multiplier) to back `notional_usd`."""
    per_contract = max(strike * 100.0, 1.0)
    return max(1, int(notional_usd // per_contract))


def shares_for_notional(notional_usd: float, price: float) -> int:
    """Whole shares for a delta-one equity leg."""
    if price <= 0:
        return 0
    return max(0, int(notional_usd // price))
