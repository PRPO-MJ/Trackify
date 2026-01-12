-- -----------------------------------------------------
-- USERS
-- -----------------------------------------------------
CREATE USER user_service WITH PASSWORD 'user_service123!';
CREATE USER goals_service WITH PASSWORD 'goals_service123!';
CREATE USER mail_service WITH PASSWORD 'mail_service123!';
CREATE USER entries_service WITH PASSWORD 'entries_service123!';

-- -----------------------------------------------------
-- DATABASES
-- -----------------------------------------------------
CREATE DATABASE trackify_user OWNER user_service;
CREATE DATABASE trackify_goals OWNER goals_service;
CREATE DATABASE trackify_mail OWNER mail_service;
CREATE DATABASE trackify_entries OWNER entries_service;

-- =====================================================
-- USER SERVICE DATABASE
-- =====================================================
\c trackify_user

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE users (
    google_sub TEXT PRIMARY KEY,  
    google_email TEXT NOT NULL,   
    full_name TEXT NOT NULL, 
    address TEXT,
    country TEXT,
    phone TEXT,
    currency TEXT,                     
    timezone TEXT,                     
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

GRANT SELECT, INSERT, UPDATE, DELETE ON users TO user_service;

-- =====================================================
-- GOALS SERVICE DATABASE
-- =====================================================
\c trackify_goals

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE goals (
    goal_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    owner_user_id TEXT NOT NULL,
    title TEXT NOT NULL,
    target_hours NUMERIC,
    start_date DATE,
    end_date DATE,
    hourly_rate NUMERIC,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_goals_owner ON goals(owner_user_id);

GRANT SELECT, INSERT, UPDATE, DELETE ON goals TO goals_service;

-- =====================================================
-- MAIL SERVICE DATABASE
-- =====================================================
\c trackify_mail

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE mails (
    mail_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    owner_user_id TEXT NOT NULL,
    related_goal_id UUID,
    recipient TEXT NOT NULL,
    subject TEXT,
    body TEXT,
    pdf_url TEXT,
    sent_when NUMERIC, 
    enabled BOOLEAN NOT NULL DEFAULT FALSE,
    status TEXT DEFAULT 'pending',
    error_message TEXT,
    last_sent_at TIMESTAMPTZ,
    sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_mails_owner ON mails(owner_user_id);
CREATE INDEX idx_mails_goal ON mails(related_goal_id);
CREATE INDEX idx_mails_enabled ON mails(enabled);
CREATE INDEX idx_mails_sent_when ON mails(sent_when);
CREATE INDEX idx_mails_status ON mails(status);

GRANT SELECT, INSERT, UPDATE, DELETE ON mails TO mail_service;

-- =====================================================
-- TIME ENTRIES SERVICE DATABASE
-- =====================================================
\c trackify_entries

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE time_entries (
    entry_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    owner_user_id TEXT NOT NULL,
    related_goal_id UUID,
    work_date DATE,
    start_time TIME,
    end_time TIME,
    minutes NUMERIC,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_time_entries_owner ON time_entries(owner_user_id);
CREATE INDEX idx_time_entries_goal ON time_entries(related_goal_id);

GRANT SELECT, INSERT, UPDATE, DELETE ON time_entries TO entries_service;

