"""
API request/response schemas for Stage 1 endpoints.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ──────────────────────────────────────────────
# Cases
# ──────────────────────────────────────────────

class CaseCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None


class CaseResponse(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    status: str
    created_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime
    source_count: int = 0
    comparable_count: int = 0

    model_config = {"from_attributes": True}


class CaseListResponse(BaseModel):
    data: list[CaseResponse]
    total: int


# ──────────────────────────────────────────────
# Sources
# ──────────────────────────────────────────────

class SourceAddURL(BaseModel):
    url: str = Field(..., min_length=5)
    notes: Optional[str] = None


class SourceResponse(BaseModel):
    id: UUID
    case_id: UUID
    source_type: str
    url: Optional[str]
    file_name: Optional[str]
    status: str
    error_message: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ──────────────────────────────────────────────
# Extraction Jobs
# ──────────────────────────────────────────────

class ExtractionJobResponse(BaseModel):
    id: UUID
    source_id: UUID
    status: str
    extractor_name: Optional[str]
    extractor_version: Optional[str]
    error_log: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class StartExtractionResponse(BaseModel):
    job_id: UUID
    status: str
    message: str


# ──────────────────────────────────────────────
# Extracted Fields
# ──────────────────────────────────────────────

class ExtractedFieldResponse(BaseModel):
    id: UUID
    field_name: str
    raw_value: Optional[str]
    normalized_value: Optional[str]
    display_value: Optional[str]
    confidence: float
    classification: str
    citation: Optional[dict]  # Full CitationObject as dict
    is_overridden: bool = False
    override_value: Optional[str] = None

    model_config = {"from_attributes": True}


class FieldOverrideRequest(BaseModel):
    new_value: str
    reason: str = Field(..., min_length=1, description="Reason for override is required")


# ──────────────────────────────────────────────
# Comparables
# ──────────────────────────────────────────────

class ComparableResponse(BaseModel):
    id: UUID
    case_id: UUID
    source_id: UUID
    status: str
    reliability_score: int

    # Key fields (denormalized for display)
    property_title: Optional[str]
    city: Optional[str]
    district: Optional[str]
    property_type: Optional[str]
    evidence_type: Optional[str]
    asking_price: Optional[float]
    transacted_price: Optional[float]
    currency: str
    primary_area_sqm: Optional[float]
    price_per_sqm: Optional[float]
    listing_date: Optional[str]
    transaction_date: Optional[str]
    tenure: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    notes: Optional[str]

    created_at: datetime

    # Full extracted fields with citations
    extracted_fields: list[ExtractedFieldResponse] = []

    # Source info
    source_url: Optional[str] = None
    source_type: Optional[str] = None

    model_config = {"from_attributes": True}


class ComparableStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(active|invalid|outlier)$")
    reason: Optional[str] = None


class ComparableListResponse(BaseModel):
    data: list[ComparableResponse]
    total: int


# ──────────────────────────────────────────────
# Generic
# ──────────────────────────────────────────────

class APIResponse(BaseModel):
    """Standard API response envelope."""
    data: Any = None
    meta: Optional[dict] = None
    errors: Optional[list[str]] = None
