"""
Base classes and data structures for valuation approaches.
"""

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional


class ApproachType(str, Enum):
    """Type of valuation approach."""
    SALES_COMPARISON = "sales_comparison"
    INCOME = "income"
    COST = "cost"


@dataclass
class ApproachResult:
    """
    Result from a single valuation approach.
    
    Each approach produces a value indication with supporting evidence
    and quality metrics for reconciliation weighting.
    """
    
    # Approach identification
    approach_type: ApproachType
    
    # Value indication
    value_low: float
    value_mid: float
    value_high: float
    
    # Quality metrics (0-100)
    reliability_score: int = 75
    data_quality_score: int = 75
    
    # Supporting evidence
    evidence: dict = field(default_factory=dict)
    
    # Metadata
    effective_date: Optional[date] = None
    notes: Optional[str] = None
    
    @property
    def value_range(self) -> tuple[float, float]:
        """Return (low, high) value range."""
        return (self.value_low, self.value_high)
    
    @property
    def confidence_score(self) -> int:
        """Combined confidence based on reliability and data quality."""
        return int((self.reliability_score + self.data_quality_score) / 2)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON export."""
        return {
            "approach_type": self.approach_type.value,
            "value_low": int(self.value_low),
            "value_mid": int(self.value_mid),
            "value_high": int(self.value_high),
            "reliability_score": self.reliability_score,
            "data_quality_score": self.data_quality_score,
            "confidence_score": self.confidence_score,
            "evidence": self.evidence,
            "notes": self.notes,
        }
