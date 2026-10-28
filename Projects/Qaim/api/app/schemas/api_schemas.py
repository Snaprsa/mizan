"""Pydantic schemas for API request/response models."""
from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field


# ── Cases ──
class CaseCreateRequest(BaseModel):
    title: str
    description: Optional[str] = None
    city: Optional[str] = None


class CaseResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    city: Optional[str] = None
    created_by: str = "admin"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    source_count: int = 0
    comp_count: int = 0

    class Config:
        from_attributes = True


# ── Sources ──
class SourceAddURLRequest(BaseModel):
    url: str


class SourceResponse(BaseModel):
    id: str
    case_id: str
    source_type: str
    url: Optional[str] = None
    filename: Optional[str] = None
    fetch_status: str = "pending"
    fetched_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Extraction Jobs ──
class ExtractionJobResponse(BaseModel):
    id: str
    case_id: str
    source_id: str
    status: str = "pending"
    extractor_name: Optional[str] = None
    extractor_version: str = "0.1.0"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    fields_extracted: int = 0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Extracted Fields ──
class ExtractedFieldResponse(BaseModel):
    id: str
    comparable_id: str
    field_name: str
    raw_value: Optional[str] = None
    normalized_value: Optional[str] = None
    confidence: float = 0.0
    citation: Optional[Dict[str, Any]] = None
    extraction_version: str = "0.1.0"
    fact_type: str = "fact"

    class Config:
        from_attributes = True


# ── Comparables ──
class ComparableResponse(BaseModel):
    id: str
    case_id: str
    source_id: str
    source_url: Optional[str] = None
    source_type: str = "url"
    property_title: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    subdistrict: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    property_category: Optional[str] = None
    property_subtype: Optional[str] = None
    evidence_type: str = "unknown"
    asking_price: Optional[float] = None
    transacted_price: Optional[float] = None
    currency: str = "SAR"
    areas: List[Dict[str, Any]] = Field(default_factory=list)
    price_per_sqm: Optional[float] = None
    listing_date: Optional[str] = None
    transaction_date: Optional[str] = None
    tenure: str = "unknown"
    remaining_lease_term: Optional[str] = None
    notes: Optional[str] = None
    reliability_score: int = 2
    is_invalid: bool = False
    is_outlier: bool = False
    extracted_fields: List[ExtractedFieldResponse] = Field(default_factory=list)
    overrides: List["FieldOverrideResponse"] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Overrides ──
class FieldOverrideRequest(BaseModel):
    field_name: str
    new_value: str
    reason: str


class FieldOverrideResponse(BaseModel):
    id: str
    comparable_id: str
    field_name: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    reason: str
    overridden_by: str = "admin"
    overridden_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Comp Status Update ──
class CompStatusUpdate(BaseModel):
    is_invalid: Optional[bool] = None
    is_outlier: Optional[bool] = None


# ── Generic ──
class MessageResponse(BaseModel):
    message: str
    id: Optional[str] = None
