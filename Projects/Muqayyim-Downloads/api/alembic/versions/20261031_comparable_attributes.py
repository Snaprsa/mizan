"""Add optional structured attributes to comparables (floor, position, grade, ...).

Revision ID: 20261031_comparable_attributes
Revises: 20261025_foundation
"""
from alembic import op
import sqlalchemy as sa

revision = '20261031_comparable_attributes'
down_revision = '20261025_foundation'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('comparables', sa.Column('attributes', sa.JSON(), nullable=True))


def downgrade():
    op.drop_column('comparables', 'attributes')
