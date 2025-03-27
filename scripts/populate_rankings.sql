-- SQL script to populate initial account rankings data
-- Ranks accounts based on follower count from the most recent profile data

-- Get the latest data for each account
WITH latest_profiles AS (
    SELECT DISTINCT ON (account_id)
        p.account_id,
        a.username,
        p.follower_count,
        p.checked_at
    FROM
        instagram_profiles p
    JOIN
        instagram_accounts a ON p.account_id = a.id
    WHERE
        a.status = 'active'
    ORDER BY
        p.account_id, p.checked_at DESC
),
-- Rank the accounts by follower count
ranked_accounts AS (
    SELECT
        account_id,
        username,
        follower_count,
        ROW_NUMBER() OVER (ORDER BY follower_count DESC) as rank
    FROM
        latest_profiles
)
-- Insert into the rankings table
INSERT INTO account_rankings (
    account_id,
    username,
    follower_count,
    rank,
    snapshot_date
)
SELECT
    account_id,
    username,
    follower_count,
    rank,
    CURRENT_TIMESTAMP
FROM
    ranked_accounts;