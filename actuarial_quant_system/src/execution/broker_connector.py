"""
broker_connector.py
==================
Execution-layer adapter for cash and derivative venues.

================================================================================
SECURITY POSTURE  --  WHY THIS SYSTEM CANNOT MOVE YOUR MONEY OUT
================================================================================
This connector is structurally incapable of withdrawing funds or touching a
bank network. That is enforced at THREE independent layers:

1. API-KEY SCOPING (cryptographic, enforced by the venue, not by us)
   ---------------------------------------------------------------------------
   The API keys this service loads MUST be minted with the narrowest scope the
   exchange offers:
       * READ            -> market data, balances, positions          (REQUIRED)
       * TRADE           -> place / cancel orders                     (OPTIONAL*)
       * WITHDRAW        -> move funds off-venue                       (NEVER)
   The withdrawal permission is disabled at key-creation time on the exchange.
   Even if this entire codebase were compromised, the signed requests it can
   produce are cryptographically rejected for any withdrawal endpoint, because
   the key simply lacks that capability server-side. We never hold a key that
   can call `POST /v1/withdraw`.
   (*) TRADE scope stays OFF until a validated paper track record exists; until
   then this service is read-only/informational (see PAPER_TRADING_ONLY).

2. NO WITHDRAWAL CODE PATH (structural)
   ---------------------------------------------------------------------------
   There is intentionally NO withdraw(), transfer(), payout(), or
   send_to_bank() method anywhere in this class or module. You cannot call a
   method that does not exist. This absence is part of the audited surface area.

3. NO BANK-NETWORK REACHABILITY (network isolation)
   ---------------------------------------------------------------------------
   This service has NO ACH, SWIFT, wire, FedNow, SEPA, or card-rail integration
   of any kind. It speaks only HTTPS/WSS to the exchange market-data and (later)
   order endpoints. It holds no bank credentials, no routing/account numbers,
   and no payment-processor tokens. Money that arrives on the venue can only
   leave the venue through a manual, human-initiated withdrawal performed
   OUTSIDE this system, from a separately-scoped key/credential.

The net effect: this engine can observe markets and (eventually, on an
explicitly trade-scoped key) place risk-gated orders, but it can never
exfiltrate capital. Capital survival is enforced by what the code *cannot* do.
================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

import httpx

from ..risk_gate.pre_trade_check import (
    AccountState,
    RiskDecision,
    TradeIntent,
    Verdict,
    check_trade,
)


class KeyScope(str, Enum):
    READ_ONLY = "READ_ONLY"     # default & only safe state for this service
    READ_TRADE = "READ_TRADE"   # opt-in, paper-validated strategies only


@dataclass(frozen=True)
class BrokerCredentials:
    """
    Credentials container. Note there is no field for any banking/withdrawal
    secret -- by construction this object can only authenticate read (and,
    optionally, trade) requests.
    """
    api_key: str
    api_secret: str
    scope: KeyScope = KeyScope.READ_ONLY


class BrokerConnector:
    """
    Read-first market/position adapter. Order placement is double-gated:
    (a) the service must be out of PAPER_TRADING_ONLY mode AND on a READ_TRADE
    key, and (b) every ticket must pass the hardcoded risk gate.
    """

    def __init__(
        self,
        base_url: str,
        credentials: BrokerCredentials,
        paper_trading_only: bool = True,
    ):
        self._base_url = base_url.rstrip("/")
        self._creds = credentials
        self._paper_trading_only = paper_trading_only
        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=10.0)

    # ----- READ surface (always available) ------------------------------
    async def get_quote(self, symbol: str) -> dict:
        """GET market data. Uses only the READ scope of the key."""
        resp = await self._client.get(f"/v1/marketdata/{symbol}")
        resp.raise_for_status()
        return resp.json()

    async def get_positions(self) -> dict:
        """GET current positions/balances. READ scope only."""
        resp = await self._client.get("/v1/account/positions")
        resp.raise_for_status()
        return resp.json()

    # ----- WRITE surface (gated; never withdrawal) ----------------------
    async def place_order(
        self, intent: TradeIntent, account: AccountState
    ) -> RiskDecision:
        """
        Attempt to place ONE order. Returns the risk decision. The order is only
        forwarded to the venue if (1) we are not in paper-only mode, (2) the key
        carries READ_TRADE scope, and (3) the hardcoded risk gate APPROVES.

        This method handles ORDERS only. It has no capability to move funds.
        """
        decision = check_trade(intent, account)
        if not decision.approved:
            return decision

        if self._paper_trading_only:
            decision.reasons.append("PAPER_TRADING_ONLY: order simulated, not sent.")
            return decision

        if self._creds.scope is not KeyScope.READ_TRADE:
            decision.verdict = Verdict.REJECTED
            decision.reasons.append("Live order blocked: key lacks READ_TRADE scope.")
            return decision

        # Real order submission would happen here against /v1/orders, signed with
        # a TRADE-scoped (never WITHDRAW-scoped) key.
        resp = await self._client.post(
            "/v1/orders",
            json={
                "symbol": intent.symbol,
                "side": intent.side,
                "notional": intent.notional_usd,
            },
        )
        resp.raise_for_status()
        decision.reasons.append("Order forwarded to venue (trade-scoped key).")
        return decision

    # NOTE: There is intentionally NO withdraw / transfer / payout method.
    #       Its absence is a security control, not an oversight.

    async def aclose(self) -> None:
        await self._client.aclose()
