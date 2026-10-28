"""
Category 12: Development and Residual Land Value

Development feasibility, highest and best use, and residual land valuation.
"""

from typing import Optional

from pydantic import BaseModel, Field


class DevelopmentResidual(BaseModel):
    """
    Development and residual land value variables.
    
    Development feasibility analysis including HBU, buildable area,
    development costs, and residual land value calculation.
    """
    
    # Highest and Best Use
    hbu_as_vacant: Optional[str] = Field(
        default=None,
        description="Highest and best use as if vacant"
    )
    hbu_as_improved: Optional[str] = Field(
        default=None,
        description="Highest and best use as improved"
    )
    hbu_options_considered: Optional[list[str]] = Field(
        default=None,
        description="HBU options considered"
    )
    selected_hbu: Optional[str] = Field(
        default=None,
        description="Selected highest and best use"
    )
    hbu_justification: Optional[str] = Field(
        default=None,
        description="Justification for HBU selection"
    )
    
    # Buildable Area
    gross_development_area_sqm: Optional[float] = Field(
        default=None, ge=0,
        description="Gross development area under code"
    )
    efficiency_ratio: Optional[float] = Field(
        default=None, ge=0, le=1,
        description="Building efficiency ratio"
    )
    net_sellable_area_sqm: Optional[float] = Field(
        default=None, ge=0,
        description="Net sellable/leasable area"
    )
    
    # Unit Mix
    unit_mix: Optional[dict] = Field(
        default=None,
        description="Unit mix by type {type: count}"
    )
    unit_sizes: Optional[dict] = Field(
        default=None,
        description="Average unit sizes by type"
    )
    total_units: Optional[int] = Field(
        default=None, ge=0,
        description="Total number of units"
    )
    
    # Pricing
    avg_price_per_sqm_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Average anticipated price per sqm"
    )
    price_by_unit_type: Optional[dict] = Field(
        default=None,
        description="Pricing by unit type"
    )
    gross_development_value_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Gross Development Value (GDV)"
    )
    
    # Sales Assumptions
    sales_velocity_units_per_month: Optional[float] = Field(
        default=None, ge=0,
        description="Sales velocity (units per month)"
    )
    absorption_period_months: Optional[int] = Field(
        default=None, ge=0,
        description="Total absorption period"
    )
    presales_pct: Optional[float] = Field(
        default=None, ge=0, le=100,
        description="Presales percentage assumed"
    )
    
    # Construction Schedule
    construction_start_date: Optional[str] = Field(
        default=None,
        description="Planned construction start"
    )
    construction_period_months: Optional[int] = Field(
        default=None, ge=0,
        description="Construction period in months"
    )
    total_development_period_months: Optional[int] = Field(
        default=None, ge=0,
        description="Total development period"
    )
    development_phases: Optional[int] = Field(
        default=None, ge=1,
        description="Number of development phases"
    )
    phase_details: Optional[list[str]] = Field(
        default=None,
        description="Details of each phase"
    )
    
    # Construction Costs
    hard_construction_cost_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Hard construction costs"
    )
    hard_cost_per_sqm_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Hard costs per sqm GDA"
    )
    soft_costs_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Soft costs"
    )
    cost_escalation_assumption_pct: Optional[float] = Field(
        default=None,
        description="Annual cost escalation"
    )
    total_development_cost_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Total development cost"
    )
    
    # Marketing and Sales
    marketing_cost_pct: Optional[float] = Field(
        default=None, ge=0,
        description="Marketing as % of GDV"
    )
    marketing_cost_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Marketing costs"
    )
    sales_commission_pct: Optional[float] = Field(
        default=None, ge=0,
        description="Sales commission percentage"
    )
    sales_commission_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Sales commission amount"
    )
    
    # Financing
    construction_loan_ltc_pct: Optional[float] = Field(
        default=None, ge=0, le=100,
        description="Construction loan LTC"
    )
    construction_loan_rate_pct: Optional[float] = Field(
        default=None, ge=0,
        description="Construction loan interest rate"
    )
    interest_reserve_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Interest reserve"
    )
    draw_schedule: Optional[list[float]] = Field(
        default=None,
        description="Monthly draw schedule percentages"
    )
    
    # Contingency and Risk
    contingency_pct: Optional[float] = Field(
        default=None, ge=0,
        description="Development contingency"
    )
    contingency_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Contingency amount"
    )
    cost_overrun_probability_pct: Optional[float] = Field(
        default=None, ge=0, le=100,
        description="Probability of cost overrun"
    )
    
    # Permitting
    permit_status: Optional[str] = Field(
        default=None,
        description="Current permit status"
    )
    permit_timeline_months: Optional[int] = Field(
        default=None, ge=0,
        description="Expected time to permit"
    )
    permit_probability_pct: Optional[float] = Field(
        default=None, ge=0, le=100,
        description="Probability of permit approval"
    )
    
    # Exit Strategy
    exit_strategy: Optional[str] = Field(
        default=None,
        description="Exit strategy (sell units, hold, refinance)"
    )
    exit_cap_rate_pct: Optional[float] = Field(
        default=None, ge=0,
        description="Exit cap rate if holding"
    )
    terminal_value_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Terminal value at exit"
    )
    
    # Returns
    target_irr_pct: Optional[float] = Field(
        default=None,
        description="Target IRR"
    )
    target_profit_margin_pct: Optional[float] = Field(
        default=None,
        description="Target profit margin on cost"
    )
    target_equity_multiple: Optional[float] = Field(
        default=None, ge=0,
        description="Target equity multiple"
    )
    hurdle_rate_pct: Optional[float] = Field(
        default=None,
        description="Investment hurdle rate"
    )
    
    # Residual Land Value
    total_costs_excl_land_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Total costs excluding land"
    )
    required_developer_return_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Required developer profit"
    )
    residual_land_value_sar: Optional[float] = Field(
        default=None,
        description="Residual land value (GDV - costs - profit)"
    )
    residual_land_value_per_sqm_sar: Optional[float] = Field(
        default=None,
        description="Residual land value per sqm of land"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "selected_hbu": "Mixed-use residential/retail",
                "gross_development_value_sar": 50000000,
                "total_development_cost_sar": 35000000,
                "target_irr_pct": 18,
                "residual_land_value_sar": 8000000,
            }
        }
