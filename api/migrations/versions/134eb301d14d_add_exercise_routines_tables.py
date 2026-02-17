"""add exercise routines tables

Revision ID: 134eb301d14d
Revises: 540bcab28f6a
Create Date: 2026-02-16 22:26:16.969887
"""
from alembic import op
import sqlalchemy as sa


revision = '134eb301d14d'
down_revision = '540bcab28f6a'
branch_labels = None
depends_on = None


def upgrade():
    # Create exercise_routines table
    op.create_table(
        'exercise_routines',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('patient_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'))
    )

    # Create index for exercise_routines
    op.create_index('ix_exercise_routines_patient', 'exercise_routines', ['patient_id', 'is_active'])

    # Create exercise_routine_items table
    op.create_table(
        'exercise_routine_items',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('routine_id', sa.String(36), sa.ForeignKey('exercise_routines.id', ondelete='CASCADE'), nullable=False),
        sa.Column('exercise_definition_id', sa.String(36), sa.ForeignKey('exercise_definitions.id'), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('default_measurements', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True)
    )

    # Create index for exercise_routine_items
    op.create_index('ix_exercise_routine_items_routine', 'exercise_routine_items', ['routine_id'])


def downgrade():
    op.drop_index('ix_exercise_routine_items_routine', table_name='exercise_routine_items')
    op.drop_table('exercise_routine_items')
    op.drop_index('ix_exercise_routines_patient', table_name='exercise_routines')
    op.drop_table('exercise_routines')
