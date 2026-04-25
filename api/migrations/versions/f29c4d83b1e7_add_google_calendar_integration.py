"""add google calendar integration

Revision ID: f29c4d83b1e7
Revises: e8a91b20cf5d
Create Date: 2026-04-25 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = 'f29c4d83b1e7'
down_revision = 'e8a91b20cf5d'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'google_calendar_tokens',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('access_token', sa.Text(), nullable=False),
        sa.Column('refresh_token', sa.Text(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('scope', sa.Text(), nullable=False),
        sa.Column('calendar_id', sa.String(255), nullable=False, server_default='primary'),
        sa.Column('google_email', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    op.create_index('ix_google_calendar_tokens_user', 'google_calendar_tokens', ['user_id'])

    op.add_column(
        'appointments',
        sa.Column('google_event_id', sa.String(255), nullable=True),
    )
    op.create_index('ix_appointments_google_event', 'appointments', ['google_event_id'])


def downgrade():
    op.drop_index('ix_appointments_google_event', table_name='appointments')
    op.drop_column('appointments', 'google_event_id')
    op.drop_index('ix_google_calendar_tokens_user', table_name='google_calendar_tokens')
    op.drop_table('google_calendar_tokens')
