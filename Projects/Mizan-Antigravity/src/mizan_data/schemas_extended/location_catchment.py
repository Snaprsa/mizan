"""
Category 2: Location and Catchment

Location, accessibility, demographics, and market fundamentals for the property.
"""

from typing import Optional

from pydantic import BaseModel, Field


class LocationCatchment(BaseModel):
    """
    Location and catchment area variables.
    
    Comprehensive location analysis including accessibility, demographics,
    externalities, and sector-specific market fundamentals.
    """
    
    # Coordinates and Address
    latitude: Optional[float] = Field(
        default=None, ge=-90, le=90,
        description="Latitude coordinate"
    )
    longitude: Optional[float] = Field(
        default=None, ge=-180, le=180,
        description="Longitude coordinate"
    )
    neighborhood_name: Optional[str] = Field(
        default=None,
        description="Neighborhood or area name"
    )
    submarket: Optional[str] = Field(
        default=None,
        description="Real estate submarket classification"
    )
    municipality: Optional[str] = Field(
        default=None,
        description="Municipality or local authority"
    )
    
    # Accessibility
    drive_time_cbd_mins: Optional[int] = Field(
        default=None, ge=0,
        description="Drive time to CBD in minutes"
    )
    drive_time_airport_mins: Optional[int] = Field(
        default=None, ge=0,
        description="Drive time to main airport in minutes"
    )
    walk_score: Optional[int] = Field(
        default=None, ge=0, le=100,
        description="Walk score (0-100)"
    )
    transit_score: Optional[int] = Field(
        default=None, ge=0, le=100,
        description="Transit accessibility score (0-100)"
    )
    metro_station_distance_m: Optional[int] = Field(
        default=None, ge=0,
        description="Distance to nearest metro station in meters"
    )
    road_hierarchy: Optional[str] = Field(
        default=None,
        description="Road classification (highway, arterial, collector, local)"
    )
    congestion_level: Optional[str] = Field(
        default=None,
        description="Traffic congestion level (low, moderate, high)"
    )
    
    # Visibility and Frontage
    visibility_rating: Optional[int] = Field(
        default=None, ge=1, le=5,
        description="Visibility rating 1-5"
    )
    frontage_m: Optional[float] = Field(
        default=None, ge=0,
        description="Street frontage in meters"
    )
    is_corner_lot: Optional[bool] = Field(
        default=None,
        description="Whether property is on a corner lot"
    )
    has_signage_rights: Optional[bool] = Field(
        default=None,
        description="Whether signage rights are available"
    )
    
    # Surrounding Land Uses
    adjacent_uses: Optional[list[str]] = Field(
        default=None,
        description="Adjacent land uses (residential, commercial, industrial, etc.)"
    )
    proximity_schools_m: Optional[int] = Field(
        default=None, ge=0,
        description="Distance to nearest school in meters"
    )
    proximity_hospitals_m: Optional[int] = Field(
        default=None, ge=0,
        description="Distance to nearest hospital in meters"
    )
    proximity_mosques_m: Optional[int] = Field(
        default=None, ge=0,
        description="Distance to nearest mosque in meters"
    )
    proximity_shopping_m: Optional[int] = Field(
        default=None, ge=0,
        description="Distance to nearest shopping center in meters"
    )
    
    # Externalities
    noise_level: Optional[str] = Field(
        default=None,
        description="Noise level (low, moderate, high)"
    )
    light_pollution: Optional[str] = Field(
        default=None,
        description="Light pollution level"
    )
    odor_issues: Optional[bool] = Field(
        default=None,
        description="Whether there are odor externalities"
    )
    
    # Safety and Crime
    crime_rate_index: Optional[float] = Field(
        default=None, ge=0,
        description="Crime rate index for the area"
    )
    safety_rating: Optional[int] = Field(
        default=None, ge=1, le=5,
        description="Safety rating 1-5"
    )
    
    # Demographics
    population_catchment: Optional[int] = Field(
        default=None, ge=0,
        description="Population within catchment area"
    )
    population_growth_pct: Optional[float] = Field(
        default=None,
        description="Annual population growth rate (%)"
    )
    median_age: Optional[float] = Field(
        default=None, ge=0,
        description="Median age of population"
    )
    avg_household_size: Optional[float] = Field(
        default=None, ge=0,
        description="Average household size"
    )
    median_household_income_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Median household income in SAR"
    )
    education_level_pct_university: Optional[float] = Field(
        default=None, ge=0, le=100,
        description="Percentage with university education"
    )
    
    # Demand Generators
    employment_nodes: Optional[list[str]] = Field(
        default=None,
        description="Nearby major employment nodes"
    )
    universities_nearby: Optional[list[str]] = Field(
        default=None,
        description="Nearby universities"
    )
    government_hubs: Optional[list[str]] = Field(
        default=None,
        description="Nearby government facilities"
    )
    annual_tourist_visitors: Optional[int] = Field(
        default=None, ge=0,
        description="Annual tourist visitors to the area"
    )
    
    # Retail Fundamentals
    daily_footfall: Optional[int] = Field(
        default=None, ge=0,
        description="Estimated daily footfall"
    )
    competing_retail_centers: Optional[int] = Field(
        default=None, ge=0,
        description="Number of competing retail centers in catchment"
    )
    catchment_spending_power_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Estimated annual retail spending power in catchment"
    )
    
    # Residential Fundamentals
    net_migration_annual: Optional[int] = Field(
        default=None,
        description="Annual net migration to area"
    )
    household_formation_rate: Optional[float] = Field(
        default=None,
        description="Annual household formation rate (%)"
    )
    price_to_income_ratio: Optional[float] = Field(
        default=None, ge=0,
        description="Property price to income ratio"
    )
    
    # Hospitality Fundamentals
    airport_connectivity_score: Optional[int] = Field(
        default=None, ge=0, le=100,
        description="Airport connectivity score"
    )
    seasonality_factor: Optional[float] = Field(
        default=None, ge=0, le=1,
        description="Seasonality factor (0=stable, 1=highly seasonal)"
    )
    corporate_demand_pct: Optional[float] = Field(
        default=None, ge=0, le=100,
        description="Percentage of hospitality demand from corporate"
    )
    
    # Industrial Fundamentals
    port_distance_km: Optional[float] = Field(
        default=None, ge=0,
        description="Distance to nearest port in km"
    )
    last_mile_density_score: Optional[int] = Field(
        default=None, ge=0, le=100,
        description="Last-mile delivery density score"
    )
    trucking_access_rating: Optional[int] = Field(
        default=None, ge=1, le=5,
        description="Trucking access rating 1-5"
    )
    
    # Macro Linkages
    interest_rate_assumption: Optional[float] = Field(
        default=None,
        description="Interest rate assumption (%)"
    )
    inflation_assumption: Optional[float] = Field(
        default=None,
        description="Inflation assumption (%)"
    )
    gdp_growth_assumption: Optional[float] = Field(
        default=None,
        description="GDP growth assumption (%)"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "latitude": 24.7136,
                "longitude": 46.6753,
                "neighborhood_name": "Al Olaya",
                "drive_time_cbd_mins": 10,
                "walk_score": 75,
            }
        }
