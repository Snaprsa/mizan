"""
Category 4: Planning and Development Controls

Zoning, FAR, permits, and regulatory constraints.
"""

from typing import Optional

from pydantic import BaseModel, Field

from .enums import ZoningCategory


class PlanningControls(BaseModel):
    """
    Planning and development control variables.
    
    Regulatory framework including zoning, density controls, height limits,
    permitting status, and development constraints.
    """
    
    # Zoning
    zoning_designation: Optional[str] = Field(
        default=None,
        description="Specific zoning code/designation"
    )
    zoning_category: Optional[ZoningCategory] = Field(
        default=None,
        description="General zoning category"
    )
    permitted_uses: Optional[list[str]] = Field(
        default=None,
        description="Permitted uses under current zoning"
    )
    conditional_uses: Optional[list[str]] = Field(
        default=None,
        description="Conditionally permitted uses"
    )
    
    # Density Controls
    floor_area_ratio: Optional[float] = Field(
        default=None, ge=0,
        description="Floor Area Ratio (FAR) / Plot Ratio"
    )
    plot_ratio: Optional[float] = Field(
        default=None, ge=0,
        description="Plot ratio (alternative term for FAR)"
    )
    site_coverage_pct: Optional[float] = Field(
        default=None, ge=0, le=100,
        description="Maximum site coverage percentage"
    )
    height_limit_m: Optional[float] = Field(
        default=None, ge=0,
        description="Maximum building height in meters"
    )
    height_limit_floors: Optional[int] = Field(
        default=None, ge=0,
        description="Maximum number of floors"
    )
    
    # Setback Requirements
    required_front_setback_m: Optional[float] = Field(
        default=None, ge=0,
        description="Required front setback in meters"
    )
    required_rear_setback_m: Optional[float] = Field(
        default=None, ge=0,
        description="Required rear setback in meters"
    )
    required_side_setback_m: Optional[float] = Field(
        default=None, ge=0,
        description="Required side setback in meters"
    )
    daylight_plane_angle: Optional[float] = Field(
        default=None, ge=0, le=90,
        description="Daylight plane angle in degrees"
    )
    view_corridor_restrictions: Optional[str] = Field(
        default=None,
        description="View corridor restrictions if any"
    )
    
    # Unit Constraints
    density_cap_units_per_ha: Optional[float] = Field(
        default=None, ge=0,
        description="Maximum residential density (units per hectare)"
    )
    unit_mix_requirements: Optional[str] = Field(
        default=None,
        description="Required unit mix specifications"
    )
    minimum_unit_size_sqm: Optional[float] = Field(
        default=None, ge=0,
        description="Minimum unit size in square meters"
    )
    affordable_housing_pct: Optional[float] = Field(
        default=None, ge=0, le=100,
        description="Required affordable housing percentage"
    )
    
    # Parking
    parking_ratio_required: Optional[float] = Field(
        default=None, ge=0,
        description="Required parking spaces per unit or per sqm"
    )
    parking_basis: Optional[str] = Field(
        default=None,
        description="Basis for parking calculation (per unit, per sqm, per bed)"
    )
    accessible_parking_required: Optional[int] = Field(
        default=None, ge=0,
        description="Required number of accessible parking spaces"
    )
    bicycle_parking_required: Optional[int] = Field(
        default=None, ge=0,
        description="Required bicycle parking spaces"
    )
    
    # Floorplate Constraints
    max_floorplate_sqm: Optional[float] = Field(
        default=None, ge=0,
        description="Maximum floorplate size"
    )
    core_requirements: Optional[str] = Field(
        default=None,
        description="Building core requirements"
    )
    
    # Heritage and Environmental
    heritage_listed: Optional[bool] = Field(
        default=None,
        description="Whether property has heritage listing"
    )
    heritage_grade: Optional[str] = Field(
        default=None,
        description="Heritage grade if listed"
    )
    protected_trees: Optional[bool] = Field(
        default=None,
        description="Whether there are protected trees"
    )
    archaeological_constraints: Optional[bool] = Field(
        default=None,
        description="Whether there are archaeological constraints"
    )
    environmental_impact_required: Optional[bool] = Field(
        default=None,
        description="Whether EIA is required"
    )
    mitigation_obligations: Optional[list[str]] = Field(
        default=None,
        description="Required mitigation measures"
    )
    
    # Development Fees
    development_fees_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Development fees in SAR"
    )
    infrastructure_levy_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Infrastructure levy in SAR"
    )
    community_contributions_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Community contributions/exactions"
    )
    
    # Permitting Status
    planning_approval_status: Optional[str] = Field(
        default=None,
        description="Current planning approval status"
    )
    building_permit_status: Optional[str] = Field(
        default=None,
        description="Building permit status"
    )
    approvals_obtained: Optional[list[str]] = Field(
        default=None,
        description="List of approvals already obtained"
    )
    conditions_precedent: Optional[list[str]] = Field(
        default=None,
        description="Conditions to be satisfied before development"
    )
    
    # Risk Assessment
    estimated_permit_time_months: Optional[int] = Field(
        default=None, ge=0,
        description="Estimated time to obtain permits"
    )
    appeal_risk: Optional[str] = Field(
        default=None,
        description="Risk of appeal (low, moderate, high)"
    )
    community_opposition_risk: Optional[str] = Field(
        default=None,
        description="Community opposition risk level"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "zoning_category": "residential",
                "floor_area_ratio": 2.5,
                "height_limit_floors": 10,
                "site_coverage_pct": 60,
            }
        }
