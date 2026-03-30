-- GDPR compliance: add soft-delete support for user accounts
-- When set, the account is pending deletion with a 30-day grace period

ALTER TABLE users ADD COLUMN IF NOT EXISTS pending_deletion_at TIMESTAMPTZ DEFAULT NULL;

-- Index for the cron job that finds expired soft-deleted accounts
CREATE INDEX IF NOT EXISTS idx_users_pending_deletion ON users (pending_deletion_at)
  WHERE pending_deletion_at IS NOT NULL;
