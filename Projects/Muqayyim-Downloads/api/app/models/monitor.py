"""Mizan Monitor: portfolios over the existing properties. Valuations stay in the shared engine."""
import uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, String, Text, JSON, UniqueConstraint, event
from api.app.database import Base
from api.app.models import UUID


class Portfolio(Base):
    __tablename__ = 'portfolios'
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    created_by = Column(UUID(), ForeignKey('users.id'), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    owner_entity = Column(String(255))
    fund = Column(String(255))
    asset_manager = Column(String(255))
    settings = Column(JSON, nullable=False, default=dict)  # Alert thresholds; defaults live in monitor_calc.
    official_nav_sar = Column(Float)
    is_demo = Column(Boolean, nullable=False, default=False)
    last_checked_at = Column(DateTime)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class PortfolioAsset(Base):
    __tablename__ = 'portfolio_assets'
    __table_args__ = (UniqueConstraint('portfolio_id', 'property_id', name='uq_portfolio_property'),)
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(UUID(), ForeignKey('portfolios.id'), nullable=False, index=True)
    property_id = Column(UUID(), ForeignKey('properties.id'), nullable=False, index=True)
    ownership_pct = Column(Float, nullable=False, default=100)
    acquisition_cost_sar = Column(Float)
    acquisition_date = Column(Date)
    book_value_sar = Column(Float)
    debt_sar = Column(Float)  # On a 100% basis; scaled by ownership in portfolio totals.
    # How often Mizan looks for evidence, versus how often a formal valuation is expected.
    monitoring_frequency = Column(String(20), nullable=False, default='event_driven')
    formal_frequency = Column(String(20), nullable=False, default='quarterly')
    next_formal_on = Column(Date)
    formal_requested_at = Column(DateTime)
    facts = Column(JSON, nullable=False, default=dict)  # User-provided NOI, occupancy, WAULT, each with source and date.
    method_weights = Column(JSON)  # Reviewer's weights; without them reconciliation is the median.
    demo_evidence = Column(JSON)  # Synthetic sales for demo assets only, so they can never reach a real valuation.
    summary = Column(JSON, nullable=False, default=dict)  # Latest computed state, so dashboards never rescan snapshots.
    priority_score = Column(Float, nullable=False, default=0, index=True)
    last_checked_at = Column(DateTime)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class ValuationSnapshot(Base):
    """Immutable record of one valuation: inputs, evidence, weighting, result and why it was made."""
    __tablename__ = 'valuation_snapshots'
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    property_id = Column(UUID(), ForeignKey('properties.id'), nullable=False, index=True)
    kind = Column(String(20), nullable=False, index=True)  # official | indicative
    valued_on = Column(Date, nullable=False, index=True)
    value_sar = Column(Float, nullable=False)
    low_sar = Column(Float)
    high_sar = Column(Float)
    confidence = Column(String(10))  # high | medium | low; official valuations carry none.
    trigger = Column(String(50), nullable=False)
    origin = Column(String(20), nullable=False)  # real | demo | user_provided | derived
    previous_id = Column(UUID(), ForeignKey('valuation_snapshots.id'))
    data = Column(JSON, nullable=False)
    created_by = Column(UUID(), ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


@event.listens_for(ValuationSnapshot, 'before_update')
def snapshots_are_immutable(mapper, connection, target):
    raise ValueError('Valuation snapshots are immutable; record a new snapshot instead')


class MonitorEvent(Base):
    """Something that happened to an asset or its market, detected or recorded by a user."""
    __tablename__ = 'monitor_events'
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    property_id = Column(UUID(), ForeignKey('properties.id'), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)
    category = Column(String(20), nullable=False)  # property | market | location | portfolio | system
    occurred_on = Column(Date, nullable=False, index=True)
    summary = Column(Text, nullable=False)
    origin = Column(String(20), nullable=False)  # detected | user_provided | demo
    snapshot_id = Column(UUID(), ForeignKey('valuation_snapshots.id'))
    details = Column(JSON)
    created_by = Column(UUID(), ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class MonitorAlert(Base):
    __tablename__ = 'monitor_alerts'
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(UUID(), ForeignKey('portfolios.id'), nullable=False, index=True)
    asset_id = Column(UUID(), ForeignKey('portfolio_assets.id'), index=True)  # Null for portfolio-level alerts.
    kind = Column(String(50), nullable=False)
    severity = Column(String(10), nullable=False)  # info | watch | warning | critical
    status = Column(String(20), nullable=False, default='open', index=True)  # open | investigating | accepted | resolved
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    details = Column(JSON)
    raised_on = Column(Date, nullable=False)
    note = Column(Text)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
