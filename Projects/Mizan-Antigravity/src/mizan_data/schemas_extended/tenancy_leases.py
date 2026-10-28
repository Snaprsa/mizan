"""
Category 8: Tenancy, Leases, and Occupancy

Rent roll, lease terms, tenant analysis, and occupancy metrics.
"""

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field

from .enums import LeaseType, EscalationType


class TenantRecord(BaseModel):
    """Individual tenant record in the rent roll."""
    
    unit_id: str = Field(..., description="Unit identifier")
    tenant_name: Optional[str] = Field(default=None, description="Tenant name")
    industry: Optional[str] = Field(default=None, description="Tenant industry/sector")
    credit_rating: Optional[str] = Field(default=None, description="Tenant credit rating")
    guarantor: Optional[str] = Field(default=None, description="Guarantor if any")
    lease_start: Optional[date] = Field(default=None, description="Lease start date")
    lease_expiry: Optional[date] = Field(default=None, description="Lease expiry date")
    remaining_term_months: Optional[int] = Field(default=None, ge=0)
    unit_size_sqm: Optional[float] = Field(default=None, ge=0)
    annual_rent_sar: Optional[float] = Field(default=None, ge=0)
    rent_per_sqm_sar: Optional[float] = Field(default=None, ge=0)
    lease_type: Optional[LeaseType] = Field(default=None)
    escalation_type: Optional[EscalationType] = Field(default=None)
    escalation_rate_pct: Optional[float] = Field(default=None)
    has_break_option: Optional[bool] = Field(default=None)
    break_option_date: Optional[date] = Field(default=None)
    has_renewal_option: Optional[bool] = Field(default=None)
    security_deposit_sar: Optional[float] = Field(default=None, ge=0)
    is_in_arrears: Optional[bool] = Field(default=None)
    arrears_amount_sar: Optional[float] = Field(default=None, ge=0)


