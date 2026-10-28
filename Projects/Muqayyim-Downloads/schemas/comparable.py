"""
Comparable — A comparable property record extracted from a source.
Contains all KSA-relevant fields, each backed by ExtractedField with citation.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from .enums import (
    AreaType, AreaUnit, ComparableStatus, Currency, DealType,
    EvidenceType, PropertyType, ReliabilityScore, Tenure,
)
from .extracted_field import ExtractedField


class AreaMeasurement(BaseModel):
    """A single area value with type and unit tracking."""
    value: Optional[float] = None
    unit: AreaUnit = AreaUnit.SQM
    area_type: AreaType = AreaType.UNKNOWN
    raw_value: Optional[str] = None
    raw_unit: Optional[str] = None


class Comparable(BaseModel):
    """
    A comparable property used in valuation.
    
    Every field that comes from extraction has a parallel ExtractedField
    with full citation. This schema is the "flattened view" for the UI
    and export, while extracted_fields holds the provenance.
    """

    id: UUID = Field(default_factory=uuid4)
    case_id: UUID
    source_id: UUID
    extraction_job_id: Optional[UUID] = None

    # Status
    status: ComparableStatus = ComparableStatus.DRAFT
    reliability_score: int = Field(
        default=ReliabilityScore.MARKETPLACE_LISTING,
        ge=1, le=5,
        description="1=unverified, 5=authenticated transaction"
    )

    # === Core Fields ===

    # Identity
    property_title: Optional[str] = None
    source_url: Optional[str] = None
    source_type: Optional[str] = None

    # Location
    city: Optional[str] = None
    city_ar: Optional[str] = None         # Arabic name
    district: Optional[str] = None
    district_ar: Optional[str] = None
    subdistrict: Optional[str] = None
    raw_location_text: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # Property classification
    property_type: PropertyType = PropertyType.UNKNOWN
    deal_type: DealType = DealType.UNKNOWN
    evidence_type: EvidenceType = EvidenceType.UNKNOWN

    # Pricing
    asking_price: Optional[float] = None
    transacted_price: Optional[float] = None
    currency: Currency = Currency.SAR
    price_per_sqm: Optional[float] = None

    # Area (can have multiple measurements)
    areas: list[AreaMeasurement] = Field(default_factory=list)
    primary_area_sqm: Optional[float] = None   # Best single area figure

    # Dates
    listing_date: Optional[str] = None         # ISO date or descriptive
    transaction_date: Optional[str] = None
    listing_date_hijri: Optional[str] = None
    transaction_date_hijri: Optional[str] = None

    # Tenure
    tenure: Tenure = Tenure.UNKNOWN
    remaining_lease_years: Optional[float] = None

    # Notes
    notes: Optional[str] = None
    caveats: Optional[str] = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # The full extracted fields with citations are stored separately
    # and joined in the API response. This keeps the comparable
    # lightweight while maintaining full provenance.
    extracted_fields: list[ExtractedField] = Field(default_factory=list)
