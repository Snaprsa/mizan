"""
Pydantic schemas for data validation.

Defines the structure for comparable sales (comps) and subject properties
with field validation, type checking, and default values.
"""

from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class PropertyType(str, Enum):
    """Supported property types for Phase 1."""

    APARTMENT = "apartment"
    VILLA = "villa"


class CompRecord(BaseModel):
    """
    Schema for a comparable sale record.

    Represents a historical property transaction in the Saudi market.
    All monetary values are in SAR.
    """

    # Required fields
    trans_date: date = Field(..., description="Transaction date YYYY-MM-DD")
    city: str = Field(..., min_length=1, description="City name")
    district: str = Field(..., min_length=1, description="District name")
    property_type: PropertyType = Field(..., description="apartment or villa")
    total_price_sar: float = Field(..., gt=0, description="Total sale price in SAR")
    area_sqm: float = Field(..., gt=0, description="Total area in square meters")

    # Core features
    bedrooms: int = Field(..., ge=0, le=20, description="Number of bedrooms")
    bathrooms: int = Field(..., ge=0, le=15, description="Number of bathrooms")
    parking_count: int = Field(default=0, ge=0, le=10, description="Parking spaces")
    floor_level: Optional[int] = Field(
        default=None, ge=-2, le=100, description="Floor level (apartments only)"
    )

    # Age information (one of these should be provided)
    year_built: Optional[int] = Field(
        default=None, ge=1900, le=2030, description="Year of construction"
    )
    age_years: Optional[int] = Field(
        default=None, ge=0, le=100, description="Age in years at transaction"
    )

    # Quality tiers (1=basic, 5=luxury)
    finish_tier: int = Field(default=3, ge=1, le=5, description="Finish quality 1-5")
    condition_tier: int = Field(
        default=3, ge=1, le=5, description="Condition quality 1-5"
    )

    # Binary amenities
    elevator: int = Field(default=0, ge=0, le=1, description="Has elevator 0/1")
    central_ac: int = Field(default=1, ge=0, le=1, description="Has central AC 0/1")
    maid_room: int = Field(default=0, ge=0, le=1, description="Has maid room 0/1")
    garden: int = Field(default=0, ge=0, le=1, description="Has garden 0/1")
    private_entrance: int = Field(
        default=0, ge=0, le=1, description="Has private entrance 0/1"
    )

    # Optional geospatial
    lat: Optional[float] = Field(default=None, ge=15, le=35, description="Latitude")
    lon: Optional[float] = Field(default=None, ge=35, le=60, description="Longitude")

    # Metadata
    source_tag: Optional[str] = Field(
        default=None, description="Data source identifier"
    )

    @field_validator("city", "district")
    @classmethod
    def normalize_string_fields(cls, v: str) -> str:
        """Strip whitespace from string fields."""
        return v.strip()

    @model_validator(mode="after")
    def validate_age_info(self) -> "CompRecord":
        """Ensure at least year_built or age_years is provided."""
        if self.year_built is None and self.age_years is None:
            # Default to 5 years age if neither provided
            object.__setattr__(self, "age_years", 5)
        return self

    @model_validator(mode="after")
    def validate_floor_for_villa(self) -> "CompRecord":
        """Set floor_level to 0 for villas."""
        if self.property_type == PropertyType.VILLA and self.floor_level is not None:
            object.__setattr__(self, "floor_level", 0)
        return self

    @property
    def price_per_sqm(self) -> float:
        """Calculate price per square meter."""
        return self.total_price_sar / self.area_sqm

    @property
    def computed_age_years(self) -> int:
        """Get age in years, computing from year_built if needed."""
        if self.age_years is not None:
            return self.age_years
        if self.year_built is not None:
            current_year = date.today().year
            return max(0, current_year - self.year_built)
        return 5  # Default


class SubjectProperty(BaseModel):
    """
    Schema for a subject property to be valued.

    Similar to CompRecord but total_price_sar is not required.
    Missing optional fields will be imputed during prediction.
    """

    # Identifier
    property_id: Optional[str] = Field(default=None, description="Unique property ID")

    # Required fields
    city: str = Field(..., min_length=1, description="City name")
    district: str = Field(..., min_length=1, description="District name")
    property_type: PropertyType = Field(..., description="apartment or villa")
    area_sqm: float = Field(..., gt=0, description="Total area in square meters")

    # Core features (optional for subject)
    bedrooms: Optional[int] = Field(
        default=None, ge=0, le=20, description="Number of bedrooms"
    )
    bathrooms: Optional[int] = Field(
        default=None, ge=0, le=15, description="Number of bathrooms"
    )
    parking_count: Optional[int] = Field(
        default=None, ge=0, le=10, description="Parking spaces"
    )
    floor_level: Optional[int] = Field(
        default=None, ge=-2, le=100, description="Floor level (apartments only)"
    )

    # Age information
    year_built: Optional[int] = Field(
        default=None, ge=1900, le=2030, description="Year of construction"
    )
    age_years: Optional[int] = Field(
        default=None, ge=0, le=100, description="Age in years"
    )

    # Quality tiers
    finish_tier: Optional[int] = Field(
        default=None, ge=1, le=5, description="Finish quality 1-5"
    )
    condition_tier: Optional[int] = Field(
        default=None, ge=1, le=5, description="Condition quality 1-5"
    )

    # Binary amenities
    elevator: Optional[int] = Field(
        default=None, ge=0, le=1, description="Has elevator 0/1"
    )
    central_ac: Optional[int] = Field(
        default=None, ge=0, le=1, description="Has central AC 0/1"
    )
    maid_room: Optional[int] = Field(
        default=None, ge=0, le=1, description="Has maid room 0/1"
    )
    garden: Optional[int] = Field(default=None, ge=0, le=1, description="Has garden 0/1")
    private_entrance: Optional[int] = Field(
        default=None, ge=0, le=1, description="Has private entrance 0/1"
    )

    # Optional geospatial
    lat: Optional[float] = Field(default=None, ge=15, le=35, description="Latitude")
    lon: Optional[float] = Field(default=None, ge=35, le=60, description="Longitude")

    @field_validator("city", "district")
    @classmethod
    def normalize_string_fields(cls, v: str) -> str:
        """Strip whitespace from string fields."""
        return v.strip()

    def get_present_fields(self) -> set[str]:
        """Return set of field names that are not None."""
        return {
            field
            for field, value in self.model_dump().items()
            if value is not None and field not in ("property_id",)
        }


# Field weights for completeness scoring
FIELD_WEIGHTS = {
    "area_sqm": 1.0,
    "property_type": 1.0,
    "city": 1.0,
    "district": 0.8,
    "bedrooms": 0.6,
    "bathrooms": 0.5,
    "year_built": 0.7,
    "age_years": 0.7,
    "finish_tier": 0.4,
    "condition_tier": 0.4,
    "parking_count": 0.3,
    "floor_level": 0.3,
    "elevator": 0.2,
    "central_ac": 0.2,
    "maid_room": 0.2,
    "garden": 0.2,
    "private_entrance": 0.2,
}
