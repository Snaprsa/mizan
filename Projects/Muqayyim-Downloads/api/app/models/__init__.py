"""
SQLAlchemy ORM models for all core entities.
Uses a cross-database UUID type that works with both PostgreSQL and SQLite.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey,
    Integer, String, Text, JSON, TypeDecorator, CHAR,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from api.app.database import Base


class UUID(TypeDecorator):
    """
    Platform-independent UUID type.
    Uses PostgreSQL's native UUID when available, CHAR(36) for SQLite/others.
    Stores and returns Python uuid.UUID objects.
    Accepts (and ignores) as_uuid= kwarg for drop-in compatibility.
    """
    impl = CHAR
    cache_ok = True

    def __init__(self, as_uuid=True, *args, **kwargs):
        # Accept as_uuid for API compatibility; we always store as Python uuid.UUID
        super().__init__(*args, **kwargs)

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return str(value) if not isinstance(value, uuid.UUID) else value
        return str(value) if isinstance(value, uuid.UUID) else value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return uuid.UUID(str(value)) if not isinstance(value, uuid.UUID) else value


# ──────────────────────────────────────────────
# Auth & Org
# ──────────────────────────────────────────────

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    users = relationship("User", back_populates="organization")
    cases = relationship("Case", back_populates="organization")


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    hashed_password = Column(String(512), nullable=True)  # nullable for dev seeding
    role = Column(String(50), default="analyst")  # admin, valuer, analyst, reviewer, viewer
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    organization = relationship("Organization", back_populates="users")


# ──────────────────────────────────────────────
# Cases
# ──────────────────────────────────────────────

class Case(Base):
    __tablename__ = "cases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="draft")  # draft, in_progress, review, completed, archived
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization = relationship("Organization", back_populates="cases")
    sources = relationship("Source", back_populates="case", cascade="all, delete-orphan")
    comparables = relationship("Comparable", back_populates="case", cascade="all, delete-orphan")


# ──────────────────────────────────────────────
# Sources
# ──────────────────────────────────────────────

class Source(Base):
    __tablename__ = "sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False, index=True)
    source_type = Column(String(20), nullable=False)  # url, pdf, manual
    url = Column(Text, nullable=True)
    file_path = Column(Text, nullable=True)
    file_name = Column(String(500), nullable=True)
    raw_content = Column(Text, nullable=True)  # stored HTML or extracted text
    status = Column(String(50), default="pending")  # pending, fetching, fetched, failed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("Case", back_populates="sources")
    extraction_jobs = relationship("ExtractionJob", back_populates="source")
    comparables = relationship("Comparable", back_populates="source")


# ──────────────────────────────────────────────
# Extraction
# ──────────────────────────────────────────────

class ExtractionJob(Base):
    __tablename__ = "extraction_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id"), nullable=False, index=True)
    status = Column(String(50), default="pending")  # pending, running, completed, failed, partial
    extractor_name = Column(String(100), nullable=True)
    extractor_version = Column(String(50), nullable=True)
    error_log = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    source = relationship("Source", back_populates="extraction_jobs")
    extracted_fields = relationship("ExtractedField", back_populates="extraction_job")
    comparables = relationship("Comparable", back_populates="extraction_job")


class ExtractedField(Base):
    __tablename__ = "extracted_fields"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    extraction_job_id = Column(UUID(as_uuid=True), ForeignKey("extraction_jobs.id"), nullable=False, index=True)
    comparable_id = Column(UUID(as_uuid=True), ForeignKey("comparables.id"), nullable=True, index=True)

    field_name = Column(String(100), nullable=False, index=True)
    raw_value = Column(Text, nullable=True)
    normalized_value = Column(Text, nullable=True)  # stored as text, parsed by app
    display_value = Column(Text, nullable=True)
    value_type = Column(String(50), default="string")  # string, number, date, enum, json

    confidence = Column(Float, default=0.0)
    classification = Column(String(50), default="fact")  # fact, assumption, judgment

    # Citation stored as JSONB — full CitationObject
    citation = Column(JSON, nullable=True)

    extraction_version = Column(String(50), nullable=True)
    extracted_at = Column(DateTime, default=datetime.utcnow)

    extraction_job = relationship("ExtractionJob", back_populates="extracted_fields")
    comparable = relationship("Comparable", back_populates="extracted_fields")
    overrides = relationship("Override", back_populates="extracted_field")


# ──────────────────────────────────────────────
# Comparables
# ──────────────────────────────────────────────

class Comparable(Base):
    __tablename__ = "comparables"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False, index=True)
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id"), nullable=False)
    extraction_job_id = Column(UUID(as_uuid=True), ForeignKey("extraction_jobs.id"), nullable=True)

    status = Column(String(50), default="draft")  # active, invalid, outlier, draft
    reliability_score = Column(Integer, default=2)  # 1-5 scale

    # Denormalized key fields for quick querying/display
    # (canonical values are in extracted_fields with citations)
    property_title = Column(Text, nullable=True)
    city = Column(String(255), nullable=True)
    district = Column(String(255), nullable=True)
    property_type = Column(String(100), nullable=True)
    evidence_type = Column(String(100), nullable=True)
    asking_price = Column(Float, nullable=True)
    transacted_price = Column(Float, nullable=True)
    currency = Column(String(10), default="SAR")
    primary_area_sqm = Column(Float, nullable=True)
    price_per_sqm = Column(Float, nullable=True)
    listing_date = Column(String(50), nullable=True)
    transaction_date = Column(String(50), nullable=True)
    tenure = Column(String(50), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    attributes = Column(JSON, nullable=True)  # Reviewed structured details: floor, position, grade, ...

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    case = relationship("Case", back_populates="comparables")
    source = relationship("Source", back_populates="comparables")
    extraction_job = relationship("ExtractionJob", back_populates="comparables")
    extracted_fields = relationship("ExtractedField", back_populates="comparable")


# ──────────────────────────────────────────────
# Overrides (audit trail for edits)
# ──────────────────────────────────────────────

class Override(Base):
    __tablename__ = "overrides"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    extracted_field_id = Column(UUID(as_uuid=True), ForeignKey("extracted_fields.id"), nullable=False, index=True)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    reason = Column(Text, nullable=False)  # reason is REQUIRED
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    extracted_field = relationship("ExtractedField", back_populates="overrides")


# ──────────────────────────────────────────────
# Audit Log
# ──────────────────────────────────────────────

class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type = Column(String(100), nullable=False, index=True)  # case, source, comparable, etc.
    entity_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    action = Column(String(100), nullable=False)  # created, updated, deleted, extracted, overridden, exported
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    details = Column(JSON, nullable=True)  # arbitrary action context
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)


# ──────────────────────────────────────────────
# Future tables (Stage 2-5) — create empty for now
# ──────────────────────────────────────────────

class SubjectProperty(Base):
    """Stage 2 — placeholder table."""
    __tablename__ = "subject_properties"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    data = Column(JSON, nullable=True)  # Will be fully structured in Stage 2
    created_at = Column(DateTime, default=datetime.utcnow)


class Adjustment(Base):
    """Stage 3 — placeholder table."""
    __tablename__ = "adjustments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    valuation_run_id = Column(UUID(as_uuid=True), nullable=True)
    comparable_id = Column(UUID(as_uuid=True), ForeignKey("comparables.id"), nullable=True)
    data = Column(JSON, nullable=True)  # Will be fully structured in Stage 3
    approved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class ValuationRun(Base):
    """Stage 3 — placeholder table."""
    __tablename__ = "valuation_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    subject_id = Column(UUID(as_uuid=True), nullable=True)
    status = Column(String(50), default="draft")
    data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ReportArtifact(Base):
    """Stage 5 — placeholder table."""
    __tablename__ = "report_artifacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    valuation_run_id = Column(UUID(as_uuid=True), nullable=True)
    file_path = Column(Text, nullable=True)
    file_format = Column(String(20), nullable=True)
    generated_at = Column(DateTime, default=datetime.utcnow)


class MarketReferenceData(Base):
    """Reference data for market indices, benchmarks, etc."""
    __tablename__ = "market_reference_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    data_type = Column(String(100), nullable=False)  # index, benchmark, rate
    region = Column(String(255), nullable=True)
    period = Column(String(50), nullable=True)
    value = Column(Float, nullable=True)
    unit = Column(String(50), nullable=True)
    source = Column(Text, nullable=True)
    data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
