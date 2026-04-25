-- Migration: Add is_online_only flag to professional_availability
-- Date: 2026-04-25
-- Lets professionals mark recurring weekly intervals as online-only,
-- so the booking page can show those slots are video-only.

ALTER TABLE professional_availability
    ADD COLUMN IF NOT EXISTS is_online_only BOOLEAN NOT NULL DEFAULT FALSE;

-- Rollback:
-- ALTER TABLE professional_availability DROP COLUMN IF EXISTS is_online_only;
