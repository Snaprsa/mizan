"""
Valuation Engine — Stage 3 scaffold.

The adjustment engine proposes adjustments, humans approve.
Rules-first, pattern-learning later, never auto-apply.
"""

from abc import ABC, abstractmethod
from uuid import UUID

from schemas._future import Adjustment, SubjectProperty
from schemas.comparable import Comparable


class AdjustmentEngine(ABC):
    """
    Interface for proposing comparable adjustments.
    
    Rules:
    - AI/rules SUGGEST adjustments
    - Human APPROVES every adjustment
    - Every adjustment must have evidence or be classified as JUDGMENT
    - Never auto-apply without explicit approval
    """

    @abstractmethod
    async def propose_adjustments(
        self,
        subject: SubjectProperty,
        comparables: list[Comparable],
    ) -> list[Adjustment]:
        """
        Propose adjustments for each comparable relative to subject.
        Returns unapproved adjustment proposals.
        """
        ...


class RulesEngine(AdjustmentEngine):
    """Rule-based adjustment proposals — TODO: Stage 3."""

    async def propose_adjustments(
        self,
        subject: SubjectProperty,
        comparables: list[Comparable],
    ) -> list[Adjustment]:
        # TODO: Implement rule-based adjustments
        # Examples:
        # - Time adjustment based on market index
        # - Size adjustment per sqm rate curve
        # - Location adjustment based on district premium/discount
        # - Condition adjustment
        raise NotImplementedError("Stage 3: Rules engine not yet built")


class ApprovalWorkflow:
    """Approval workflow for adjustments — TODO: Stage 3."""

    async def submit_for_approval(self, adjustments: list[Adjustment]) -> None:
        raise NotImplementedError("Stage 3: Approval workflow not yet built")

    async def approve(self, adjustment_id: UUID, user_id: UUID, notes: str = "") -> Adjustment:
        raise NotImplementedError("Stage 3: Approval workflow not yet built")

    async def reject(self, adjustment_id: UUID, user_id: UUID, reason: str) -> Adjustment:
        raise NotImplementedError("Stage 3: Approval workflow not yet built")
