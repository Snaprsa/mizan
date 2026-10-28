"""
Reconciliation Engine.

Combines multiple valuation approach results into a final value
using weighted reconciliation per IVS/TAQEEM standards.
"""

import logging
from dataclasses import dataclass
from typing import Optional

from mizan_data.schemas_extended import ValuationPurpose
from .approaches.base import ApproachResult, ApproachType


logger = logging.getLogger(__name__)


# Default reconciliation weights by property type
DEFAULT_WEIGHTS = {
    "residential": {
        ApproachType.SALES_COMPARISON: 0.70,
        ApproachType.INCOME: 0.20,
        ApproachType.COST: 0.10,
    },
    "commercial": {
        ApproachType.SALES_COMPARISON: 0.30,
        ApproachType.INCOME: 0.60,
        ApproachType.COST: 0.10,
    },
    "industrial": {
        ApproachType.SALES_COMPARISON: 0.25,
        ApproachType.INCOME: 0.50,
        ApproachType.COST: 0.25,
    },
    "development": {
        ApproachType.SALES_COMPARISON: 0.20,
        ApproachType.INCOME: 0.40,
        ApproachType.COST: 0.40,
    },
    "specialty": {
        ApproachType.SALES_COMPARISON: 0.10,
        ApproachType.INCOME: 0.10,
        ApproachType.COST: 0.80,
    },
}


@dataclass
class ReconciliationResult:
    """Result of reconciling multiple approach values."""
    
    final_value_low: float
    final_value_mid: float
    final_value_high: float
    
    confidence_score: int
    
    weights_used: dict[ApproachType, float]
    approach_results: dict[ApproachType, ApproachResult]
    
    notes: str = ""
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "final_value_low": int(self.final_value_low),
            "final_value_mid": int(self.final_value_mid),
            "final_value_high": int(self.final_value_high),
            "confidence_score": self.confidence_score,
            "weights_used": {k.value: v for k, v in self.weights_used.items()},
            "approach_results": {
                k.value: v.to_dict() for k, v in self.approach_results.items()
            },
            "notes": self.notes,
        }


class ReconciliationEngine:
    """
    Reconciles multiple valuation approach results.
    
    Follows IVS/TAQEEM standards for value reconciliation,
    weighting approaches based on:
    - Property type
    - Data quality
    - Market conditions
    - Valuation purpose
    """
    
    def __init__(self, weights: Optional[dict] = None):
        """
        Initialize reconciliation engine.
        
        Args:
            weights: Custom weights by property type, or None for defaults
        """
        self.weights = weights or DEFAULT_WEIGHTS
    
    def reconcile(
        self,
        sales_result: Optional[ApproachResult] = None,
        income_result: Optional[ApproachResult] = None,
        cost_result: Optional[ApproachResult] = None,
        property_type: str = "residential",
        purpose: Optional[ValuationPurpose] = None,
        custom_weights: Optional[dict[ApproachType, float]] = None,
    ) -> ReconciliationResult:
        """
        Reconcile approach results into final value.
        
        Args:
            sales_result: Result from sales comparison approach
            income_result: Result from income approach
            cost_result: Result from cost approach
            property_type: Property type for default weights
            purpose: Valuation purpose (may affect weighting)
            custom_weights: Override weights
            
        Returns:
            ReconciliationResult with final reconciled value
        """
        # Collect available results
        results = {}
        if sales_result:
            results[ApproachType.SALES_COMPARISON] = sales_result
        if income_result:
            results[ApproachType.INCOME] = income_result
        if cost_result:
            results[ApproachType.COST] = cost_result
        
        if not results:
            raise ValueError("At least one approach result is required")
        
        # Determine weights
        if custom_weights:
            base_weights = custom_weights
        else:
            base_weights = self.weights.get(property_type, self.weights["residential"])
        
        # Filter to available approaches and normalize
        available_weights = {
            k: v for k, v in base_weights.items() if k in results
        }
        total_weight = sum(available_weights.values())
        normalized_weights = {
            k: v / total_weight for k, v in available_weights.items()
        }
        
        # Adjust weights by reliability (quality-weighted)
        quality_adjusted = {}
        for approach, weight in normalized_weights.items():
            reliability = results[approach].reliability_score / 100
            quality_adjusted[approach] = weight * reliability
        
        # Re-normalize after quality adjustment
        total_adjusted = sum(quality_adjusted.values())
        if total_adjusted > 0:
            final_weights = {k: v / total_adjusted for k, v in quality_adjusted.items()}
        else:
            final_weights = normalized_weights
        
        # Weighted average of values
        value_low = sum(
            results[a].value_low * w for a, w in final_weights.items()
        )
        value_mid = sum(
            results[a].value_mid * w for a, w in final_weights.items()
        )
        value_high = sum(
            results[a].value_high * w for a, w in final_weights.items()
        )
        
        # Combined confidence
        confidence = int(sum(
            results[a].confidence_score * w for a, w in final_weights.items()
        ))
        
        # Build notes
        weight_strs = [
            f"{a.value}: {w*100:.0f}%" for a, w in final_weights.items()
        ]
        notes = f"Reconciled using weights: {', '.join(weight_strs)}"
        
        return ReconciliationResult(
            final_value_low=value_low,
            final_value_mid=value_mid,
            final_value_high=value_high,
            confidence_score=confidence,
            weights_used=final_weights,
            approach_results=results,
            notes=notes,
        )
    
    def reconcile_simple(
        self,
        results: list[ApproachResult],
        property_type: str = "residential",
    ) -> ReconciliationResult:
        """
        Simple reconciliation from a list of results.
        
        Args:
            results: List of ApproachResult objects
            property_type: Property type for weighting
            
        Returns:
            ReconciliationResult
        """
        sales = None
        income = None
        cost = None
        
        for r in results:
            if r.approach_type == ApproachType.SALES_COMPARISON:
                sales = r
            elif r.approach_type == ApproachType.INCOME:
                income = r
            elif r.approach_type == ApproachType.COST:
                cost = r
        
        return self.reconcile(
            sales_result=sales,
            income_result=income,
            cost_result=cost,
            property_type=property_type,
        )
