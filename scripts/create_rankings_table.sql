-- SQL script to create the account_rankings table
-- This table stores ranking information for Instagram accounts

-- Create the rankings table with references to instagram_accounts
CREATE TABLE IF NOT EXISTS account_rankings (
    id SERIAL PRIMARY KEY,
    account_id INTEGER REFERENCES instagram_accounts(id),
    username VARCHAR(255) NOT NULL,
    follower_count INTEGER NOT NULL,
    rank INTEGER NOT NULL,
    previous_rank INTEGER,
    position_change INTEGER,
    snapshot_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_account_snapshot UNIQUE (account_id, snapshot_date)
);

-- Create indexes to improve query performance
CREATE INDEX IF NOT EXISTS idx_account_rankings_username ON account_rankings(username);
CREATE INDEX IF NOT EXISTS idx_account_rankings_snapshot_date ON account_rankings(snapshot_date);