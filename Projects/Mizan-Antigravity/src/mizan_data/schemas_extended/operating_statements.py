"""
Category 9: Operating Statements (NOI Drivers)

Income and expense line items for NOI calculation.
"""

from typing import Optional

from pydantic import BaseModel, Field


class OperatingStatements(BaseModel):
    """
    Operating statement variables (NOI drivers).
    
    Comprehensive income and expense analysis for calculating Net Operating Income.
    """
    
    # Gross Potential Income
    gross_potential_rent_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Gross Potential Rent at full occupancy"
    )
    
    # Vacancy and Loss
    vacancy_allowance_pct: Optional[float] = Field(
        default=None, ge=0, le=100,
        description="Vacancy allowance percentage"
    )
    vacancy_loss_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Vacancy loss in SAR"
    )
    credit_loss_pct: Optional[float] = Field(
        default=None, ge=0, le=100,
        description="Credit/collection loss percentage"
    )
    credit_loss_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Credit loss in SAR"
    )
    
    # Other Income
    parking_income_sar: Optional[float] = Field(default=None, ge=0)
    storage_income_sar: Optional[float] = Field(default=None, ge=0)
    signage_income_sar: Optional[float] = Field(default=None, ge=0)
    vending_income_sar: Optional[float] = Field(default=None, ge=0)
    antenna_income_sar: Optional[float] = Field(default=None, ge=0)
    service_income_sar: Optional[float] = Field(default=None, ge=0)
    late_fee_income_sar: Optional[float] = Field(default=None, ge=0)
    cam_recovery_income_sar: Optional[float] = Field(default=None, ge=0)
    utility_recovery_income_sar: Optional[float] = Field(default=None, ge=0)
    other_income_sar: Optional[float] = Field(default=None, ge=0)
    total_other_income_sar: Optional[float] = Field(default=None, ge=0)
    
    # Effective Gross Income
    effective_gross_income_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Effective Gross Income (EGI)"
    )
    
    # Operating Expenses
    # Property Management
    property_management_fee_pct: Optional[float] = Field(default=None, ge=0, le=100)
    property_management_fee_sar: Optional[float] = Field(default=None, ge=0)
    
    # Payroll
    payroll_expense_sar: Optional[float] = Field(default=None, ge=0)
    staffing_fte: Optional[float] = Field(default=None, ge=0)
    
    # Utilities
    electricity_expense_sar: Optional[float] = Field(default=None, ge=0)
    water_expense_sar: Optional[float] = Field(default=None, ge=0)
    gas_expense_sar: Optional[float] = Field(default=None, ge=0)
    district_cooling_expense_sar: Optional[float] = Field(default=None, ge=0)
    total_utilities_sar: Optional[float] = Field(default=None, ge=0)
    
    # Maintenance
    repairs_maintenance_sar: Optional[float] = Field(default=None, ge=0)
    contract_services_sar: Optional[float] = Field(default=None, ge=0)
    elevator_maintenance_sar: Optional[float] = Field(default=None, ge=0)
    hvac_maintenance_sar: Optional[float] = Field(default=None, ge=0)
    
    # Building Services
    cleaning_expense_sar: Optional[float] = Field(default=None, ge=0)
    security_expense_sar: Optional[float] = Field(default=None, ge=0)
    landscaping_expense_sar: Optional[float] = Field(default=None, ge=0)
    waste_management_sar: Optional[float] = Field(default=None, ge=0)
    pest_control_sar: Optional[float] = Field(default=None, ge=0)
    
    # Insurance and Taxes
    insurance_expense_sar: Optional[float] = Field(default=None, ge=0)
    property_tax_sar: Optional[float] = Field(default=None, ge=0)
    municipality_fees_sar: Optional[float] = Field(default=None, ge=0)
    other_taxes_levies_sar: Optional[float] = Field(default=None, ge=0)
    
    # Marketing and Leasing
    marketing_expense_sar: Optional[float] = Field(default=None, ge=0)
    leasing_expense_sar: Optional[float] = Field(default=None, ge=0)
    
    # Professional Fees
    legal_fees_sar: Optional[float] = Field(default=None, ge=0)
    audit_fees_sar: Optional[float] = Field(default=None, ge=0)
    consulting_fees_sar: Optional[float] = Field(default=None, ge=0)
    
    # Technology and Admin
    it_software_expense_sar: Optional[float] = Field(default=None, ge=0)
    bms_contracts_sar: Optional[float] = Field(default=None, ge=0)
    admin_expense_sar: Optional[float] = Field(default=None, ge=0)
    
    # Total Operating Expenses
    total_operating_expenses_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Total Operating Expenses"
    )
    
    # Net Operating Income
    net_operating_income_sar: Optional[float] = Field(
        default=None,
        description="Net Operating Income (NOI)"
    )
    
    # Expense Analysis
    opex_ratio_pct: Optional[float] = Field(
        default=None, ge=0, le=100,
        description="Operating expense ratio (Opex/EGI)"
    )
    opex_per_sqm_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Operating expenses per sqm"
    )
    opex_per_unit_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Operating expenses per unit"
    )
    opex_per_key_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Operating expenses per key (hotels)"
    )
    
    # Capex vs Opex
    capex_classification_policy: Optional[str] = Field(
        default=None,
        description="Policy for capex vs opex classification"
    )
    capitalization_threshold_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Threshold for capitalizing expenses"
    )
    
    # Benchmarking
    is_stabilized: Optional[bool] = Field(
        default=None,
        description="Whether property is stabilized"
    )
    trailing_vs_stabilized: Optional[str] = Field(
        default=None,
        description="Trailing or stabilized figures"
    )
    benchmark_opex_per_sqm_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Market benchmark opex per sqm"
    )
    opex_variance_from_benchmark_pct: Optional[float] = Field(
        default=None,
        description="Variance from market benchmark"
    )
    
    # Seasonality
    has_seasonality: Optional[bool] = Field(
        default=None,
        description="Whether income/expenses have seasonality"
    )
    peak_season_months: Optional[list[int]] = Field(
        default=None,
        description="Peak season months (1-12)"
    )
    seasonality_adjustment_pct: Optional[float] = Field(
        default=None,
        description="Seasonality adjustment percentage"
    )
    income_volatility: Optional[str] = Field(
        default=None,
        description="Income volatility level (low, moderate, high)"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "gross_potential_rent_sar": 6000000,
                "vacancy_allowance_pct": 8,
                "effective_gross_income_sar": 5800000,
                "total_operating_expenses_sar": 1500000,
                "net_operating_income_sar": 4300000,
            }
        }
