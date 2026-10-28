"""
Cost Approach.

Estimates property value based on:
Land Value + Replacement Cost New - Depreciation
"""

import logging
from typing import Optional

from .base import ApproachResult, ApproachType


logger = logging.getLogger(__name__)


class CostApproach:
    """
    Cost Approach for property valuation.
    
    Also known as Depreciated Replacement Cost (DRC).
    Best suited for:
    - New construction
    - Specialty properties
    - Limited market transactions
    """
    
    def __init__(
        self,
        default_construction_cost_per_sqm: float = 3500,
        default_soft_cost_pct: float = 0.15,
        default_depreciation_rate_per_year: float = 0.02,
    ):
        """
        Initialize cost approach with market parameters.
        
        Args:
            default_construction_cost_per_sqm: Default hard cost (SAR/sqm)
            default_soft_cost_pct: Soft costs as % of hard costs
            default_depreciation_rate_per_year: Annual depreciation rate
        """
        self.default_construction_cost = default_construction_cost_per_sqm
        self.default_soft_cost_pct = default_soft_cost_pct
        self.default_depreciation_rate = default_depreciation_rate_per_year
    
    def value(
        self,
        land_value: float,
        building_area_sqm: float,
        age_years: int = 0,
        construction_cost_per_sqm: Optional[float] = None,
        soft_cost_pct: Optional[float] = None,
        depreciation_pct: Optional[float] = None,
        functional_obsolescence_pct: float = 0,
        external_obsolescence_pct: float = 0,
        notes: Optional[str] = None,
    ) -> ApproachResult:
        """
        Estimate value using cost approach.
        
        Value = Land + RCN - Total Depreciation
        
        Args:
            land_value: Market value of land
            building_area_sqm: Gross building area
            age_years: Building age in years
            construction_cost_per_sqm: Hard construction cost (SAR/sqm)
            soft_cost_pct: Soft costs as % of hard costs
            depreciation_pct: Total physical depreciation (overrides age calc)
            functional_obsolescence_pct: Functional obsolescence %
            external_obsolescence_pct: External/economic obsolescence %
            notes: Optional notes
            
        Returns:
            ApproachResult with cost approach value
        """
        # Construction costs
        hard_cost = construction_cost_per_sqm or self.default_construction_cost
        soft_pct = soft_cost_pct or self.default_soft_cost_pct
        
        hard_costs = building_area_sqm * hard_cost
        soft_costs = hard_costs * soft_pct
        rcn = hard_costs + soft_costs  # Replacement Cost New
        
        # Depreciation
        if depreciation_pct is not None:
            physical_depreciation_pct = depreciation_pct
        else:
            # Age-life method
            physical_depreciation_pct = min(age_years * self.default_depreciation_rate, 0.80)
        
        # Total depreciation
        total_depreciation_pct = min(
            physical_depreciation_pct + functional_obsolescence_pct + external_obsolescence_pct,
            0.95  # Cap at 95% depreciation
        )
        
        depreciation_amount = rcn * total_depreciation_pct
        depreciated_value = rcn - depreciation_amount
        
        # Total value
        value = land_value + depreciated_value
        
        # Value range (±10% on construction costs)
        value_low = land_value + (depreciated_value * 0.9)
        value_high = land_value + (depreciated_value * 1.1)
        
        return ApproachResult(
            approach_type=ApproachType.COST,
            value_low=value_low,
            value_mid=value,
            value_high=value_high,
            reliability_score=70 if age_years < 10 else 60,
            data_quality_score=75,
            evidence={
                "land_value": land_value,
                "building_area_sqm": building_area_sqm,
                "hard_cost_per_sqm": hard_cost,
                "hard_costs": hard_costs,
                "soft_costs": soft_costs,
                "rcn": rcn,
                "depreciation": {
                    "physical_pct": physical_depreciation_pct * 100,
                    "functional_pct": functional_obsolescence_pct * 100,
                    "external_pct": external_obsolescence_pct * 100,
                    "total_pct": total_depreciation_pct * 100,
                    "amount": depreciation_amount,
                },
                "depreciated_building_value": depreciated_value,
            },
            notes=notes or f"Land {land_value:,.0f} + Building (DRC) {depreciated_value:,.0f}",
        )
    
    def value_from_rcn(
        self,
        land_value: float,
        rcn: float,
        total_depreciation_pct: float,
    ) -> ApproachResult:
        """
        Quick cost approach from pre-calculated RCN.
        
        Args:
            land_value: Land value
            rcn: Replacement Cost New
            total_depreciation_pct: Total depreciation percentage
            
        Returns:
            ApproachResult
        """
        depreciated = rcn * (1 - total_depreciation_pct)
        value = land_value + depreciated
        
        return ApproachResult(
            approach_type=ApproachType.COST,
            value_low=value * 0.9,
            value_mid=value,
            value_high=value * 1.1,
            reliability_score=65,
            data_quality_score=70,
            evidence={
                "land_value": land_value,
                "rcn": rcn,
                "total_depreciation_pct": total_depreciation_pct * 100,
                "depreciated_value": depreciated,
            },
            notes=f"From RCN {rcn:,.0f} less {total_depreciation_pct*100:.0f}% depreciation",
        )
