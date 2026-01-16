
CREATE TABLE IF NOT EXISTS goals (
    goal_id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))) ,
    owner_user_id TEXT NOT NULL,
    title TEXT NOT NULL,
    target_hours REAL,
    start_date TEXT,
    end_date TEXT,
    hourly_rate REAL,
    description TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

