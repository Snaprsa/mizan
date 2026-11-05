"""Recoverable deletion of saved properties: a deleted_at marker, never a row removal.

Revision ID: 20261105_property_deleted_at
Revises: 20261031_mizan_monitor
"""
from alembic import op
import sqlalchemy as sa

revision = '20261105_property_deleted_at'
down_revision = '20261031_mizan_monitor'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('properties', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    op.create_index('ix_properties_deleted_at', 'properties', ['deleted_at'])


def downgrade():
    op.drop_index('ix_properties_deleted_at', table_name='properties')
    op.drop_column('properties', 'deleted_at')