class TenancyLeases(BaseModel):
    """
    Tenancy, leases, and occupancy variables.
    
    Comprehensive rent roll analysis including tenant details, lease terms,
    recovery structures, and market rent comparison.
    """
    
    # Occupancy Metrics
    physical_occupancy_pct: Optional[float] = Field(
        default=None, ge=0, le=100,
        description="Physical occupancy percentage"
    )
    economic_occupancy_pct: Optional[float] = Field(
        default=None, ge=0, le=100,
        description="Economic occupancy percentage"
    )
    vacant_units: Optional[int] = Field(
        default=None, ge=0,
        description="Number of vacant units"
    )
    vacant_sqm: Optional[float] = Field(
        default=None, ge=0,
        description="Vacant area in sqm"
    )
    
    # Rent Roll
    rent_roll: Optional[list[TenantRecord]] = Field(
        default=None,
        description="Complete rent roll"
    )
    total_tenants: Optional[int] = Field(
        default=None, ge=0,
        description="Total number of tenants"
    )
    
    # Lease Term Analysis
    walt_months: Optional[float] = Field(
        default=None, ge=0,
        description="Weighted Average Lease Term in months"
    )
    wale_months: Optional[float] = Field(
        default=None, ge=0,
        description="Weighted Average Lease Expiry in months"
    )
    leases_expiring_1yr: Optional[int] = Field(
        default=None, ge=0,
        description="Number of leases expiring within 1 year"
    )
    leases_expiring_1yr_sqm: Optional[float] = Field(
        default=None, ge=0,
        description="Area of leases expiring within 1 year"
    )
    leases_expiring_3yr: Optional[int] = Field(
        default=None, ge=0,
        description="Number of leases expiring within 3 years"
    )
    
    # Rent Analysis
    total_annual_rent_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Total annual contracted rent"
    )
    avg_rent_per_sqm_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Average rent per sqm"
    )
    min_rent_per_sqm_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Minimum rent per sqm"
    )
    max_rent_per_sqm_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Maximum rent per sqm"
    )
    
    # Escalation Terms
    pct_leases_with_escalation: Optional[float] = Field(
        default=None, ge=0, le=100,
        description="Percentage of leases with escalation"
    )
    avg_escalation_rate_pct: Optional[float] = Field(
        default=None,
        description="Average escalation rate"
    )
    
    # Incentives
    total_free_rent_months: Optional[float] = Field(
        default=None, ge=0,
        description="Total free rent months outstanding"
    )
    total_fitout_contribution_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Total fit-out contributions outstanding"
    )
    
    # Options
    pct_with_break_options: Optional[float] = Field(
        default=None, ge=0, le=100,
        description="Percentage of leases with break options"
    )
    pct_with_renewal_options: Optional[float] = Field(
        default=None, ge=0, le=100,
        description="Percentage of leases with renewal options"
    )
    
    # Security
    total_security_deposits_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Total security deposits held"
    )
    letters_of_credit_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Total letters of credit"
    )
    
    # Recovery Structure
    cam_recovery_basis: Optional[str] = Field(
        default=None,
        description="CAM recovery basis (pro-rata, per sqm, fixed)"
    )
    cam_recovery_pct: Optional[float] = Field(
        default=None, ge=0, le=100,
        description="Percentage of CAM recovered"
    )
    utilities_recovery_pct: Optional[float] = Field(
        default=None, ge=0, le=100,
        description="Percentage of utilities recovered"
    )
    tax_recovery_pct: Optional[float] = Field(
        default=None, ge=0, le=100,
        description="Percentage of taxes recovered"
    )
    insurance_recovery_pct: Optional[float] = Field(
        default=None, ge=0, le=100,
        description="Percentage of insurance recovered"
    )
    
    # Retail-Specific
    vacancy_co_tenancy_clauses: Optional[bool] = Field(
        default=None,
        description="Whether vacancy co-tenancy clauses exist"
    )
    co_tenancy_tenants: Optional[list[str]] = Field(
        default=None,
        description="Tenants with co-tenancy rights"
    )
    percentage_rent_tenants: Optional[int] = Field(
        default=None, ge=0,
        description="Number of tenants with percentage rent"
    )
    
    # Leasing Costs
    avg_leasing_commission_pct: Optional[float] = Field(
        default=None, ge=0,
        description="Average leasing commission as % of rent"
    )
    avg_tenant_improvement_per_sqm_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Average TI allowance per sqm"
    )
    
    # Arrears and Bad Debt
    total_arrears_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Total rent arrears"
    )
    arrears_over_90_days_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Arrears over 90 days"
    )
    delinquency_rate_pct: Optional[float] = Field(
        default=None, ge=0, le=100,
        description="Delinquency rate"
    )
    bad_debt_assumption_pct: Optional[float] = Field(
        default=None, ge=0, le=100,
        description="Bad debt assumption percentage"
    )
    
    # Concentration
    top_tenant_name: Optional[str] = Field(default=None)
    top_tenant_pct_of_rent: Optional[float] = Field(default=None, ge=0, le=100)
    top_5_tenants_pct_of_rent: Optional[float] = Field(default=None, ge=0, le=100)
    single_tenant_risk: Optional[bool] = Field(default=None)
    
    # Market Comparison
    market_rent_per_sqm_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Current market rent per sqm"
    )
    mark_to_market_pct: Optional[float] = Field(
        default=None,
        description="Mark to market percentage (+ over-rented, - under-rented)"
    )
    reversionary_potential_sar: Optional[float] = Field(
        default=None,
        description="Reversionary income potential"
    )
    
    # Leasing Velocity
    avg_leasing_time_months: Optional[float] = Field(
        default=None, ge=0,
        description="Average time to lease vacant space"
    )
    assumed_downtime_months: Optional[float] = Field(
        default=None, ge=0,
        description="Assumed downtime between tenants"
    )
    absorption_rate_sqm_per_month: Optional[float] = Field(
        default=None, ge=0,
        description="Market absorption rate"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "physical_occupancy_pct": 92,
                "economic_occupancy_pct": 88,
                "walt_months": 36,
                "total_annual_rent_sar": 5000000,
            }
        }
