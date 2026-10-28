"""
Category 10: Market Evidence and Pricing Variables

Sales and rental comparables, adjustments, and market indicators.
"""

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class SalesComparable(BaseModel):
    """Individual sales comparable record."""
    
    comp_id: Optional[str] = Field(default=None, description="Comparable ID")
    address: Optional[str] = Field(default=None, description="Property address")
    sale_date: Optional[date] = Field(default=None, description="Sale date")
    sale_price_sar: Optional[float] = Field(default=None, ge=0, description="Sale price")
    price_per_sqm_sar: Optional[float] = Field(default=None, ge=0)
    noi_at_sale_sar: Optional[float] = Field(default=None, ge=0)
    cap_rate_pct: Optional[float] = Field(default=None, ge=0)
    building_area_sqm: Optional[float] = Field(default=None, ge=0)
    land_area_sqm: Optional[float] = Field(default=None, ge=0)
    year_built: Optional[int] = Field(default=None)
    property_type: Optional[str] = Field(default=None)
    condition: Optional[str] = Field(default=None)
    occupancy_at_sale_pct: Optional[float] = Field(default=None, ge=0, le=100)
    
    # Adjustment factors
    location_adjustment_pct: Optional[float] = Field(default=None)
    size_adjustment_pct: Optional[float] = Field(default=None)
    quality_adjustment_pct: Optional[float] = Field(default=None)
    age_adjustment_pct: Optional[float] = Field(default=None)
    condition_adjustment_pct: Optional[float] = Field(default=None)
    time_adjustment_pct: Optional[float] = Field(default=None)
    tenancy_adjustment_pct: Optional[float] = Field(default=None)
    occupancy_adjustment_pct: Optional[float] = Field(default=None)
    rights_adjustment_pct: Optional[float] = Field(default=None)
    total_adjustment_pct: Optional[float] = Field(default=None)
    adjusted_price_per_sqm_sar: Optional[float] = Field(default=None, ge=0)
    
    # Sale conditions
    is_arms_length: Optional[bool] = Field(default=None)
    motivated_seller: Optional[bool] = Field(default=None)
    motivated_buyer: Optional[bool] = Field(default=None)
    is_distressed: Optional[bool] = Field(default=None)
    sale_conditions_notes: Optional[str] = Field(default=None)


class RentalComparable(BaseModel):
    """Individual rental comparable record."""
    
    comp_id: Optional[str] = Field(default=None, description="Comparable ID")
    address: Optional[str] = Field(default=None, description="Property address")
    lease_date: Optional[date] = Field(default=None, description="Lease date")
    asking_rent_per_sqm_sar: Optional[float] = Field(default=None, ge=0)
    achieved_rent_per_sqm_sar: Optional[float] = Field(default=None, ge=0)
    unit_size_sqm: Optional[float] = Field(default=None, ge=0)
    unit_type: Optional[str] = Field(default=None)
    quality_tier: Optional[int] = Field(default=None, ge=1, le=5)
    floor_level: Optional[int] = Field(default=None)
    lease_term_months: Optional[int] = Field(default=None, ge=0)
    
    # Concessions
    free_rent_months: Optional[float] = Field(default=None, ge=0)
    ti_allowance_per_sqm_sar: Optional[float] = Field(default=None, ge=0)
    effective_rent_per_sqm_sar: Optional[float] = Field(default=None, ge=0)
    
    # Adjustments
    location_adjustment_pct: Optional[float] = Field(default=None)
    quality_adjustment_pct: Optional[float] = Field(default=None)
    size_adjustment_pct: Optional[float] = Field(default=None)
    time_adjustment_pct: Optional[float] = Field(default=None)
    adjusted_rent_per_sqm_sar: Optional[float] = Field(default=None, ge=0)


class MarketEvidence(BaseModel):
    """
    Market evidence and pricing variables.
    
    Sales and rental comparables with adjustments, market indicators,
    and supply/demand analysis.
    """
    
    # Sales Comparables
    sales_comparables: Optional[list[SalesComparable]] = Field(
        default=None,
        description="List of sales comparables"
    )
    sales_comp_count: Optional[int] = Field(
        default=None, ge=0,
        description="Number of sales comparables analyzed"
    )
    avg_unadjusted_price_per_sqm_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Average unadjusted price per sqm"
    )
    avg_adjusted_price_per_sqm_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Average adjusted price per sqm"
    )
    price_per_sqm_range_low_sar: Optional[float] = Field(default=None, ge=0)
    price_per_sqm_range_high_sar: Optional[float] = Field(default=None, ge=0)
    
    # Cap Rate Evidence
    market_cap_rate_low_pct: Optional[float] = Field(default=None, ge=0)
    market_cap_rate_high_pct: Optional[float] = Field(default=None, ge=0)
    market_cap_rate_mid_pct: Optional[float] = Field(default=None, ge=0)
    selected_cap_rate_pct: Optional[float] = Field(default=None, ge=0)
    cap_rate_justification: Optional[str] = Field(default=None)
    
    # Rental Comparables
    rental_comparables: Optional[list[RentalComparable]] = Field(
        default=None,
        description="List of rental comparables"
    )
    rental_comp_count: Optional[int] = Field(
        default=None, ge=0,
        description="Number of rental comparables analyzed"
    )
    avg_market_rent_per_sqm_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Average market rent per sqm"
    )
    market_rent_range_low_sar: Optional[float] = Field(default=None, ge=0)
    market_rent_range_high_sar: Optional[float] = Field(default=None, ge=0)
    
    # Concession Analysis
    market_free_rent_months: Optional[float] = Field(
        default=None, ge=0,
        description="Market standard free rent months"
    )
    market_ti_per_sqm_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Market standard TI allowance"
    )
    
    # Market Indicators
    submarket_vacancy_rate_pct: Optional[float] = Field(default=None, ge=0, le=100)
    submarket_absorption_sqm: Optional[float] = Field(default=None)
    submarket_inventory_sqm: Optional[float] = Field(default=None, ge=0)
    
    # Supply Pipeline
    new_supply_pipeline_sqm: Optional[float] = Field(
        default=None, ge=0,
        description="New supply in pipeline (sqm)"
    )
    completions_next_year_sqm: Optional[float] = Field(default=None, ge=0)
    completions_next_3yr_sqm: Optional[float] = Field(default=None, ge=0)
    competing_projects: Optional[list[str]] = Field(default=None)
    
    # Demand Indicators
    demand_growth_pct: Optional[float] = Field(default=None)
    demand_drivers: Optional[list[str]] = Field(default=None)
    demand_risk_factors: Optional[list[str]] = Field(default=None)
    
    # Market Trend
    price_trend_1yr_pct: Optional[float] = Field(default=None)
    price_trend_3yr_pct: Optional[float] = Field(default=None)
    rent_trend_1yr_pct: Optional[float] = Field(default=None)
    rent_trend_3yr_pct: Optional[float] = Field(default=None)
    market_cycle_phase: Optional[str] = Field(
        default=None,
        description="Market cycle phase (recovery, expansion, hypersupply, recession)"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "sales_comp_count": 5,
                "avg_adjusted_price_per_sqm_sar": 12500,
                "market_cap_rate_mid_pct": 7.5,
                "avg_market_rent_per_sqm_sar": 1200,
            }
        }
