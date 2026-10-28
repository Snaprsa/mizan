"""
Category 13: Income Approach and DCF Variables

DCF projections, discount rates, terminal value, and sensitivities.
"""

from typing import Optional

from pydantic import BaseModel, Field

from .enums import TerminalValueMethod


class IncomeDCF(BaseModel):
    """
    Income approach and DCF variables.
    
    Discounted cash flow analysis including projections, discount rate
    build-up, terminal value, and sensitivity analysis.
    """
    
    # Projection Period
    projection_horizon_years: Optional[int] = Field(
        default=None, ge=1, le=20,
        description="DCF projection horizon in years"
    )
    projection_start_date: Optional[str] = Field(
        default=None,
        description="Start date of projection"
    )
    fiscal_year_end: Optional[str] = Field(
        default=None,
        description="Fiscal year end month"
    )
    
    # Revenue Assumptions
    rent_growth_year1_pct: Optional[float] = Field(default=None)
    rent_growth_year2_pct: Optional[float] = Field(default=None)
    rent_growth_year3_plus_pct: Optional[float] = Field(default=None)
    rent_growth_by_segment: Optional[dict] = Field(
        default=None,
        description="Rent growth by property segment"
    )
    
    # Leasing Assumptions
    renewal_probability_pct: Optional[float] = Field(
        default=None, ge=0, le=100,
        description="Tenant renewal probability"
    )
    releasing_spread_pct: Optional[float] = Field(
        default=None,
        description="Spread to market on renewals (%)"
    )
    downtime_months: Optional[float] = Field(
        default=None, ge=0,
        description="Average downtime between tenants"
    )
    tenant_improvement_per_sqm_new_sar: Optional[float] = Field(
        default=None, ge=0,
        description="TI allowance for new tenants"
    )
    tenant_improvement_per_sqm_renewal_sar: Optional[float] = Field(
        default=None, ge=0,
        description="TI allowance for renewals"
    )
    leasing_commission_new_pct: Optional[float] = Field(
        default=None, ge=0,
        description="Leasing commission for new leases"
    )
    leasing_commission_renewal_pct: Optional[float] = Field(
        default=None, ge=0,
        description="Leasing commission for renewals"
    )
    
    # Expense Assumptions
    opex_inflation_pct: Optional[float] = Field(
        default=None,
        description="Annual opex inflation rate"
    )
    management_fee_pct: Optional[float] = Field(
        default=None, ge=0,
        description="Property management fee as % of EGI"
    )
    
    # Capital Expenditure
    capex_reserve_per_sqm_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Annual capex reserve per sqm"
    )
    capex_schedule: Optional[list[float]] = Field(
        default=None,
        description="Capex by year in projection"
    )
    major_capex_items: Optional[list[dict]] = Field(
        default=None,
        description="Major capex items with year and amount"
    )
    
    # Terminal Value
    terminal_value_method: Optional[TerminalValueMethod] = Field(
        default=None,
        description="Method for terminal value"
    )
    exit_cap_rate_pct: Optional[float] = Field(
        default=None, ge=0,
        description="Exit/terminal cap rate"
    )
    terminal_year_noi_sar: Optional[float] = Field(
        default=None, ge=0,
        description="NOI used for terminal value"
    )
    terminal_noi_basis: Optional[str] = Field(
        default=None,
        description="Terminal NOI basis (year 11 forward NOI, stabilized)"
    )
    terminal_growth_rate_pct: Optional[float] = Field(
        default=None,
        description="Terminal growth rate for Gordon model"
    )
    selling_costs_pct: Optional[float] = Field(
        default=None, ge=0,
        description="Selling costs at exit"
    )
    terminal_value_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Calculated terminal value"
    )
    
    # Discount Rate
    discount_rate_pct: Optional[float] = Field(
        default=None, ge=0,
        description="Overall discount rate"
    )
    
    # Discount Rate Build-up
    risk_free_rate_pct: Optional[float] = Field(
        default=None, ge=0,
        description="Risk-free rate"
    )
    market_risk_premium_pct: Optional[float] = Field(
        default=None, ge=0,
        description="Market/equity risk premium"
    )
    property_risk_premium_pct: Optional[float] = Field(
        default=None, ge=0,
        description="Property-specific risk premium"
    )
    size_premium_pct: Optional[float] = Field(
        default=None, ge=0,
        description="Size/liquidity premium"
    )
    illiquidity_premium_pct: Optional[float] = Field(
        default=None, ge=0,
        description="Illiquidity premium"
    )
    country_risk_premium_pct: Optional[float] = Field(
        default=None, ge=0,
        description="Country risk premium"
    )
    discount_rate_justification: Optional[str] = Field(
        default=None,
        description="Justification for discount rate"
    )
    
    # Leverage Impact
    leverage_adjusted: Optional[bool] = Field(
        default=None,
        description="Whether rate is levered"
    )
    ltv_assumed_pct: Optional[float] = Field(
        default=None, ge=0, le=100,
        description="LTV for leverage adjustment"
    )
    
    # Stabilization
    is_stabilized: Optional[bool] = Field(
        default=None,
        description="Whether property is stabilized"
    )
    stabilization_period_months: Optional[int] = Field(
        default=None, ge=0,
        description="Months to stabilization"
    )
    stabilized_occupancy_pct: Optional[float] = Field(
        default=None, ge=0, le=100,
        description="Stabilized occupancy assumption"
    )
    lease_up_pace: Optional[str] = Field(
        default=None,
        description="Lease-up pace assumption"
    )
    
    # DCF Outputs
    pv_of_cash_flows_sar: Optional[float] = Field(
        default=None, ge=0,
        description="PV of projected cash flows"
    )
    pv_of_terminal_value_sar: Optional[float] = Field(
        default=None, ge=0,
        description="PV of terminal value"
    )
    dcf_value_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Total DCF value"
    )
    implied_going_in_cap_rate_pct: Optional[float] = Field(
        default=None, ge=0,
        description="Implied going-in cap rate"
    )
    
    # Sensitivities
    sensitivity_cap_rate_range: Optional[list[float]] = Field(
        default=None,
        description="Cap rate sensitivity range"
    )
    sensitivity_rent_growth_range: Optional[list[float]] = Field(
        default=None,
        description="Rent growth sensitivity range"
    )
    sensitivity_vacancy_range: Optional[list[float]] = Field(
        default=None,
        description="Vacancy sensitivity range"
    )
    sensitivity_opex_range: Optional[list[float]] = Field(
        default=None,
        description="Opex inflation sensitivity range"
    )
    sensitivity_discount_rate_range: Optional[list[float]] = Field(
        default=None,
        description="Discount rate sensitivity range"
    )
    sensitivity_results: Optional[dict] = Field(
        default=None,
        description="Sensitivity analysis results matrix"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "projection_horizon_years": 10,
                "discount_rate_pct": 9.5,
                "exit_cap_rate_pct": 7.5,
                "dcf_value_sar": 25000000,
            }
        }
