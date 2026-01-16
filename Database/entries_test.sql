
CREATE TABLE IF NOT EXISTS time_entries (
    entry_id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))) ,
    owner_user_id TEXT NOT NULL,
    related_goal_id TEXT,
    work_date TEXT,
    start_time TEXT,
    end_time TEXT,
    minutes REAL,
    description TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
