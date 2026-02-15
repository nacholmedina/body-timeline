"""exercise tracking redesign

Revision ID: d7e8f9a0b1c2
Revises: c61456329be3
Create Date: 2026-02-15 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from app.extensions import GUID


# revision identifiers, used by Alembic.
revision = 'd7e8f9a0b1c2'
down_revision = 'c61456329be3'
branch_labels = None
depends_on = None


def upgrade():
    # ═══════════════════════════════════════════════════════════
    # DROP OLD TABLES (Fresh Start)
    # ═══════════════════════════════════════════════════════════
    op.execute("DROP TABLE IF EXISTS workout_photos CASCADE")
    op.execute("DROP TABLE IF EXISTS workout_items CASCADE")
    op.execute("DROP TABLE IF EXISTS workouts CASCADE")
    op.execute("DROP TABLE IF EXISTS exercise_requests CASCADE")
    op.execute("DROP TABLE IF EXISTS exercises CASCADE")

    # Drop old enum types
    op.execute("DROP TYPE IF EXISTS exercise_type CASCADE")
    op.execute("DROP TYPE IF EXISTS request_status CASCADE")

    # ═══════════════════════════════════════════════════════════
    # CREATE NEW ENUM TYPES
    # ═══════════════════════════════════════════════════════════
    # Enum types will be created automatically by SQLAlchemy when creating tables

    # ═══════════════════════════════════════════════════════════
    # CREATE EXERCISE_DEFINITIONS TABLE
    # ═══════════════════════════════════════════════════════════
    op.create_table(
        'exercise_definitions',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('category', sa.Enum('cardio', 'strength', 'sports', 'flexibility', 'general',
                                       name='exercise_category'), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('allowed_measurements', sa.Text(), nullable=True),
        sa.Column('is_system', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_by', GUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('ix_exercise_definitions_name', 'exercise_definitions', ['name'])
    op.create_index('ix_exercise_definitions_category', 'exercise_definitions', ['category'])
    op.create_index('ix_exercise_defs_category_usage', 'exercise_definitions',
                    ['category', 'is_active', 'usage_count'])

    # ═══════════════════════════════════════════════════════════
    # CREATE EXERCISE_LOGS TABLE
    # ═══════════════════════════════════════════════════════════
    op.create_table(
        'exercise_logs',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('patient_id', GUID(), nullable=False),
        sa.Column('exercise_definition_id', GUID(), nullable=True),
        sa.Column('custom_exercise_name', sa.String(length=200), nullable=True),
        sa.Column('custom_exercise_description', sa.Text(), nullable=True),
        sa.Column('measurements', sa.Text(), nullable=True),
        sa.Column('performed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['patient_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['exercise_definition_id'], ['exercise_definitions.id'],
                                ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_exercise_logs_patient_id', 'exercise_logs', ['patient_id'])
    op.create_index('ix_exercise_logs_performed_at', 'exercise_logs', ['performed_at'])
    op.create_index('ix_exercise_logs_patient_date', 'exercise_logs',
                    ['patient_id', 'performed_at'])
    op.create_index('ix_exercise_logs_exercise_definition_id', 'exercise_logs',
                    ['exercise_definition_id'])

    # ═══════════════════════════════════════════════════════════
    # CREATE EXERCISE_PHOTOS TABLE
    # ═══════════════════════════════════════════════════════════
    op.create_table(
        'exercise_photos',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('exercise_log_id', GUID(), nullable=False),
        sa.Column('storage_key', sa.String(length=500), nullable=False),
        sa.Column('caption', sa.String(length=255), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['exercise_log_id'], ['exercise_logs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_exercise_photos_exercise_log_id', 'exercise_photos',
                    ['exercise_log_id'])

    # ═══════════════════════════════════════════════════════════
    # CREATE EXERCISE_REQUESTS TABLE (New Version)
    # ═══════════════════════════════════════════════════════════
    op.create_table(
        'exercise_requests',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('requested_by', GUID(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('category', sa.Enum('cardio', 'strength', 'sports', 'flexibility', 'general',
                                       name='exercise_category', create_type=False), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('suggested_measurements', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('pending', 'approved', 'rejected',
                                     name='exercise_request_status'), nullable=False,
                  server_default='pending'),
        sa.Column('reviewed_by', GUID(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('created_exercise_id', GUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['requested_by'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_exercise_id'], ['exercise_definitions.id'],
                                ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_exercise_requests_requested_by', 'exercise_requests', ['requested_by'])
    op.create_index('ix_exercise_requests_status', 'exercise_requests', ['status'])
    op.create_index('ix_exercise_requests_status_date', 'exercise_requests',
                    ['status', 'created_at'])


def downgrade():
    # Drop new tables
    op.drop_table('exercise_requests')
    op.drop_table('exercise_photos')
    op.drop_table('exercise_logs')
    op.drop_table('exercise_definitions')

    # Drop new enum types
    op.execute("DROP TYPE IF EXISTS exercise_category")
    op.execute("DROP TYPE IF EXISTS exercise_request_status")

    # Recreate old tables (basic structure - data will be lost)
    op.execute("CREATE TYPE exercise_type AS ENUM ('duration', 'sets_reps', 'both')")
    op.execute("CREATE TYPE request_status AS ENUM ('pending', 'approved', 'rejected')")

    op.create_table(
        'exercises',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('exercise_type', sa.Enum('duration', 'sets_reps', 'both',
                                            name='exercise_type'), nullable=False),
        sa.Column('muscle_group', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    op.create_table(
        'workouts',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('patient_id', GUID(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['patient_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'workout_items',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('workout_id', GUID(), nullable=False),
        sa.Column('exercise_id', GUID(), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('sets', sa.Integer(), nullable=True),
        sa.Column('reps', sa.Integer(), nullable=True),
        sa.Column('weight_kg', sa.Numeric(6, 2), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['workout_id'], ['workouts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['exercise_id'], ['exercises.id']),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'workout_photos',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('workout_id', GUID(), nullable=False),
        sa.Column('storage_key', sa.String(500), nullable=False),
        sa.Column('caption', sa.String(255), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['workout_id'], ['workouts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'exercise_requests',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('requested_by', GUID(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('exercise_type', sa.Enum('duration', 'sets_reps', 'both',
                                            name='exercise_type', create_type=False), nullable=False),
        sa.Column('status', sa.Enum('pending', 'approved', 'rejected',
                                     name='request_status'), nullable=False),
        sa.Column('reviewed_by', GUID(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_exercise_id', GUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['requested_by'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id']),
        sa.ForeignKeyConstraint(['created_exercise_id'], ['exercises.id']),
        sa.PrimaryKeyConstraint('id')
    )
