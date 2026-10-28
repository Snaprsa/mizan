"""
Category 6: Physical Condition and Capex

Deferred maintenance, capital expenditure planning, and obsolescence.
"""

from typing import Optional

from pydantic import BaseModel, Field

from .enums import ConditionRating, ObsolescenceType


class CapexItem(BaseModel):
    """Individual capital expenditure item."""
    system: str = Field(..., description="Building system (roof, HVAC, elevator, etc.)")
    description: Optional[str] = Field(default=None, description="Description of work")
    estimated_cost_sar: float = Field(..., ge=0, description="Estimated cost in SAR")
    priority: Optional[str] = Field(default=None, description="Priority (immediate, short-term, long-term)")
    year_due: Optional[int] = Field(default=None, description="Year work is expected to be needed")


class PhysicalCondition(BaseModel):
    """
    Physical condition and capex variables.
    
    Detailed condition assessment including deferred maintenance,
    capital planning, replacement reserves, and obsolescence analysis.
    """
    
    # Overall Condition
    overall_condition: Optional[ConditionRating] = Field(
        default=None,
        description="Overall property condition rating"
    )
    condition_score: Optional[int] = Field(
        default=None, ge=0, le=100,
        description="Condition score 0-100"
    )
    
    # Deferred Maintenance
    deferred_maintenance_items: Optional[list[str]] = Field(
        default=None,
        description="List of deferred maintenance items"
    )
    deferred_maintenance_cost_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Total estimated deferred maintenance cost"
    )
    
    # Immediate Repairs
    immediate_repairs_required: Optional[bool] = Field(
        default=None,
        description="Whether immediate repairs are required"
    )
    immediate_repair_items: Optional[list[str]] = Field(
        default=None,
        description="List of immediate repair items"
    )
    immediate_repair_cost_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Cost of immediate repairs"
    )
    
    # Capital Plan by System
    capex_items: Optional[list[CapexItem]] = Field(
        default=None,
        description="List of capital expenditure items"
    )
    total_capex_5yr_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Total capex expected over 5 years"
    )
    total_capex_10yr_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Total capex expected over 10 years"
    )
    
    # Component Condition Ratings
    roof_condition: Optional[ConditionRating] = Field(default=None)
    roof_remaining_life_years: Optional[int] = Field(default=None, ge=0)
    facade_condition: Optional[ConditionRating] = Field(default=None)
    hvac_condition: Optional[ConditionRating] = Field(default=None)
    hvac_remaining_life_years: Optional[int] = Field(default=None, ge=0)
    elevator_condition: Optional[ConditionRating] = Field(default=None)
    elevator_remaining_life_years: Optional[int] = Field(default=None, ge=0)
    plumbing_condition: Optional[ConditionRating] = Field(default=None)
    electrical_condition: Optional[ConditionRating] = Field(default=None)
    waterproofing_condition: Optional[ConditionRating] = Field(default=None)
    parking_structure_condition: Optional[ConditionRating] = Field(default=None)
    
    # Replacement Reserves
    replacement_reserve_per_sqm_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Recommended replacement reserve per sqm per year"
    )
    replacement_reserve_per_unit_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Recommended replacement reserve per unit per year"
    )
    replacement_reserve_per_key_sar: Optional[float] = Field(
        default=None, ge=0,
        description="For hotels: reserve per key per year"
    )
    current_reserve_balance_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Current replacement reserve balance"
    )
    reserve_adequacy: Optional[str] = Field(
        default=None,
        description="Reserve adequacy (adequate, underfunded, overfunded)"
    )
    
    # Obsolescence
    functional_obsolescence: Optional[bool] = Field(
        default=None,
        description="Whether functional obsolescence exists"
    )
    functional_obsolescence_items: Optional[list[str]] = Field(
        default=None,
        description="Items causing functional obsolescence"
    )
    functional_obsolescence_cost_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Cost to cure functional obsolescence"
    )
    technical_obsolescence: Optional[bool] = Field(
        default=None,
        description="Whether technical obsolescence exists"
    )
    technical_obsolescence_items: Optional[list[str]] = Field(
        default=None,
        description="Items causing technical obsolescence"
    )
    external_obsolescence: Optional[bool] = Field(
        default=None,
        description="Whether external obsolescence exists"
    )
    external_obsolescence_factors: Optional[list[str]] = Field(
        default=None,
        description="Factors causing external obsolescence"
    )
    total_obsolescence_adjustment_pct: Optional[float] = Field(
        default=None, ge=0, le=100,
        description="Total obsolescence adjustment percentage"
    )
    
    # Cost Assumptions
    contractor_pricing_date: Optional[str] = Field(
        default=None,
        description="Date of contractor pricing"
    )
    escalation_assumption_pct: Optional[float] = Field(
        default=None,
        description="Annual escalation assumption for costs"
    )
    contingency_pct: Optional[float] = Field(
        default=None, ge=0, le=100,
        description="Contingency percentage applied"
    )
    
    # Warranty and Claims
    warranty_status: Optional[str] = Field(
        default=None,
        description="Current warranty status"
    )
    warranty_expiry_date: Optional[str] = Field(
        default=None,
        description="Warranty expiry date"
    )
    active_defect_claims: Optional[bool] = Field(
        default=None,
        description="Whether there are active defect claims"
    )
    defect_claim_details: Optional[str] = Field(
        default=None,
        description="Details of any defect claims"
    )
    defect_liability_period_end: Optional[str] = Field(
        default=None,
        description="End of defect liability period"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "overall_condition": "good",
                "condition_score": 78,
                "deferred_maintenance_cost_sar": 250000,
                "total_capex_5yr_sar": 500000,
            }
        }
