-- Migration: Google Calendar integration
-- Date: 2026-04-25
-- Adds tokens table for the per-user Google Calendar OAuth connection,
-- and google_event_id on appointments to track synced events.

CREATE TABLE IF NOT EXISTS google_calendar_tokens (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    access_token TEXT NOT NULL,
    refresh_token TEXT NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    scope TEXT NOT NULL,
    calendar_id VARCHAR(255) NOT NULL DEFAULT 'primary',
    google_email VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_google_calendar_tokens_user
    ON google_calendar_tokens(user_id);

ALTER TABLE appointments
    ADD COLUMN IF NOT EXISTS google_event_id VARCHAR(255);

CREATE INDEX IF NOT EXISTS ix_appointments_google_event
    ON appointments(google_event_id);

-- Rollback:
-- DROP INDEX IF EXISTS ix_appointments_google_event;
-- ALTER TABLE appointments DROP COLUMN IF EXISTS google_event_id;
-- DROP INDEX IF EXISTS ix_google_calendar_tokens_user;
-- DROP TABLE IF EXISTS google_calendar_tokens CASCADE;
