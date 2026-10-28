"""
Future stage schemas — scaffolded now, built later.
These define the contracts for Stages 2–5.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from .enums import DataClassification, PropertyType, Tenure


# =============================================================
# STAGE 2: Subject Property
# =============================================================

class SubjectProperty(BaseModel):
    """The property being valued. Created from user input + docs."""
    id: UUID = Field(default_factory=uuid4)
    case_id: UUID

    # Location
    address: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # Classification
    property_type: PropertyType = PropertyType.UNKNOWN
    tenure: Tenure = Tenure.UNKNOWN

    # Areas (sqm)
    land_area_sqm: Optional[float] = None
    bua_sqm: Optional[float] = None
    gla_sqm: Optional[float] = None

    # Building details
    year_built: Optional[int] = None
    floors: Optional[int] = None
    condition: Optional[str] = None
    zoning: Optional[str] = None

    # Valuation context
    valuation_date: Optional[datetime] = None
    purpose_of_valuation: Optional[str] = None
    basis_of_value: Optional[str] = None  # e.g. "Market Value" per RICS/TAQEEM

    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# =============================================================
# STAGE 3: Adjustments & Valuation Run
# =============================================================

class Adjustment(BaseModel):
    """A single adjustment applied to a comparable."""
    id: UUID = Field(default_factory=uuid4)
    valuation_run_id: UUID
    comparable_id: UUID

    adjustment_type: str = Field(
        ..., description="e.g. time, location, size, condition, tenure"
    )
    description: str = Field(default="")
    
    # Values
    percentage: Optional[float] = None     # e.g. -5.0 for 5% downward
    absolute_amount: Optional[float] = None  # SAR amount
    
    # Provenance
    method: str = Field(
        default="manual",
        description="manual | rule | index | pattern"
    )
    evidence: Optional[str] = None
    classification: DataClassification = DataClassification.JUDGMENT
    
    # Approval
    proposed_by: str = Field(default="system")  # system | user_id
    approved: bool = False
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)


class ValuationRun(BaseModel):
    """A complete valuation calculation with all adjustments."""
    id: UUID = Field(default_factory=uuid4)
    case_id: UUID
    subject_id: UUID

    # Method
    approach: str = Field(
        default="sales_comparison",
        description="sales_comparison | income | cost | drc"
    )

    # Results
    indicated_value: Optional[float] = None
    currency: str = "SAR"
    value_per_sqm: Optional[float] = None
    
    # Status
    status: str = Field(default="draft")  # draft | in_review | approved | final
    
    # Audit
    prepared_by: Optional[UUID] = None
    reviewed_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    
    notes: Optional[str] = None
    assumptions: list[str] = Field(default_factory=list)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


# =============================================================
# STAGE 4: Provider / Comparable Discovery
# =============================================================

class ProviderSearchCriteria(BaseModel):
    """Criteria for searching comparable listings from providers."""
    city: Optional[str] = None
    district: Optional[str] = None
    property_type: Optional[PropertyType] = None
    min_area_sqm: Optional[float] = None
    max_area_sqm: Optional[float] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    radius_km: Optional[float] = None
    center_lat: Optional[float] = None
    center_lng: Optional[float] = None
    max_results: int = 20


class CandidateComparable(BaseModel):
    """A potential comp found by a provider, before user selection."""
    provider_name: str
    external_id: str
    url: Optional[str] = None
    title: Optional[str] = None
    summary: Optional[str] = None
    relevance_score: Optional[float] = None  # 0.0–1.0


# =============================================================
# STAGE 5: Report Templates
# =============================================================

class ReportTemplate(BaseModel):
    """Template for generating valuation reports."""
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: Optional[str] = None
    format: str = Field(default="docx")  # docx | pdf
    template_path: Optional[str] = None
    sections: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ReportArtifact(BaseModel):
    """A generated report file."""
    id: UUID = Field(default_factory=uuid4)
    case_id: UUID
    valuation_run_id: Optional[UUID] = None
    template_id: Optional[UUID] = None
    file_path: str
    file_format: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    generated_by: Optional[UUID] = None
