"""
Category 3: Site and Land Characteristics

Physical site attributes, topography, utilities, and access.
"""

from typing import Optional

from pydantic import BaseModel, Field

from .enums import HazardType


class SiteLand(BaseModel):
    """
    Site and land characteristics.
    
    Physical attributes of the land including area, shape, topography,
    environmental factors, utilities, and access.
    """
    
    # Site Area
    gross_site_area_sqm: Optional[float] = Field(
        default=None, gt=0,
        description="Gross site area in square meters"
    )
    net_site_area_sqm: Optional[float] = Field(
        default=None, gt=0,
        description="Net developable site area in square meters"
    )
    developable_area_sqm: Optional[float] = Field(
        default=None, ge=0,
        description="Developable area after setbacks and easements"
    )
    
    # Shape and Dimensions
    site_shape: Optional[str] = Field(
        default=None,
        description="Site shape (regular, irregular, L-shaped, etc.)"
    )
    site_depth_m: Optional[float] = Field(
        default=None, ge=0,
        description="Site depth in meters"
    )
    site_width_m: Optional[float] = Field(
        default=None, ge=0,
        description="Site width/frontage in meters"
    )
    depth_to_width_ratio: Optional[float] = Field(
        default=None, ge=0,
        description="Depth to width ratio"
    )
    
    # Topography
    topography: Optional[str] = Field(
        default=None,
        description="Topography description (flat, sloping, undulating)"
    )
    slope_pct: Optional[float] = Field(
        default=None, ge=0, le=100,
        description="Average slope percentage"
    )
    elevation_m: Optional[float] = Field(
        default=None,
        description="Site elevation above sea level in meters"
    )
    
    # Soil and Geotechnical
    soil_bearing_capacity_kpa: Optional[float] = Field(
        default=None, ge=0,
        description="Soil bearing capacity in kPa"
    )
    soil_type: Optional[str] = Field(
        default=None,
        description="Primary soil type"
    )
    geotechnical_risk: Optional[str] = Field(
        default=None,
        description="Geotechnical risk level (low, moderate, high)"
    )
    contamination_risk: Optional[str] = Field(
        default=None,
        description="Contamination risk level"
    )
    contamination_remediation_cost_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Estimated remediation cost if contaminated"
    )
    
    # Flood and Drainage
    flood_zone: Optional[str] = Field(
        default=None,
        description="Flood zone classification"
    )
    flood_risk_level: Optional[str] = Field(
        default=None,
        description="Flood risk level (low, moderate, high)"
    )
    drainage_condition: Optional[str] = Field(
        default=None,
        description="Site drainage condition"
    )
    water_table_depth_m: Optional[float] = Field(
        default=None, ge=0,
        description="Water table depth in meters"
    )
    
    # Natural Hazards
    natural_hazards: Optional[list[HazardType]] = Field(
        default=None,
        description="Applicable natural hazards"
    )
    seismic_zone: Optional[str] = Field(
        default=None,
        description="Seismic zone classification"
    )
    sandstorm_exposure: Optional[str] = Field(
        default=None,
        description="Sandstorm exposure level"
    )
    
    # Access
    access_points_count: Optional[int] = Field(
        default=None, ge=0,
        description="Number of vehicular access points"
    )
    curb_cuts_count: Optional[int] = Field(
        default=None, ge=0,
        description="Number of curb cuts"
    )
    has_easements: Optional[bool] = Field(
        default=None,
        description="Whether site has easements"
    )
    easement_types: Optional[list[str]] = Field(
        default=None,
        description="Types of easements on the property"
    )
    right_of_way_m: Optional[float] = Field(
        default=None, ge=0,
        description="Right of way width in meters"
    )
    
    # Utilities
    electricity_connected: Optional[bool] = Field(
        default=None,
        description="Whether electricity is connected"
    )
    electricity_capacity_kw: Optional[float] = Field(
        default=None, ge=0,
        description="Electrical capacity in kW"
    )
    water_connected: Optional[bool] = Field(
        default=None,
        description="Whether water is connected"
    )
    water_capacity_cmd: Optional[float] = Field(
        default=None, ge=0,
        description="Water capacity in cubic meters per day"
    )
    sewer_connected: Optional[bool] = Field(
        default=None,
        description="Whether sewer is connected"
    )
    gas_connected: Optional[bool] = Field(
        default=None,
        description="Whether natural gas is connected"
    )
    district_cooling_connected: Optional[bool] = Field(
        default=None,
        description="Whether district cooling is connected"
    )
    district_cooling_capacity_tr: Optional[float] = Field(
        default=None, ge=0,
        description="District cooling capacity in tons of refrigeration"
    )
    telecom_fiber: Optional[bool] = Field(
        default=None,
        description="Whether fiber optic is available"
    )
    utility_connection_cost_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Estimated utility connection costs"
    )
    
    # Parking and Loading
    surface_parking_spaces: Optional[int] = Field(
        default=None, ge=0,
        description="Number of surface parking spaces"
    )
    loading_docks: Optional[int] = Field(
        default=None, ge=0,
        description="Number of loading docks"
    )
    truck_turning_radius_m: Optional[float] = Field(
        default=None, ge=0,
        description="Truck turning radius in meters"
    )
    
    # Landscaping and Open Space
    landscaped_area_sqm: Optional[float] = Field(
        default=None, ge=0,
        description="Landscaped area in square meters"
    )
    open_space_ratio: Optional[float] = Field(
        default=None, ge=0, le=1,
        description="Open space ratio"
    )
    
    # Setbacks
    front_setback_m: Optional[float] = Field(
        default=None, ge=0,
        description="Front setback in meters"
    )
    rear_setback_m: Optional[float] = Field(
        default=None, ge=0,
        description="Rear setback in meters"
    )
    side_setback_m: Optional[float] = Field(
        default=None, ge=0,
        description="Side setback in meters"
    )
    
    # Boundary
    boundary_certainty: Optional[str] = Field(
        default=None,
        description="Boundary certainty (surveyed, estimated, disputed)"
    )
    has_encroachments: Optional[bool] = Field(
        default=None,
        description="Whether there are encroachments"
    )
    encroachment_description: Optional[str] = Field(
        default=None,
        description="Description of any encroachments"
    )
    survey_date: Optional[str] = Field(
        default=None,
        description="Date of most recent survey"
    )
    survey_quality: Optional[str] = Field(
        default=None,
        description="Survey quality (professional, sketch, none)"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "gross_site_area_sqm": 2500,
                "net_site_area_sqm": 2200,
                "topography": "flat",
                "electricity_connected": True,
                "water_connected": True,
            }
        }
