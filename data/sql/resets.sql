-- Password reset links (backend/tracking/auth.py, "Password reset").
--
-- One row per link sent. Only a SHA-256 of the token is kept: the token is
-- the whole credential, so a copy of this table (a backup, an export, a
-- leaked dump) must not be a set of working links. A link is good for an hour
-- and once: using it, or asking for a newer one, marks every earlier one of
-- the account's used.
CREATE TABLE IF NOT EXISTS password_resets (
    token_hash  TEXT PRIMARY KEY,
    user_id     TEXT NOT NULL REFERENCES users (username) ON DELETE CASCADE,
    created_at  TEXT NOT NULL,
    expires_at  TEXT NOT NULL,
    used_at     TEXT
);

CREATE INDEX IF NOT EXISTS password_resets_user_idx ON password_resets (user_id);
