"""SQLAlchemy ORM models for Qaim."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Text, Float, Integer, Boolean, DateTime,
    ForeignKey, JSON, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from ..core.database import Base


def gen_id() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ── Users & Auth ──

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=gen_id)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="valuer")  # admin, valuer, reviewer, viewer
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)


class Organization(Base):
    __tablename__ = "organizations"
    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=utcnow)


# ── Cases ──

class Case(Base):
    __tablename__ = "cases"
    id = Column(String, primary_key=True, default=gen_id)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    city = Column(String(255), nullable=True)
    created_by = Column(String, default="admin")
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    sources = relationship("Source", back_populates="case", cascade="all, delete-orphan")
    comparables = relationship("Comparable", back_populates="case", cascade="all, delete-orphan")


# ── Sources ──

class Source(Base):
    __tablename__ = "sources"
    id = Column(String, primary_key=True, default=gen_id)
    case_id = Column(String, ForeignKey("cases.id"), nullable=False)
    source_type = Column(String(20), nullable=False)  # url, pdf, manual
    url = Column(Text, nullable=True)
    filename = Column(String(500), nullable=True)
    file_path = Column(Text, nullable=True)
    raw_content = Column(Text, nullable=True)
    fetch_status = Column(String(20), default="pending")
    fetched_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    case = relationship("Case", back_populates="sources")
    extraction_jobs = relationship("ExtractionJob", back_populates="source", cascade="all, delete-orphan")


# ── Extraction Jobs ──

class ExtractionJob(Base):
    __tablename__ = "extraction_jobs"
    id = Column(String, primary_key=True, default=gen_id)
    case_id = Column(String, ForeignKey("cases.id"), nullable=False)
    source_id = Column(String, ForeignKey("sources.id"), nullable=False)
    status = Column(String(20), default="pending")
    extractor_name = Column(String(100), nullable=True)
    extractor_version = Column(String(20), default="0.1.0")
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    fields_extracted = Column(Integer, default=0)
    created_at = Column(DateTime, default=utcnow)

    source = relationship("Source", back_populates="extraction_jobs")


# ── Comparables ──

class Comparable(Base):
    __tablename__ = "comparables"
    id = Column(String, primary_key=True, default=gen_id)
    case_id = Column(String, ForeignKey("cases.id"), nullable=False)
    source_id = Column(String, ForeignKey("sources.id"), nullable=False)
    extraction_job_id = Column(String, ForeignKey("extraction_jobs.id"), nullable=True)
    source_url = Column(Text, nullable=True)
    source_type = Column(String(20), default="url")
    property_title = Column(String(500), nullable=True)
    city = Column(String(255), nullable=True)
    district = Column(String(255), nullable=True)
    subdistrict = Column(String(255), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    property_category = Column(String(50), nullable=True)
    property_subtype = Column(String(50), nullable=True)
    evidence_type = Column(String(50), default="unknown")
    asking_price = Column(Float, nullable=True)
    transacted_price = Column(Float, nullable=True)
    currency = Column(String(10), default="SAR")
    areas = Column(JSON, default=list)  # List of AreaMeasurement dicts
    price_per_sqm = Column(Float, nullable=True)
    listing_date = Column(String(100), nullable=True)
    transaction_date = Column(String(100), nullable=True)
    tenure = Column(String(50), default="unknown")
    remaining_lease_term = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    reliability_score = Column(Integer, default=2)
    is_invalid = Column(Boolean, default=False)
    is_outlier = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    case = relationship("Case", back_populates="comparables")
    extracted_fields = relationship("ExtractedField", back_populates="comparable", cascade="all, delete-orphan")
    overrides = relationship("FieldOverride", back_populates="comparable", cascade="all, delete-orphan")


# ── Extracted Fields ──

class ExtractedField(Base):
    __tablename__ = "extracted_fields"
    id = Column(String, primary_key=True, default=gen_id)
    comparable_id = Column(String, ForeignKey("comparables.id"), nullable=False)
    source_id = Column(String, ForeignKey("sources.id"), nullable=False)
    field_name = Column(String(100), nullable=False)
    raw_value = Column(Text, nullable=True)
    normalized_value = Column(Text, nullable=True)
    confidence = Column(Float, default=0.0)
    citation = Column(JSON, nullable=True)  # Full CitationObject as JSON
    extraction_version = Column(String(20), default="0.1.0")
    fact_type = Column(String(20), default="fact")
    created_at = Column(DateTime, default=utcnow)

    comparable = relationship("Comparable", back_populates="extracted_fields")


# ── Field Overrides (Audit Log) ──

class FieldOverride(Base):
    __tablename__ = "field_overrides"
    id = Column(String, primary_key=True, default=gen_id)
    comparable_id = Column(String, ForeignKey("comparables.id"), nullable=False)
    field_name = Column(String(100), nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    reason = Column(Text, nullable=False)
    overridden_by = Column(String(100), default="admin")
    overridden_at = Column(DateTime, default=utcnow)

    comparable = relationship("Comparable", back_populates="overrides")


# ── Report Artifacts ──

class ReportArtifact(Base):
    __tablename__ = "report_artifacts"
    id = Column(String, primary_key=True, default=gen_id)
    case_id = Column(String, ForeignKey("cases.id"), nullable=False)
    report_type = Column(String(50), nullable=False)  # csv, xlsx, pdf
    filename = Column(String(500), nullable=False)
    file_path = Column(Text, nullable=False)
    created_by = Column(String(100), default="admin")
    created_at = Column(DateTime, default=utcnow)


# ══════════════════════════════════════════════
# Future Stage Tables (Scaffolding)
# ══════════════════════════════════════════════

class SubjectProperty(Base):
    """Stage 2: Subject property profile."""
    __tablename__ = "subject_properties"
    id = Column(String, primary_key=True, default=gen_id)
    case_id = Column(String, ForeignKey("cases.id"), nullable=False)
    title = Column(String(500), nullable=True)
    city = Column(String(255), nullable=True)
    district = Column(String(255), nullable=True)
    property_category = Column(String(50), nullable=True)
    property_subtype = Column(String(50), nullable=True)
    tenure = Column(String(50), default="unknown")
    areas = Column(JSON, default=list)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    description = Column(Text, nullable=True)
    valuation_date = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=utcnow)


class AdjustmentRecord(Base):
    """Stage 3: Valuation adjustment."""
    __tablename__ = "adjustments"
    id = Column(String, primary_key=True, default=gen_id)
    comparable_id = Column(String, ForeignKey("comparables.id"), nullable=True)
    subject_id = Column(String, ForeignKey("subject_properties.id"), nullable=True)
    adjustment_type = Column(String(100), nullable=True)
    adjustment_value = Column(Float, nullable=True)
    adjustment_pct = Column(Float, nullable=True)
    method = Column(String(50), nullable=True)
    evidence = Column(Text, nullable=True)
    fact_type = Column(String(20), default="assumption")
    approved_by = Column(String(100), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)


class ValuationRunRecord(Base):
    """Stage 5: Valuation run."""
    __tablename__ = "valuation_runs"
    id = Column(String, primary_key=True, default=gen_id)
    case_id = Column(String, ForeignKey("cases.id"), nullable=False)
    subject_id = Column(String, ForeignKey("subject_properties.id"), nullable=True)
    methodology = Column(String(100), nullable=True)
    concluded_value = Column(Float, nullable=True)
    currency = Column(String(10), default="SAR")
    value_per_sqm = Column(Float, nullable=True)
    approved_by = Column(String(100), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)


class MarketReferenceData(Base):
    """Reference data for market indices, benchmarks."""
    __tablename__ = "market_reference_data"
    id = Column(String, primary_key=True, default=gen_id)
    data_type = Column(String(100), nullable=False)
    city = Column(String(255), nullable=True)
    district = Column(String(255), nullable=True)
    property_category = Column(String(50), nullable=True)
    period = Column(String(50), nullable=True)
    value = Column(Float, nullable=True)
    unit = Column(String(50), nullable=True)
    source_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=utcnow)
