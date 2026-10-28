"""
Sales Comparison Approach.

Estimates property value by comparing to recent sales of similar properties
with adjustments for differences.
"""

import logging
from typing import Optional

from mizan_data.schemas import SubjectProperty
from mizan_models.predictor import MizanPredictor, ValuationResult

from .base import ApproachResult, ApproachType


logger = logging.getLogger(__name__)


class SalesComparisonApproach:
    """
    Sales Comparison Approach for property valuation.
    
    Uses ML-based prediction with comparable sales analysis to estimate
    market value based on recent transactions of similar properties.
    """
    
    def __init__(self, predictor: MizanPredictor):
        """
        Initialize with trained predictor.
        
        Args:
            predictor: Trained MizanPredictor with model and anchor bands
        """
        self.predictor = predictor
    
    def value(self, subject: SubjectProperty) -> ApproachResult:
        """
        Estimate value using sales comparison approach.
        
        Args:
            subject: Property to value
            
        Returns:
            ApproachResult with value indication and evidence
        """
        # Use existing predictor for ML-based valuation
        results = self.predictor.predict([subject])
        result = results[0]
        
        # Convert to ApproachResult format
        return ApproachResult(
            approach_type=ApproachType.SALES_COMPARISON,
            value_low=result.estimated_value_sar_low,
            value_mid=result.estimated_value_sar_mid,
            value_high=result.estimated_value_sar_high,
            reliability_score=result.confidence_score,
            data_quality_score=result.data_completeness_score,
            evidence={
                "segment": result.explanation.get("segment", {}),
                "comparables_count": result.explanation.get("segment", {}).get("count", 0),
                "fallback_level": result.explanation.get("segment", {}).get("level", "unknown"),
                "price_per_sqm": {
                    "low": int(result.estimated_price_per_sqm_low),
                    "mid": int(result.estimated_price_per_sqm_mid),
                    "high": int(result.estimated_price_per_sqm_high),
                },
                "top_drivers": result.explanation.get("top_drivers", []),
                "imputed_fields": result.explanation.get("imputed_fields", []),
            },
            notes=f"Based on {result.explanation.get('segment', {}).get('count', 0)} comparable sales",
        )
    
    def value_with_adjustments(
        self,
        subject: SubjectProperty,
        adjustments: Optional[dict] = None,
    ) -> ApproachResult:
        """
        Estimate value with manual adjustments.
        
        Args:
            subject: Property to value
            adjustments: Dict of adjustment factors (e.g., {"location": 0.05, "condition": -0.03})
            
        Returns:
            ApproachResult with adjusted value
        """
        base_result = self.value(subject)
        
        if not adjustments:
            return base_result
        
        # Calculate total adjustment factor
        total_adjustment = sum(adjustments.values())
        adjustment_multiplier = 1 + total_adjustment
        
        # Apply adjustments
        return ApproachResult(
            approach_type=ApproachType.SALES_COMPARISON,
            value_low=base_result.value_low * adjustment_multiplier,
            value_mid=base_result.value_mid * adjustment_multiplier,
            value_high=base_result.value_high * adjustment_multiplier,
            reliability_score=base_result.reliability_score,
            data_quality_score=base_result.data_quality_score,
            evidence={
                **base_result.evidence,
                "adjustments": adjustments,
                "total_adjustment_pct": total_adjustment * 100,
            },
            notes=f"Adjusted by {total_adjustment*100:+.1f}%",
        )
