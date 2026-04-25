"""add body composition and measurement log tables

Revision ID: a4d2e9f3b8c1
Revises: f29c4d83b1e7
Create Date: 2026-04-25 19:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = 'a4d2e9f3b8c1'
down_revision = 'f29c4d83b1e7'
branch_labels = None
depends_on = None


_TABLES = (
    ('body_fat_logs', 'body_fat_pct', sa.Numeric(precision=4, scale=1)),
    ('muscle_mass_logs', 'muscle_mass_kg', sa.Numeric(precision=5, scale=2)),
    ('waist_measurements', 'waist_cm', sa.Numeric(precision=5, scale=1)),
    ('hips_measurements', 'hips_cm', sa.Numeric(precision=5, scale=1)),
    ('neck_measurements', 'neck_cm', sa.Numeric(precision=4, scale=1)),
)


def upgrade():
    for table, value_col, value_type in _TABLES:
        op.create_table(
            table,
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('patient_id', sa.String(length=36), nullable=False),
            sa.Column(value_col, value_type, nullable=False),
            sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['patient_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.create_index(
                batch_op.f(f'ix_{table}_patient_id'), ['patient_id'], unique=False
            )
            batch_op.create_index(
                f'ix_{table}_patient_recorded',
                ['patient_id', 'recorded_at'],
                unique=False,
            )


def downgrade():
    for table, _value_col, _value_type in reversed(_TABLES):
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.drop_index(f'ix_{table}_patient_recorded')
            batch_op.drop_index(batch_op.f(f'ix_{table}_patient_id'))
        op.drop_table(table)
