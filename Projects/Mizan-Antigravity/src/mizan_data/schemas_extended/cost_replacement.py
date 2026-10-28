"""
Category 11: Cost and Replacement Variables

Cost approach components including land value, construction costs, and depreciation.
"""

from typing import Optional

from pydantic import BaseModel, Field


class CostReplacement(BaseModel):
    """
    Cost and replacement value variables.
    
    Cost approach components including land value, direct and indirect costs,
    entrepreneurial profit, and depreciation analysis.
    """
    
    # Land Value
    land_value_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Estimated land value"
    )
    land_value_per_sqm_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Land value per square meter"
    )
    land_valuation_method: Optional[str] = Field(
        default=None,
        description="Method used for land valuation"
    )
    
    # Direct Hard Costs
    structure_cost_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Structural system cost"
    )
    mep_cost_sar: Optional[float] = Field(
        default=None, ge=0,
        description="MEP systems cost"
    )
    finishes_cost_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Finishes cost"
    )
    site_improvements_cost_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Site improvements cost"
    )
    total_hard_costs_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Total direct hard costs"
    )
    hard_cost_per_sqm_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Hard costs per sqm"
    )
    
    # Soft Costs
    design_fees_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Architectural and engineering fees"
    )
    permit_fees_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Permit and approval fees"
    )
    project_management_fees_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Project management fees"
    )
    legal_fees_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Legal fees"
    )
    marketing_fees_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Marketing and sales costs"
    )
    other_soft_costs_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Other soft costs"
    )
    total_soft_costs_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Total soft costs"
    )
    soft_cost_pct_of_hard: Optional[float] = Field(
        default=None, ge=0,
        description="Soft costs as % of hard costs"
    )
    
    # Financing During Construction
    idc_rate_pct: Optional[float] = Field(
        default=None, ge=0,
        description="Interest during construction rate"
    )
    idc_period_months: Optional[int] = Field(
        default=None, ge=0,
        description="Construction period for IDC calculation"
    )
    interest_during_construction_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Interest during construction"
    )
    
    # Developer Profit
    developer_overhead_pct: Optional[float] = Field(
        default=None, ge=0,
        description="Developer overhead percentage"
    )
    developer_overhead_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Developer overhead amount"
    )
    developer_profit_pct: Optional[float] = Field(
        default=None, ge=0,
        description="Developer profit percentage"
    )
    developer_profit_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Developer profit amount"
    )
    
    # Contingency
    contingency_pct: Optional[float] = Field(
        default=None, ge=0, le=50,
        description="Contingency percentage"
    )
    contingency_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Contingency amount"
    )
    
    # Escalation
    escalation_rate_pct: Optional[float] = Field(
        default=None,
        description="Cost escalation rate assumption"
    )
    escalation_allowance_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Escalation allowance"
    )
    
    # Total Replacement Cost New
    replacement_cost_new_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Replacement Cost New (RCN)"
    )
    
    # Depreciation
    physical_deterioration_pct: Optional[float] = Field(
        default=None, ge=0, le=100,
        description="Physical deterioration percentage"
    )
    physical_deterioration_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Physical deterioration amount"
    )
    functional_obsolescence_pct: Optional[float] = Field(
        default=None, ge=0, le=100,
        description="Functional obsolescence percentage"
    )
    functional_obsolescence_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Functional obsolescence amount"
    )
    external_obsolescence_pct: Optional[float] = Field(
        default=None, ge=0, le=100,
        description="External/economic obsolescence percentage"
    )
    external_obsolescence_sar: Optional[float] = Field(
        default=None, ge=0,
        description="External obsolescence amount"
    )
    total_depreciation_pct: Optional[float] = Field(
        default=None, ge=0, le=100,
        description="Total depreciation percentage"
    )
    total_depreciation_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Total depreciation amount"
    )
    
    # Depreciated Cost
    depreciated_replacement_cost_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Depreciated Replacement Cost"
    )
    
    # Entrepreneurial Incentive
    entrepreneurial_incentive_pct: Optional[float] = Field(
        default=None, ge=0,
        description="Entrepreneurial incentive percentage"
    )
    entrepreneurial_incentive_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Entrepreneurial incentive amount"
    )
    
    # Cost Approach Value
    cost_approach_value_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Indicated value by cost approach"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "land_value_sar": 5000000,
                "total_hard_costs_sar": 8000000,
                "total_soft_costs_sar": 1200000,
                "replacement_cost_new_sar": 15000000,
                "total_depreciation_pct": 15,
            }
        }
