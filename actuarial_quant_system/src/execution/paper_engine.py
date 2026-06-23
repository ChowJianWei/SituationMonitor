"""
paper_engine.py
===============
Paper (simulated) execution engine — the "auto-invest" loop, with ZERO real-money
capability.

This is the deliberate stand-in for live execution. It runs the full underwriting
cycle end to end — proposal -> hardcoded risk gate -> simulated fill -> reserve
lock -> persistence -> audit — but every fill is synthetic. There is no path to a
real venue here; going live requires a separate, explicitly trade-scoped
connector and a validated paper track record. Until then the system is fully
autonomous on paper and completely safe.

Slippage and transaction costs are modelled so paper PnL is not naively optimistic.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from ..data_pipeline.database import Database
from ..data_pipeline.state_store import StateStore
from ..risk_gate.pre_trade_check import (
    AccountState,
    TradeIntent,
    Verdict,
    check_trade,
)
from .strategy_selector import StrategyProposal, Structure

logger = logging.getLogger("paper_engine")

# Cost model (basis points of notional).
SLIPPAGE_BPS = 5.0
FEE_BPS = 2.0


@dataclass
class FillResult:
    proposal: StrategyProposal
    verdict: str
    fill_price: float
    slippage_usd: float
    fee_usd: float
    executed: bool
    reasons: list[str]

    def as_dict(self) -> dict:
        return {
            "symbol": self.proposal.symbol,
            "structure": self.proposal.structure.value,
            "side": self.proposal.side,
            "notional_usd": self.proposal.notional_usd,
            "verdict": self.verdict,
            "fill_price": self.fill_price,
            "slippage_usd": self.slippage_usd,
            "fee_usd": self.fee_usd,
            "executed": self.executed,
            "reasons": self.reasons,
        }


class PaperExecutionEngine:
    """Risk-gated, persistence-backed simulator. Never touches real funds."""

    def __init__(self, db: Database, state: StateStore):
        self._db = db
        self._state = state

    def _simulate_fill(self, ref_price: float, side: str, notional: float) -> tuple[float, float, float]:
        """Return (fill_price, slippage_usd, fee_usd) with adverse slippage."""
        slip = ref_price * (SLIPPAGE_BPS / 10_000.0)
        # Buying fills slightly higher, selling slightly lower (adverse).
        fill_price = ref_price + slip if side == "BUY" else ref_price - slip
        slippage_usd = notional * (SLIPPAGE_BPS / 10_000.0)
        fee_usd = notional * (FEE_BPS / 10_000.0)
        return round(fill_price, 4), round(slippage_usd, 2), round(fee_usd, 2)

    async def execute(self, proposal: StrategyProposal, account: AccountState,
                      ref_price: float, account_id: Optional[int] = None) -> FillResult:
        """Run one proposal through the gate and (if approved) simulate a fill."""
        # RAISE_CASH is a de-risking action, not a new liability — no gate needed.
        if proposal.structure is Structure.RAISE_CASH:
            await self._db.write_audit("engine", "defensive_raise_cash",
                                       {"symbol": proposal.symbol})
            return FillResult(proposal, "APPROVED", ref_price, 0.0, 0.0, True,
                              ["Defensive de-risk; no new exposure."])

        intent = TradeIntent(
            symbol=proposal.symbol, side=proposal.side,
            notional_usd=proposal.notional_usd,
        )
        decision = check_trade(intent, account)

        if not decision.approved:
            await self._db.write_audit("risk_gate", "order_rejected", {
                "symbol": proposal.symbol, "reasons": decision.reasons,
            })
            await self._db.save_trade({
                "account_id": account_id, "symbol": proposal.symbol,
                "structure": proposal.structure.value, "side": proposal.side,
                "notional_usd": proposal.notional_usd, "fill_price": 0.0,
                "paper": True, "risk_verdict": Verdict.REJECTED.value,
                "rationale": "; ".join(decision.reasons),
            })
            return FillResult(proposal, Verdict.REJECTED.value, 0.0, 0.0, 0.0,
                              False, decision.reasons)

        # Approved -> simulate the fill.
        fill_price, slippage, fee = self._simulate_fill(
            ref_price, proposal.side, proposal.notional_usd
        )

        # Lock the dynamic loss reserve in live state (survives reboot via Redis).
        if proposal.loss_reserve_usd > 0:
            await self._state.lock_loss_reserve(proposal.symbol, proposal.loss_reserve_usd)

        # Persist position, trade and audit.
        await self._db.upsert_position({
            "account_id": account_id, "symbol": proposal.symbol,
            "structure": proposal.structure.value, "side": proposal.side,
            "notional_usd": proposal.notional_usd, "entry_price": fill_price,
            "delta": proposal.est_delta, "vega": proposal.est_vega,
            "loss_reserve_usd": proposal.loss_reserve_usd,
        })
        await self._db.save_trade({
            "account_id": account_id, "symbol": proposal.symbol,
            "structure": proposal.structure.value, "side": proposal.side,
            "notional_usd": proposal.notional_usd, "fill_price": fill_price,
            "slippage_usd": slippage, "fee_usd": fee, "paper": True,
            "risk_verdict": Verdict.APPROVED.value, "rationale": proposal.rationale,
        })
        await self._db.write_audit("engine", "paper_fill", {
            "symbol": proposal.symbol, "structure": proposal.structure.value,
            "notional": proposal.notional_usd, "fill_price": fill_price,
        })
        logger.info("PAPER FILL %s %s $%.0f @ %.2f", proposal.side,
                    proposal.symbol, proposal.notional_usd, fill_price)

        return FillResult(proposal, Verdict.APPROVED.value, fill_price,
                          slippage, fee, True, [proposal.rationale])
