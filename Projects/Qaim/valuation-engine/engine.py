"""Valuation Engine — Stage 3 scaffolding.

This module will contain:
- Adjustment rules engine
- Prior-report pattern learning (human-approved only)
- Approval workflow
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class AdjustmentRule(ABC):
    """Base class for adjustment rules."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @abstractmethod
    def compute(
        self,
        subject: Dict[str, Any],
        comparable: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Compute adjustment. Returns None if not applicable.
        
        Returns dict with:
        - adjustment_type: str
        - adjustment_value: float (SAR)
        - adjustment_pct: float (percentage)
        - method: str (rule, index, judgment)
        - evidence: str
        - fact_type: str (fact, assumption, judgment)
        """
        pass


class TimeAdjustmentRule(AdjustmentRule):
    """Time adjustment based on market indices or judgment."""
    
    @property
    def name(self) -> str:
        return "time_adjustment"
    
    def compute(self, subject, comparable):
        # TODO: Stage 3 — implement time adjustment logic
        # Options: index-based, manual rate, prior-report patterns
        raise NotImplementedError("Stage 3")


class LocationAdjustmentRule(AdjustmentRule):
    """Location adjustment based on district differentials."""
    
    @property
    def name(self) -> str:
        return "location_adjustment"
    
    def compute(self, subject, comparable):
        raise NotImplementedError("Stage 3")


class SizeAdjustmentRule(AdjustmentRule):
    """Size adjustment based on area differentials."""
    
    @property
    def name(self) -> str:
        return "size_adjustment"
    
    def compute(self, subject, comparable):
        raise NotImplementedError("Stage 3")


class ValuationEngine:
    """Orchestrates valuation adjustments and produces concluded values.
    
    Rules:
    - AI suggests, human approves
    - All adjustments must be logged with evidence
    - Never auto-apply without valuer approval
    """
    
    def __init__(self):
        self.rules: List[AdjustmentRule] = [
            TimeAdjustmentRule(),
            LocationAdjustmentRule(),
            SizeAdjustmentRule(),
        ]
    
    def propose_adjustments(
        self,
        subject: Dict[str, Any],
        comparables: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Propose adjustments for each comparable. Returns unapproved proposals."""
        # TODO: Stage 3 — implement
        raise NotImplementedError("Stage 3")
    
    def conclude_value(
        self,
        subject: Dict[str, Any],
        adjusted_comps: List[Dict[str, Any]],
        methodology: str = "comparison",
    ) -> Dict[str, Any]:
        """Produce a concluded value from adjusted comparables."""
        # TODO: Stage 3 — implement
        raise NotImplementedError("Stage 3")
