-- Keikenchi — canonical schema (fresh install).
-- Existing DBs: use migrate_v2.sql instead (it ALTERs the maps table).

CREATE TABLE IF NOT EXISTS users (
  id         TEXT PRIMARY KEY,
  username   TEXT UNIQUE NOT NULL,
  pass_hash  TEXT NOT NULL,
  salt       TEXT NOT NULL,
  created_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
  token   TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  expires INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);

-- A "map" = one shareable board. edit_key is a secret held by the owner
-- (anonymous flow); logged-in users edit via their session instead.
CREATE TABLE IF NOT EXISTS maps (
  id         TEXT PRIMARY KEY,
  edit_key   TEXT NOT NULL,
  user_id    TEXT,                       -- owner account (nullable = anonymous)
  name       TEXT,
  data       TEXT NOT NULL,              -- "<47 scores>-<47 counts b36>"
  extra      TEXT,                       -- JSON: {memo:{}, dates:{}, ach:[]}
  score      INTEGER NOT NULL DEFAULT 0,
  updated_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_maps_user ON maps(user_id);

CREATE TABLE IF NOT EXISTS rooms (
  id         TEXT PRIMARY KEY,
  name       TEXT,
  created_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS room_members (
  room_id   TEXT NOT NULL,
  map_id    TEXT NOT NULL,
  joined_at INTEGER NOT NULL,
  PRIMARY KEY (room_id, map_id)
);
CREATE INDEX IF NOT EXISTS idx_members_room ON room_members(room_id);
