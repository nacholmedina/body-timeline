"""add gender to users

Revision ID: b3f1a2c8d9e0
Revises: ea73dc6a59d0
Create Date: 2026-02-14 20:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = 'b3f1a2c8d9e0'
down_revision = 'ea73dc6a59d0'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('gender', sa.String(20), nullable=True))


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('gender')
