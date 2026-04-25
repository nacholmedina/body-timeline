"""add is_online_only to professional_availability

Revision ID: e8a91b20cf5d
Revises: 134eb301d14d
Create Date: 2026-04-25 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = 'e8a91b20cf5d'
down_revision = '134eb301d14d'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'professional_availability',
        sa.Column('is_online_only', sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade():
    op.drop_column('professional_availability', 'is_online_only')
