"""
Category 17: ESG and Sustainability Variables

Energy, carbon, certifications, and sustainability metrics.
"""

from typing import Optional

from pydantic import BaseModel, Field

from .enums import CertificationType


class ESGSustainability(BaseModel):
    """
    ESG and sustainability variables.
    
    Environmental performance, green certifications, and climate-related
    metrics increasingly factored into property valuation.
    """
    
    # Energy Performance
    energy_intensity_kwh_per_sqm: Optional[float] = Field(
        default=None, ge=0,
        description="Annual energy intensity"
    )
    energy_benchmark_percentile: Optional[int] = Field(
        default=None, ge=0, le=100,
        description="Energy benchmark percentile vs peers"
    )
    energy_rating: Optional[str] = Field(
        default=None,
        description="Energy performance rating"
    )
    energy_rating_score: Optional[int] = Field(
        default=None, ge=0, le=100,
        description="Energy rating score"
    )
    electricity_source_renewable_pct: Optional[float] = Field(
        default=None, ge=0, le=100,
        description="Percentage from renewable sources"
    )
    
    # Water
    water_intensity_liters_per_sqm: Optional[float] = Field(
        default=None, ge=0,
        description="Annual water consumption per sqm"
    )
    water_recycling_pct: Optional[float] = Field(
        default=None, ge=0, le=100,
        description="Percentage of water recycled"
    )
    rainwater_harvesting: Optional[bool] = Field(default=None)
    greywater_reuse: Optional[bool] = Field(default=None)
    
    # Carbon
    carbon_footprint_kg_co2_per_sqm: Optional[float] = Field(
        default=None, ge=0,
        description="Annual carbon footprint per sqm"
    )
    scope_1_emissions_tonnes: Optional[float] = Field(
        default=None, ge=0,
        description="Direct emissions (Scope 1)"
    )
    scope_2_emissions_tonnes: Optional[float] = Field(
        default=None, ge=0,
        description="Indirect energy emissions (Scope 2)"
    )
    scope_3_emissions_tonnes: Optional[float] = Field(
        default=None, ge=0,
        description="Other indirect emissions (Scope 3)"
    )
    embodied_carbon_kg_co2_per_sqm: Optional[float] = Field(
        default=None, ge=0,
        description="Embodied carbon from construction"
    )
    net_zero_pathway: Optional[bool] = Field(
        default=None,
        description="Whether property has net-zero pathway"
    )
    net_zero_target_year: Optional[int] = Field(
        default=None,
        description="Target year for net zero"
    )
    
    # Green Certifications
    certifications: Optional[list[CertificationType]] = Field(
        default=None,
        description="Green building certifications"
    )
    leed_level: Optional[str] = Field(
        default=None,
        description="LEED certification level"
    )
    breeam_rating: Optional[str] = Field(
        default=None,
        description="BREEAM rating"
    )
    well_certification: Optional[bool] = Field(default=None)
    well_level: Optional[str] = Field(default=None)
    mostadam_rating: Optional[str] = Field(
        default=None,
        description="Saudi Mostadam rating"
    )
    certification_expiry_date: Optional[str] = Field(default=None)
    
    # Building Systems
    hvac_efficiency_rating: Optional[str] = Field(default=None)
    cooling_cop: Optional[float] = Field(
        default=None, ge=0,
        description="Cooling coefficient of performance"
    )
    insulation_u_value: Optional[float] = Field(
        default=None, ge=0,
        description="Insulation U-value"
    )
    glazing_performance: Optional[str] = Field(default=None)
    led_lighting_pct: Optional[float] = Field(
        default=None, ge=0, le=100,
        description="Percentage LED lighting"
    )
    smart_lighting_controls: Optional[bool] = Field(default=None)
    occupancy_sensors: Optional[bool] = Field(default=None)
    
    # Renewable Integration
    solar_capacity_kwp: Optional[float] = Field(
        default=None, ge=0,
        description="Solar PV capacity in kWp"
    )
    solar_generation_kwh: Optional[float] = Field(
        default=None, ge=0,
        description="Annual solar generation"
    )
    onsite_renewable_pct: Optional[float] = Field(
        default=None, ge=0, le=100,
        description="Onsite renewable as % of consumption"
    )
    battery_storage_kwh: Optional[float] = Field(
        default=None, ge=0,
        description="Battery storage capacity"
    )
    
    # Waste Management
    waste_diversion_rate_pct: Optional[float] = Field(
        default=None, ge=0, le=100,
        description="Waste diverted from landfill"
    )
    recycling_facilities: Optional[bool] = Field(default=None)
    composting: Optional[bool] = Field(default=None)
    
    # Indoor Environment
    indoor_air_quality_rating: Optional[str] = Field(default=None)
    co2_monitoring: Optional[bool] = Field(default=None)
    natural_ventilation_pct: Optional[float] = Field(
        default=None, ge=0, le=100,
        description="Percentage with natural ventilation"
    )
    daylight_factor: Optional[float] = Field(
        default=None, ge=0,
        description="Average daylight factor"
    )
    biophilic_design_elements: Optional[list[str]] = Field(default=None)
    
    # Climate Resilience
    climate_resilience_measures: Optional[list[str]] = Field(default=None)
    flood_mitigation: Optional[bool] = Field(default=None)
    heat_mitigation: Optional[bool] = Field(default=None)
    backup_power_hours: Optional[float] = Field(default=None, ge=0)
    climate_adaptation_investment_sar: Optional[float] = Field(default=None, ge=0)
    
    # Valuation Impact
    green_premium_pct: Optional[float] = Field(
        default=None,
        description="Green premium in value/rent"
    )
    brown_discount_pct: Optional[float] = Field(
        default=None,
        description="Brown discount if non-compliant"
    )
    stranded_asset_risk_adjustment_pct: Optional[float] = Field(
        default=None,
        description="Adjustment for stranding risk"
    )
    esg_capex_required_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Capex needed for ESG improvements"
    )
    
    # Social and Governance
    affordable_housing_units: Optional[int] = Field(default=None, ge=0)
    community_amenities: Optional[list[str]] = Field(default=None)
    accessibility_score: Optional[int] = Field(default=None, ge=0, le=100)
    tenant_satisfaction_score: Optional[int] = Field(default=None, ge=0, le=100)

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "energy_intensity_kwh_per_sqm": 150,
                "certifications": ["leed"],
                "leed_level": "Gold",
                "solar_capacity_kwp": 100,
                "green_premium_pct": 5,
            }
        }
