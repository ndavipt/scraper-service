# Account Rankings Scripts

These scripts create and populate the `account_rankings` table for integration with the logic service.

## Overview

The account rankings functionality allows Instagram accounts to be ranked based on their follower counts.
The logic service will handle the API endpoints and the daily ranking updates.

## Setup Process

Run these scripts in the following order:

1. Create rankings table:
```bash
python scripts/create_rankings_table.py
```

2. Populate initial ranking data:
```bash
python scripts/populate_rankings.py
```

3. Verify the rankings (optional):
```bash
python scripts/verify_rankings.py
```

## File Descriptions

- `create_rankings_table.sql` - SQL script for creating the rankings table and indexes
- `create_rankings_table.py` - Python script that executes the SQL and verifies the table creation
- `populate_rankings.sql` - SQL script that populates the initial ranking data
- `populate_rankings.py` - Python script that executes the population SQL and shows results
- `verify_rankings.py` - Python script that validates the table structure and data integrity

## Dependencies

These scripts require:
- PostgreSQL database connection
- Python 3.6+
- tabulate (for verify_rankings.py)

The dependencies are listed in the project's requirements.txt file.

## Notes

- The ranking is based on follower counts, with rank 1 having the highest follower count
- No API endpoints are implemented in the scraper service for rankings
- The logic service will handle all ranking-related API functionality
- A cron job is already set up by the logic service to update rankings daily