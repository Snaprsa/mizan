"""Additive Mizan foundation. Legacy case/comparable tables remain authoritative."""
import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, JSON, UniqueConstraint
from api.app.database import Base
from api.app.models import UUID


class Property(Base):
    __tablename__ = 'properties'
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    created_by = Column(UUID(), ForeignKey('users.id'), nullable=False, index=True)
    case_id = Column(UUID(), ForeignKey('cases.id'), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    country = Column(String(2), nullable=False, default='SA')
    currency = Column(String(3), nullable=False, default='SAR')
    locale = Column(String(10), nullable=False, default='en-SA')
    city = Column(String(255), index=True)
    district = Column(String(255), index=True)
    property_type = Column(String(100), index=True)
    address = Column(Text)
    plot_number = Column(String(100), index=True)
    data = Column(JSON, nullable=False)
    revision = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class PropertyRevision(Base):
    __tablename__ = 'property_revisions'
    __table_args__ = (UniqueConstraint('property_id', 'revision', name='uq_property_revision'),)
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    property_id = Column(UUID(), ForeignKey('properties.id'), nullable=False, index=True)
    revision = Column(Integer, nullable=False)
    snapshot = Column(JSON, nullable=False)
    reason = Column(Text, nullable=False)
    created_by = Column(UUID(), ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class PropertyAssumption(Base):
    __tablename__ = 'property_assumptions'
    __table_args__ = (UniqueConstraint('property_id', 'key', name='uq_property_assumption'),)
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    property_id = Column(UUID(), ForeignKey('properties.id'), nullable=False, index=True)
    key = Column(String(100), nullable=False)
    data = Column(JSON, nullable=False)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class DataSource(Base):
    __tablename__ = 'data_sources'
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    created_by = Column(UUID(), ForeignKey('users.id'), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    provider = Column(String(100), nullable=False)
    source_type = Column(String(50), nullable=False)
    uri = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class MarketObservation(Base):
    __tablename__ = 'market_observations'
    __table_args__ = (UniqueConstraint('data_source_id', 'external_id', name='uq_market_source_record'),)
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    data_source_id = Column(UUID(), ForeignKey('data_sources.id'), nullable=False, index=True)
    external_id = Column(String(255), nullable=False)
    observed_on = Column(String(10), nullable=False, index=True)
    country = Column(String(2), nullable=False)
    city = Column(String(255), nullable=False, index=True)
    district = Column(String(255))
    property_type = Column(String(100), nullable=False)
    metric = Column(String(100), nullable=False, index=True)
    unit = Column(String(50), nullable=False)
    raw_value = Column(JSON, nullable=False)
    normalized_value = Column(JSON, nullable=False)
    reliability = Column(Integer, nullable=False)
    details = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
