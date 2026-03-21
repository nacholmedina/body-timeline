-- Migration: Professional Availability & Patient Self-Booking
-- Date: 2026-03-20
-- Note: users.id is VARCHAR(36), not UUID (GUID custom type)

DO $$ BEGIN
    CREATE TYPE override_type AS ENUM ('block', 'extra');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS professional_availability (
    id VARCHAR(36) PRIMARY KEY,
    professional_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    day_of_week INTEGER NOT NULL CHECK (day_of_week >= 0 AND day_of_week <= 6),
    start_time VARCHAR(5) NOT NULL,
    end_time VARCHAR(5) NOT NULL,
    slot_duration_minutes INTEGER NOT NULL DEFAULT 30,
    booking_window_days INTEGER NOT NULL DEFAULT 30,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_prof_availability_dow UNIQUE (professional_id, day_of_week)
);

CREATE INDEX IF NOT EXISTS ix_professional_availability_prof
    ON professional_availability(professional_id, is_active);

CREATE TABLE IF NOT EXISTS availability_overrides (
    id VARCHAR(36) PRIMARY KEY,
    professional_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    override_date DATE NOT NULL,
    override_type override_type NOT NULL,
    start_time VARCHAR(5),
    end_time VARCHAR(5),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_availability_overrides_prof_date
    ON availability_overrides(professional_id, override_date);

-- Add booking_source to appointments
ALTER TABLE appointments
    ADD COLUMN IF NOT EXISTS booking_source VARCHAR(20) NOT NULL DEFAULT 'professional';

-- Rollback:
-- ALTER TABLE appointments DROP COLUMN IF EXISTS booking_source;
-- DROP TABLE IF EXISTS availability_overrides CASCADE;
-- DROP TABLE IF EXISTS professional_availability CASCADE;
-- DROP TYPE IF EXISTS override_type;
