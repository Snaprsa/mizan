"""Core domain models (Pydantic schemas) shared across the platform."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from .enums import (
    PropertyCategory, PropertySubType, TenureType, AreaType, AreaUnit,
    Currency, EvidenceType, SourceType, ReliabilityScore,
    ExtractionJobStatus, FactType
)
from .citation import CitationObject


# ── Area with full provenance ──
class AreaMeasurement(BaseModel):
    raw_value: Optional[float] = None
    raw_unit: Optional[str] = None
    normalized_value: Optional[float] = None
    normalized_unit: AreaUnit = AreaUnit.SQM
    area_type: AreaType = AreaType.OTHER
    citation: Optional[CitationObject] = None


# ── Extracted Field ──
class ExtractedFieldValue(BaseModel):
    """A single extracted field with full provenance."""
    field_name: str
    raw_value: Optional[str] = None
    normalized_value: Optional[str] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    citation: Optional[CitationObject] = None
    extraction_version: str = "0.1.0"
    fact_type: FactType = FactType.FACT
    source_id: Optional[str] = None


# ── Comparable ──
class ComparableCreate(BaseModel):
    case_id: str
    source_url: Optional[str] = None
    source_file: Optional[str] = None
    source_type: SourceType = SourceType.URL


class ComparableRecord(BaseModel):
    """Structured comparable property record."""
    id: str
    case_id: str
    source_id: str
    source_url: Optional[str] = None
    source_type: SourceType = SourceType.URL
    property_title: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    subdistrict: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    property_category: Optional[PropertyCategory] = None
    property_subtype: Optional[PropertySubType] = None
    evidence_type: EvidenceType = EvidenceType.UNKNOWN
    asking_price: Optional[float] = None
    transacted_price: Optional[float] = None
    currency: Currency = Currency.SAR
    areas: List[AreaMeasurement] = Field(default_factory=list)
    price_per_sqm: Optional[float] = None
    listing_date: Optional[str] = None
    transaction_date: Optional[str] = None
    tenure: TenureType = TenureType.UNKNOWN
    remaining_lease_term: Optional[str] = None
    notes: Optional[str] = None
    reliability_score: ReliabilityScore = ReliabilityScore.MARKETPLACE_LISTING
    is_invalid: bool = False
    is_outlier: bool = False
    extracted_fields: List[ExtractedFieldValue] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ── Override / Audit ──
class FieldOverride(BaseModel):
    id: Optional[str] = None
    comparable_id: str
    field_name: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    reason: str
    overridden_by: str = "admin"
    overridden_at: Optional[datetime] = None


# ── Source ──
class SourceRecord(BaseModel):
    id: str
    case_id: str
    source_type: SourceType
    url: Optional[str] = None
    filename: Optional[str] = None
    file_path: Optional[str] = None
    raw_content: Optional[str] = None
    fetch_status: str = "pending"  # pending, fetched, failed
    fetched_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


# ── Case ──
class CaseCreate(BaseModel):
    title: str
    description: Optional[str] = None
    city: Optional[str] = None


class CaseRecord(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    city: Optional[str] = None
    created_by: str = "admin"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    source_count: int = 0
    comp_count: int = 0


# ── Extraction Job ──
class ExtractionJobRecord(BaseModel):
    id: str
    case_id: str
    source_id: str
    status: ExtractionJobStatus = ExtractionJobStatus.PENDING
    extractor_name: Optional[str] = None
    extractor_version: str = "0.1.0"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    fields_extracted: int = 0


# ══════════════════════════════════════════════
# Future Stage Schemas (Scaffolding)
# ══════════════════════════════════════════════

# Stage 2: Subject Property
class SubjectProperty(BaseModel):
    """Subject property profile — Stage 2."""
    id: Optional[str] = None
    case_id: Optional[str] = None
    title: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    property_category: Optional[PropertyCategory] = None
    property_subtype: Optional[PropertySubType] = None
    tenure: TenureType = TenureType.UNKNOWN
    areas: List[AreaMeasurement] = Field(default_factory=list)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: Optional[str] = None
    valuation_date: Optional[str] = None
    # TODO: Stage 2 — subject document uploads, zoning, permits


# Stage 3: Adjustment
class Adjustment(BaseModel):
    """Valuation adjustment — Stage 3."""
    id: Optional[str] = None
    comparable_id: Optional[str] = None
    subject_id: Optional[str] = None
    adjustment_type: Optional[str] = None  # time, location, size, condition, etc.
    adjustment_value: Optional[float] = None
    adjustment_pct: Optional[float] = None
    method: Optional[str] = None  # rule, index, judgment
    evidence: Optional[str] = None
    fact_type: FactType = FactType.ASSUMPTION
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    # TODO: Stage 3 — rules engine, prior-report learning


# Stage 5: Valuation Run
class ValuationRun(BaseModel):
    """Valuation run record — Stage 5."""
    id: Optional[str] = None
    case_id: Optional[str] = None
    subject_id: Optional[str] = None
    methodology: Optional[str] = None  # comparison, income, cost
    concluded_value: Optional[float] = None
    currency: Currency = Currency.SAR
    value_per_sqm: Optional[float] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    # TODO: Stage 5 — full report generation
