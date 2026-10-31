"""Add Mizan Monitor tables and a demo flag on properties. Additive only.

Revision ID: 20261031_mizan_monitor
Revises: 20261031_comparable_attributes
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

revision = '20261031_mizan_monitor'
down_revision = '20261031_comparable_attributes'
branch_labels = None
depends_on = None


def upgrade():
    # Frozen definitions: migrations must not depend on future ORM changes.
    uid = sa.String(36).with_variant(PG_UUID(as_uuid=True), 'postgresql')
    op.add_column('properties', sa.Column('is_demo', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_index('ix_properties_is_demo', 'properties', ['is_demo'])
    op.create_table('portfolios',
        sa.Column('id', uid, primary_key=True),
        sa.Column('created_by', uid, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('owner_entity', sa.String(255)), sa.Column('fund', sa.String(255)), sa.Column('asset_manager', sa.String(255)),
        sa.Column('settings', sa.JSON(), nullable=False), sa.Column('official_nav_sar', sa.Float()),
        sa.Column('is_demo', sa.Boolean(), nullable=False), sa.Column('last_checked_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), nullable=False), sa.Column('updated_at', sa.DateTime(), nullable=False))
    op.create_index('ix_portfolios_created_by', 'portfolios', ['created_by'])
    op.create_table('portfolio_assets',
        sa.Column('id', uid, primary_key=True),
        sa.Column('portfolio_id', uid, sa.ForeignKey('portfolios.id'), nullable=False),
        sa.Column('property_id', uid, sa.ForeignKey('properties.id'), nullable=False),
        sa.Column('ownership_pct', sa.Float(), nullable=False),
        sa.Column('acquisition_cost_sar', sa.Float()), sa.Column('acquisition_date', sa.Date()),
        sa.Column('book_value_sar', sa.Float()), sa.Column('debt_sar', sa.Float()),
        sa.Column('monitoring_frequency', sa.String(20), nullable=False), sa.Column('formal_frequency', sa.String(20), nullable=False),
        sa.Column('next_formal_on', sa.Date()), sa.Column('formal_requested_at', sa.DateTime()),
        sa.Column('facts', sa.JSON(), nullable=False), sa.Column('method_weights', sa.JSON()), sa.Column('demo_evidence', sa.JSON()),
        sa.Column('summary', sa.JSON(), nullable=False), sa.Column('priority_score', sa.Float(), nullable=False),
        sa.Column('last_checked_at', sa.DateTime()), sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('portfolio_id', 'property_id', name='uq_portfolio_property'))
    for column in ['portfolio_id', 'property_id', 'priority_score']:
        op.create_index('ix_portfolio_assets_' + column, 'portfolio_assets', [column])
    op.create_table('valuation_snapshots',
        sa.Column('id', uid, primary_key=True),
        sa.Column('property_id', uid, sa.ForeignKey('properties.id'), nullable=False),
        sa.Column('kind', sa.String(20), nullable=False), sa.Column('valued_on', sa.Date(), nullable=False),
        sa.Column('value_sar', sa.Float(), nullable=False), sa.Column('low_sar', sa.Float()), sa.Column('high_sar', sa.Float()),
        sa.Column('confidence', sa.String(10)), sa.Column('trigger', sa.String(50), nullable=False),
        sa.Column('origin', sa.String(20), nullable=False), sa.Column('previous_id', uid, sa.ForeignKey('valuation_snapshots.id')),
        sa.Column('data', sa.JSON(), nullable=False), sa.Column('created_by', uid, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False))
    for column in ['property_id', 'kind', 'valued_on']:
        op.create_index('ix_valuation_snapshots_' + column, 'valuation_snapshots', [column])
    op.create_table('monitor_events',
        sa.Column('id', uid, primary_key=True),
        sa.Column('property_id', uid, sa.ForeignKey('properties.id'), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False), sa.Column('category', sa.String(20), nullable=False),
        sa.Column('occurred_on', sa.Date(), nullable=False), sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('origin', sa.String(20), nullable=False), sa.Column('snapshot_id', uid, sa.ForeignKey('valuation_snapshots.id')),
        sa.Column('details', sa.JSON()), sa.Column('created_by', uid, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False))
    for column in ['property_id', 'occurred_on']:
        op.create_index('ix_monitor_events_' + column, 'monitor_events', [column])
    op.create_table('monitor_alerts',
        sa.Column('id', uid, primary_key=True),
        sa.Column('portfolio_id', uid, sa.ForeignKey('portfolios.id'), nullable=False),
        sa.Column('asset_id', uid, sa.ForeignKey('portfolio_assets.id')),
        sa.Column('kind', sa.String(50), nullable=False), sa.Column('severity', sa.String(10), nullable=False),
        sa.Column('status', sa.String(20), nullable=False), sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False), sa.Column('details', sa.JSON()),
        sa.Column('raised_on', sa.Date(), nullable=False), sa.Column('note', sa.Text()),
        sa.Column('created_at', sa.DateTime(), nullable=False), sa.Column('updated_at', sa.DateTime(), nullable=False))
    for column in ['portfolio_id', 'asset_id', 'status']:
        op.create_index('ix_monitor_alerts_' + column, 'monitor_alerts', [column])


def downgrade():
    op.drop_table('monitor_alerts')
    op.drop_table('monitor_events')
    op.drop_table('valuation_snapshots')
    op.drop_table('portfolio_assets')
    op.drop_table('portfolios')
    op.drop_index('ix_properties_is_demo', 'properties')
    op.drop_column('properties', 'is_demo')
