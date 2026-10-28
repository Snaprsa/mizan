"""Add Mizan property, assumption, history and market-evidence tables only.

Revision ID: 20261025_foundation
Revises: 74b32156b97d
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

revision = '20261025_foundation'
down_revision = '74b32156b97d'
branch_labels = None
depends_on = None


def upgrade():
    # Freeze table definitions here: migrations must not depend on future ORM changes.
    uid = sa.String(36).with_variant(PG_UUID(as_uuid=True), 'postgresql')
    op.create_table('properties',
        sa.Column('id', uid, primary_key=True),
        sa.Column('created_by', uid, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('case_id', uid, sa.ForeignKey('cases.id')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('country', sa.String(2), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False),
        sa.Column('locale', sa.String(10), nullable=False),
        sa.Column('city', sa.String(255)), sa.Column('district', sa.String(255)),
        sa.Column('property_type', sa.String(100)), sa.Column('address', sa.Text()),
        sa.Column('plot_number', sa.String(100)), sa.Column('data', sa.JSON(), nullable=False),
        sa.Column('revision', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False))
    for column in ['created_by', 'case_id', 'city', 'district', 'property_type', 'plot_number']:
        op.create_index('ix_properties_' + column, 'properties', [column])
    op.create_table('property_revisions',
        sa.Column('id', uid, primary_key=True),
        sa.Column('property_id', uid, sa.ForeignKey('properties.id'), nullable=False),
        sa.Column('revision', sa.Integer(), nullable=False),
        sa.Column('snapshot', sa.JSON(), nullable=False), sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('created_by', uid, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('property_id', 'revision', name='uq_property_revision'))
    op.create_index('ix_property_revisions_property_id', 'property_revisions', ['property_id'])
    op.create_table('property_assumptions',
        sa.Column('id', uid, primary_key=True),
        sa.Column('property_id', uid, sa.ForeignKey('properties.id'), nullable=False),
        sa.Column('key', sa.String(100), nullable=False), sa.Column('data', sa.JSON(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('property_id', 'key', name='uq_property_assumption'))
    op.create_index('ix_property_assumptions_property_id', 'property_assumptions', ['property_id'])
    op.create_table('data_sources',
        sa.Column('id', uid, primary_key=True),
        sa.Column('created_by', uid, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False), sa.Column('provider', sa.String(100), nullable=False),
        sa.Column('source_type', sa.String(50), nullable=False), sa.Column('uri', sa.Text()),
        sa.Column('notes', sa.Text()), sa.Column('created_at', sa.DateTime(), nullable=False))
    op.create_index('ix_data_sources_created_by', 'data_sources', ['created_by'])
    op.create_table('market_observations',
        sa.Column('id', uid, primary_key=True),
        sa.Column('data_source_id', uid, sa.ForeignKey('data_sources.id'), nullable=False),
        sa.Column('external_id', sa.String(255), nullable=False), sa.Column('observed_on', sa.String(10), nullable=False),
        sa.Column('country', sa.String(2), nullable=False), sa.Column('city', sa.String(255), nullable=False),
        sa.Column('district', sa.String(255)), sa.Column('property_type', sa.String(100), nullable=False),
        sa.Column('metric', sa.String(100), nullable=False), sa.Column('unit', sa.String(50), nullable=False),
        sa.Column('raw_value', sa.JSON(), nullable=False), sa.Column('normalized_value', sa.JSON(), nullable=False),
        sa.Column('reliability', sa.Integer(), nullable=False), sa.Column('details', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('data_source_id', 'external_id', name='uq_market_source_record'))
    for column in ['data_source_id', 'observed_on', 'city', 'metric']:
        op.create_index('ix_market_observations_' + column, 'market_observations', [column])


def downgrade():
    for name in ['market_observations', 'data_sources', 'property_assumptions', 'property_revisions', 'properties']:
        op.drop_table(name)
