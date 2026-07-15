-- Keikenchi MVP-2: rooms without login
-- A "map" = one person's saved board. edit_key is a secret held only by the owner.
CREATE TABLE IF NOT EXISTS maps (
  id         TEXT PRIMARY KEY,          -- short public id (share/read)
  edit_key   TEXT NOT NULL,             -- secret; required to update
  name       TEXT,                      -- display name on leaderboard
  data       TEXT NOT NULL,             -- "<47 scores>-<47 counts b36>"
  score      INTEGER NOT NULL DEFAULT 0,-- derived sum, for leaderboard sort
  updated_at INTEGER NOT NULL
);

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
