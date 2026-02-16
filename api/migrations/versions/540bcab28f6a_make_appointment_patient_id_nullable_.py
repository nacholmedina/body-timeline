"""make appointment patient_id nullable for non-registered patients

Revision ID: 540bcab28f6a
Revises: d7e8f9a0b1c2
Create Date: 2026-02-16 17:46:41.158016
"""
from alembic import op
import sqlalchemy as sa


revision = '540bcab28f6a'
down_revision = 'd7e8f9a0b1c2'
branch_labels = None
depends_on = None


def upgrade():
    # Make patient_id nullable to support appointments with non-registered patients
    op.alter_column('appointments', 'patient_id',
                    existing_type=sa.UUID(),
                    nullable=True)


def downgrade():
    # Revert patient_id back to NOT NULL
    op.alter_column('appointments', 'patient_id',
                    existing_type=sa.UUID(),
                    nullable=False)
