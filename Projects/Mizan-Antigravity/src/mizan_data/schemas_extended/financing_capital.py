"""
Category 14: Financing and Capital Structure

Loan terms, covenants, equity structure, and cost of capital.
"""

from typing import Optional

from pydantic import BaseModel, Field


class FinancingCapital(BaseModel):
    """
    Financing and capital structure variables.
    
    Debt and equity structure for property underwriting including
    loan terms, covenants, and return requirements.
    """
    
    # Loan Terms
    loan_amount_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Loan amount"
    )
    loan_to_cost_pct: Optional[float] = Field(
        default=None, ge=0, le=100,
        description="Loan to Cost ratio"
    )
    loan_to_value_pct: Optional[float] = Field(
        default=None, ge=0, le=100,
        description="Loan to Value ratio"
    )
    
    # Interest Rate
    interest_rate_type: Optional[str] = Field(
        default=None,
        description="Fixed or floating rate"
    )
    base_rate: Optional[str] = Field(
        default=None,
        description="Base rate reference (SAIBOR, etc.)"
    )
    base_rate_value_pct: Optional[float] = Field(
        default=None, ge=0,
        description="Current base rate value"
    )
    spread_bps: Optional[int] = Field(
        default=None, ge=0,
        description="Spread over base rate in basis points"
    )
    all_in_rate_pct: Optional[float] = Field(
        default=None, ge=0,
        description="All-in interest rate"
    )
    
    # Loan Structure
    amortization_years: Optional[int] = Field(
        default=None, ge=0,
        description="Amortization period in years"
    )
    interest_only_period_months: Optional[int] = Field(
        default=None, ge=0,
        description="Interest-only period in months"
    )
    loan_tenor_years: Optional[int] = Field(
        default=None, ge=0,
        description="Loan tenor in years"
    )
    maturity_date: Optional[str] = Field(
        default=None,
        description="Loan maturity date"
    )
    extension_options: Optional[int] = Field(
        default=None, ge=0,
        description="Number of extension options"
    )
    extension_term_months: Optional[int] = Field(
        default=None, ge=0,
        description="Extension term per option"
    )
    
    # Fees
    arrangement_fee_pct: Optional[float] = Field(
        default=None, ge=0,
        description="Arrangement fee percentage"
    )
    arrangement_fee_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Arrangement fee amount"
    )
    commitment_fee_pct: Optional[float] = Field(
        default=None, ge=0,
        description="Commitment fee on undrawn"
    )
    legal_fees_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Financing legal fees"
    )
    valuation_fees_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Valuation fees"
    )
    total_closing_costs_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Total loan closing costs"
    )
    
    # Covenants
    dscr_covenant: Optional[float] = Field(
        default=None, ge=0,
        description="Debt Service Coverage Ratio covenant"
    )
    current_dscr: Optional[float] = Field(
        default=None, ge=0,
        description="Current DSCR"
    )
    icr_covenant: Optional[float] = Field(
        default=None, ge=0,
        description="Interest Coverage Ratio covenant"
    )
    current_icr: Optional[float] = Field(
        default=None, ge=0,
        description="Current ICR"
    )
    ltv_covenant_pct: Optional[float] = Field(
        default=None, ge=0, le=100,
        description="LTV covenant"
    )
    other_covenants: Optional[list[str]] = Field(
        default=None,
        description="Other financial covenants"
    )
    covenant_compliance_status: Optional[str] = Field(
        default=None,
        description="Current covenant compliance status"
    )
    
    # Reserves
    capex_reserve_required_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Required capex reserve"
    )
    debt_service_reserve_months: Optional[int] = Field(
        default=None, ge=0,
        description="Debt service reserve requirement"
    )
    debt_service_reserve_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Debt service reserve amount"
    )
    tax_escrow_required: Optional[bool] = Field(
        default=None,
        description="Whether tax escrow is required"
    )
    insurance_escrow_required: Optional[bool] = Field(
        default=None,
        description="Whether insurance escrow is required"
    )
    
    # Hedging
    has_interest_rate_hedge: Optional[bool] = Field(
        default=None,
        description="Whether interest rate is hedged"
    )
    hedge_type: Optional[str] = Field(
        default=None,
        description="Type of hedge (swap, cap, collar)"
    )
    hedge_strike_rate_pct: Optional[float] = Field(
        default=None, ge=0,
        description="Hedge strike rate"
    )
    hedge_expiry: Optional[str] = Field(
        default=None,
        description="Hedge expiry date"
    )
    hedge_notional_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Hedge notional amount"
    )
    
    # Refinance Risk
    refinance_risk_level: Optional[str] = Field(
        default=None,
        description="Refinance risk (low, moderate, high)"
    )
    refinance_assumptions: Optional[str] = Field(
        default=None,
        description="Refinancing assumptions"
    )
    
    # Equity Structure
    total_equity_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Total equity investment"
    )
    sponsor_equity_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Sponsor/GP equity"
    )
    lp_equity_sar: Optional[float] = Field(
        default=None, ge=0,
        description="LP equity"
    )
    preferred_equity_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Preferred equity"
    )
    preferred_return_pct: Optional[float] = Field(
        default=None, ge=0,
        description="Preferred return rate"
    )
    mezzanine_debt_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Mezzanine debt"
    )
    mezzanine_rate_pct: Optional[float] = Field(
        default=None, ge=0,
        description="Mezzanine interest rate"
    )
    
    # Promote/Waterfall
    promote_structure: Optional[str] = Field(
        default=None,
        description="Promote/carried interest structure"
    )
    promote_hurdle_1_irr_pct: Optional[float] = Field(
        default=None,
        description="First promote hurdle IRR"
    )
    promote_hurdle_1_split: Optional[str] = Field(
        default=None,
        description="Split at first hurdle"
    )
    promote_hurdle_2_irr_pct: Optional[float] = Field(
        default=None,
        description="Second promote hurdle IRR"
    )
    promote_hurdle_2_split: Optional[str] = Field(
        default=None,
        description="Split at second hurdle"
    )
    
    # Return Requirements
    target_levered_irr_pct: Optional[float] = Field(
        default=None,
        description="Target levered IRR"
    )
    target_equity_multiple: Optional[float] = Field(
        default=None, ge=0,
        description="Target equity multiple"
    )
    cost_of_equity_pct: Optional[float] = Field(
        default=None, ge=0,
        description="Cost of equity"
    )
    wacc_pct: Optional[float] = Field(
        default=None, ge=0,
        description="Weighted average cost of capital"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "loan_amount_sar": 15000000,
                "loan_to_value_pct": 60,
                "all_in_rate_pct": 6.5,
                "dscr_covenant": 1.25,
                "target_levered_irr_pct": 15,
            }
        }
