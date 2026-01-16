CREATE TABLE IF NOT EXISTS users (
    google_sub TEXT PRIMARY KEY,
    google_email TEXT NOT NULL,
    full_name TEXT NOT NULL,
    address TEXT,
    country TEXT,
    phone TEXT,
    currency TEXT,
    timezone TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);