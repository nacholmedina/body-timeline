-- Add email verification and OAuth fields to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN NOT NULL DEFAULT TRUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS oauth_provider VARCHAR(50);
ALTER TABLE users ADD COLUMN IF NOT EXISTS oauth_id VARCHAR(255);
ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL;

-- Existing users are marked as verified (default TRUE above)
-- New registrations will set email_verified=FALSE explicitly

-- Index for OAuth lookups
CREATE INDEX IF NOT EXISTS idx_users_oauth ON users (oauth_provider, oauth_id);
