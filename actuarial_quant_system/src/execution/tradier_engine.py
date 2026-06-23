"""
tradier_engine.py
=================
Execution engine that routes underwriting proposals to the Tradier API.

Same interface as PaperExecutionEngine (`execute(...)` -> FillResult) so the
underwriting cycle can use either interchangeably. In sandbox mode the orders are
real API calls against paper money; in production they are live. Every order is
still gated by the hardcoded risk firewall first, and persisted to the audit log.

Mapping proposal -> Tradier order:
  BUY_SPOT / CASH_LONG / LONG_FUTURE -> equity BUY (delta-one)
  SELL_VOL  (SHORT_PUT / IRON_CONDOR)-> sell_to_open a single OTM put leg*
  RAISE_CASH                         -> no order (de-risk)

(*) A single short-put leg represents the short-vol structure for the sandbox
milestone; full multi-leg iron condors are a follow-up.
"""

from __future__ import annotations

import logging
from typing import Optional

from ..data_pipeline.database import Database
from ..data_pipeline.state_store import StateStore
from ..risk_gate.pre_trade_check import (
    AccountState,
    TradeIntent,
    Verdict,
    check_trade,
)
from .paper_engine import FillResult
from .strategy_selector import StrategyProposal, Structure
from .tradier_connector import (
    TradierConnector,
    contracts_for_notional,
    pick_otm_put,
    shares_for_notional,
)

logger = logging.getLogger("tradier_engine")


class TradierExecutionEngine:
    """Risk-gated Tradier order router with persistence."""

    def __init__(self, connector: TradierConnector, db: Database, state: StateStore):
        self._tx = connector
        self._db = db
        self._state = state

    async def execute(self, proposal: StrategyProposal, account: AccountState,
                      ref_price: float, account_id: Optional[int] = None) -> FillResult:
        # De-risk action — no order.
        if proposal.structure is Structure.RAISE_CASH:
            await self._db.write_audit("engine", "defensive_raise_cash",
                                       {"symbol": proposal.symbol})
            return FillResult(proposal, "APPROVED", ref_price, 0.0, 0.0, True,
                              ["Defensive de-risk; no new exposure."])

        # 1. Hardcoded risk gate (identical guardrail to the paper path).
        intent = TradeIntent(proposal.symbol, proposal.side, proposal.notional_usd)
        decision = check_trade(intent, account)
        if not decision.approved:
            await self._db.write_audit("risk_gate", "order_rejected",
                                       {"symbol": proposal.symbol, "reasons": decision.reasons})
            await self._persist_trade(proposal, account_id, 0.0, Verdict.REJECTED.value,
                                      "; ".join(decision.reasons))
            return FillResult(proposal, Verdict.REJECTED.value, 0.0, 0.0, 0.0, False,
                              decision.reasons)

        # 2. Build and submit the venue order.
        try:
            if proposal.structure in (Structure.CASH_LONG, Structure.LONG_FUTURE):
                qty = shares_for_notional(proposal.notional_usd, ref_price)
                if qty <= 0:
                    return FillResult(proposal, "REJECTED", 0.0, 0.0, 0.0, False,
                                      ["Notional too small for one share."])
                order = await self._tx.place_equity_order(proposal.symbol, "buy", qty)
                fill_ref = ref_price
            else:  # SELL_VOL -> short put
                order, fill_ref = await self._submit_short_put(proposal, ref_price)
                if order is None:
                    return FillResult(proposal, "REJECTED", 0.0, 0.0, 0.0, False,
                                      ["No suitable OTM put in chain."])
        except Exception as exc:  # pragma: no cover - network
            await self._db.write_audit("engine", "order_error",
                                       {"symbol": proposal.symbol, "error": str(exc)})
            return FillResult(proposal, "REJECTED", 0.0, 0.0, 0.0, False,
                              [f"Venue order error: {exc}"])

        if not order.ok:
            return FillResult(proposal, "REJECTED", 0.0, 0.0, 0.0, False,
                              [f"Venue rejected order: {order.error or order.status}"])

        # 3. Lock reserve + persist (same as paper path).
        if proposal.loss_reserve_usd > 0:
            await self._state.lock_loss_reserve(proposal.symbol, proposal.loss_reserve_usd)
        await self._db.upsert_position({
            "account_id": account_id, "symbol": proposal.symbol,
            "structure": proposal.structure.value, "side": proposal.side,
            "notional_usd": proposal.notional_usd, "entry_price": fill_ref,
            "delta": proposal.est_delta, "vega": proposal.est_vega,
            "loss_reserve_usd": proposal.loss_reserve_usd,
        })
        await self._persist_trade(proposal, account_id, fill_ref,
                                  Verdict.APPROVED.value,
                                  f"{proposal.rationale} [tradier:{order.order_id}]")
        await self._db.write_audit("engine", "tradier_fill", {
            "symbol": proposal.symbol, "order_id": order.order_id,
            "env": "sandbox" if self._tx.is_paper else "production",
        })
        logger.info("TRADIER ORDER %s %s id=%s", proposal.side, proposal.symbol, order.order_id)
        return FillResult(proposal, Verdict.APPROVED.value, fill_ref, 0.0, 0.0, True,
                          [f"Order placed via Tradier (id {order.order_id})."])

    async def _submit_short_put(self, proposal: StrategyProposal, ref_price: float):
        expiries = await self._tx.get_expirations(proposal.symbol)
        if not expiries:
            return None, ref_price
        chain = await self._tx.get_option_chain(proposal.symbol, expiries[0])
        put = pick_otm_put(chain, ref_price)
        if put is None:
            return None, ref_price
        qty = contracts_for_notional(proposal.notional_usd, float(put["strike"]))
        order = await self._tx.place_option_order(
            proposal.symbol, put["symbol"], "sell_to_open", qty)
        bid = float(put.get("bid") or 0)
        ask = float(put.get("ask") or 0)
        mid = (bid + ask) / 2 if (bid and ask) else ref_price
        return order, mid

    async def _persist_trade(self, proposal: StrategyProposal, account_id, fill_price,
                             verdict: str, rationale: str) -> None:
        await self._db.save_trade({
            "account_id": account_id, "symbol": proposal.symbol,
            "structure": proposal.structure.value, "side": proposal.side,
            "notional_usd": proposal.notional_usd, "fill_price": fill_price,
            "slippage_usd": 0.0, "fee_usd": 0.0,
            "paper": self._tx.is_paper, "risk_verdict": verdict, "rationale": rationale,
        })
