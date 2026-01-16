
CREATE TABLE IF NOT EXISTS mails (
    mail_id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))) ,
    owner_user_id TEXT NOT NULL,
    related_goal_id TEXT,
    recipient TEXT NOT NULL,
    subject TEXT,
    body TEXT,
    pdf_url TEXT,
    sent_when REAL,
    enabled INTEGER NOT NULL DEFAULT 0,
    status TEXT DEFAULT 'pending',
    error_message TEXT,
    last_sent_at TEXT,
    sent_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

