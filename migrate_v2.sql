-- Keikenchi v3: personal accounts (username + password), cloud achievements/notes/dates.
-- Apply once to an existing DB:  wrangler d1 execute keikenchi --remote --file migrate_v2.sql

CREATE TABLE IF NOT EXISTS users (
  id         TEXT PRIMARY KEY,
  username   TEXT UNIQUE NOT NULL,
  pass_hash  TEXT NOT NULL,      -- PBKDF2-SHA256 hex
  salt       TEXT NOT NULL,      -- hex
  created_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
  token   TEXT PRIMARY KEY,      -- random hex, sent as httpOnly cookie
  user_id TEXT NOT NULL,
  expires INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);

-- link a shareable map to an account, and store rich account data
ALTER TABLE maps ADD COLUMN user_id TEXT;   -- owner account (nullable = anonymous)
ALTER TABLE maps ADD COLUMN extra   TEXT;   -- JSON: {memo:{id:txt}, dates:{id:ts}, ach:[id]}
CREATE INDEX IF NOT EXISTS idx_maps_user ON maps(user_id);
