"""
Category 5: Building and Improvements

Property type, areas, structural systems, MEP, amenities, and compliance.
"""

from typing import Optional

from pydantic import BaseModel, Field

from .enums import ExtendedPropertyType, QualityTier


class BuildingImprovements(BaseModel):
    """
    Building and improvements variables.
    
    Physical building characteristics including type, areas, structural system,
    MEP systems, amenities, technology, and compliance status.
    """
    
    # Property Type and Classification
    property_type: Optional[ExtendedPropertyType] = Field(
        default=None,
        description="Property type classification"
    )
    property_subtype: Optional[str] = Field(
        default=None,
        description="Property subtype specification"
    )
    building_class: Optional[str] = Field(
        default=None,
        description="Building class (A, B, C for office; similar for other types)"
    )
    
    # Areas
    gross_building_area_sqm: Optional[float] = Field(
        default=None, gt=0,
        description="Gross Building Area (GBA) in sqm"
    )
    net_leasable_area_sqm: Optional[float] = Field(
        default=None, ge=0,
        description="Net Leasable Area (NLA) in sqm"
    )
    gross_leasable_area_sqm: Optional[float] = Field(
        default=None, ge=0,
        description="Gross Leasable Area (GLA) for retail"
    )
    rentable_area_sqm: Optional[float] = Field(
        default=None, ge=0,
        description="Rentable area in sqm"
    )
    efficiency_ratio: Optional[float] = Field(
        default=None, ge=0, le=1,
        description="Building efficiency ratio (NLA/GBA)"
    )
    common_area_sqm: Optional[float] = Field(
        default=None, ge=0,
        description="Common area in sqm"
    )
    
    # Units and Configuration
    total_units: Optional[int] = Field(
        default=None, ge=0,
        description="Total number of units"
    )
    unit_sizes_sqm: Optional[list[float]] = Field(
        default=None,
        description="List of individual unit sizes"
    )
    avg_unit_size_sqm: Optional[float] = Field(
        default=None, ge=0,
        description="Average unit size in sqm"
    )
    bedroom_mix: Optional[dict] = Field(
        default=None,
        description="Bedroom mix as dict {bedrooms: count}"
    )
    floors_above_grade: Optional[int] = Field(
        default=None, ge=0,
        description="Number of floors above grade"
    )
    floors_below_grade: Optional[int] = Field(
        default=None, ge=0,
        description="Number of basement floors"
    )
    floor_to_floor_height_m: Optional[float] = Field(
        default=None, ge=0,
        description="Floor to floor height in meters"
    )
    ceiling_height_m: Optional[float] = Field(
        default=None, ge=0,
        description="Clear ceiling height in meters"
    )
    typical_floorplate_sqm: Optional[float] = Field(
        default=None, ge=0,
        description="Typical floorplate size in sqm"
    )
    
    # Structural System
    structural_system: Optional[str] = Field(
        default=None,
        description="Structural system (concrete frame, steel, masonry, etc.)"
    )
    foundation_type: Optional[str] = Field(
        default=None,
        description="Foundation type"
    )
    facade_type: Optional[str] = Field(
        default=None,
        description="Facade system type"
    )
    facade_material: Optional[str] = Field(
        default=None,
        description="Primary facade material"
    )
    roof_type: Optional[str] = Field(
        default=None,
        description="Roof type (flat, pitched, etc.)"
    )
    roof_material: Optional[str] = Field(
        default=None,
        description="Roof material"
    )
    
    # MEP Systems
    hvac_type: Optional[str] = Field(
        default=None,
        description="HVAC system type"
    )
    hvac_capacity_tr: Optional[float] = Field(
        default=None, ge=0,
        description="HVAC capacity in tons of refrigeration"
    )
    hvac_redundancy: Optional[str] = Field(
        default=None,
        description="HVAC redundancy level"
    )
    central_ac: Optional[bool] = Field(
        default=None,
        description="Whether central AC is installed"
    )
    district_cooling: Optional[bool] = Field(
        default=None,
        description="Whether connected to district cooling"
    )
    elevator_count: Optional[int] = Field(
        default=None, ge=0,
        description="Number of elevators"
    )
    elevator_speed_mps: Optional[float] = Field(
        default=None, ge=0,
        description="Elevator speed in meters per second"
    )
    service_elevator_count: Optional[int] = Field(
        default=None, ge=0,
        description="Number of service elevators"
    )
    electrical_capacity_kva: Optional[float] = Field(
        default=None, ge=0,
        description="Electrical capacity in kVA"
    )
    backup_power: Optional[bool] = Field(
        default=None,
        description="Whether backup power is available"
    )
    backup_power_capacity_kva: Optional[float] = Field(
        default=None, ge=0,
        description="Backup power capacity"
    )
    
    # Fire and Life Safety
    sprinkler_coverage: Optional[str] = Field(
        default=None,
        description="Sprinkler coverage (full, partial, none)"
    )
    fire_alarm_system: Optional[str] = Field(
        default=None,
        description="Fire alarm system type"
    )
    smoke_control: Optional[bool] = Field(
        default=None,
        description="Whether smoke control system is installed"
    )
    emergency_stairwells: Optional[int] = Field(
        default=None, ge=0,
        description="Number of emergency stairwells"
    )
    egress_compliance: Optional[bool] = Field(
        default=None,
        description="Whether egress meets code"
    )
    
    # Fit-out and Finishes
    finish_quality: Optional[QualityTier] = Field(
        default=None,
        description="Overall finish quality tier"
    )
    lobby_quality: Optional[QualityTier] = Field(
        default=None,
        description="Lobby finish quality"
    )
    common_area_quality: Optional[QualityTier] = Field(
        default=None,
        description="Common area finish quality"
    )
    flooring_type: Optional[str] = Field(
        default=None,
        description="Primary flooring type"
    )
    wall_finishes: Optional[str] = Field(
        default=None,
        description="Wall finish description"
    )
    ceiling_type: Optional[str] = Field(
        default=None,
        description="Ceiling type (exposed, suspended, etc.)"
    )
    ffe_included: Optional[bool] = Field(
        default=None,
        description="Whether FF&E is included"
    )
    ffe_value_sar: Optional[float] = Field(
        default=None, ge=0,
        description="FF&E value if included"
    )
    
    # Amenities
    has_gym: Optional[bool] = Field(default=None)
    has_pool: Optional[bool] = Field(default=None)
    has_concierge: Optional[bool] = Field(default=None)
    has_lounge: Optional[bool] = Field(default=None)
    has_meeting_rooms: Optional[bool] = Field(default=None)
    has_business_center: Optional[bool] = Field(default=None)
    has_rooftop_amenity: Optional[bool] = Field(default=None)
    has_storage: Optional[bool] = Field(default=None)
    storage_units: Optional[int] = Field(default=None, ge=0)
    amenity_list: Optional[list[str]] = Field(
        default=None,
        description="Full list of amenities"
    )
    
    # Technology
    bms_installed: Optional[bool] = Field(
        default=None,
        description="Building Management System installed"
    )
    smart_home_enabled: Optional[bool] = Field(
        default=None,
        description="Smart home/IoT enabled"
    )
    access_control_type: Optional[str] = Field(
        default=None,
        description="Access control system type"
    )
    fiber_to_unit: Optional[bool] = Field(
        default=None,
        description="Fiber optic to each unit"
    )
    ev_charging_stations: Optional[int] = Field(
        default=None, ge=0,
        description="Number of EV charging stations"
    )
    
    # Compliance
    accessibility_compliant: Optional[bool] = Field(
        default=None,
        description="Whether accessibility requirements are met"
    )
    building_code_compliant: Optional[bool] = Field(
        default=None,
        description="Whether building meets current code"
    )
    occupancy_certificate: Optional[bool] = Field(
        default=None,
        description="Whether occupancy certificate is obtained"
    )
    certifications: Optional[list[str]] = Field(
        default=None,
        description="Building certifications obtained"
    )
    
    # Age and Condition
    year_built: Optional[int] = Field(
        default=None, ge=1900, le=2030,
        description="Year of original construction"
    )
    year_renovated: Optional[int] = Field(
        default=None, ge=1900, le=2030,
        description="Year of last major renovation"
    )
    renovation_scope: Optional[str] = Field(
        default=None,
        description="Scope of last renovation"
    )
    remaining_useful_life_years: Optional[int] = Field(
        default=None, ge=0,
        description="Estimated remaining useful life"
    )
    effective_age_years: Optional[int] = Field(
        default=None, ge=0,
        description="Effective age considering condition"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "property_type": "apartment",
                "gross_building_area_sqm": 5000,
                "total_units": 24,
                "elevator_count": 2,
                "year_built": 2020,
            }
        }
