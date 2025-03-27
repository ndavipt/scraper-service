#!/usr/bin/env python3
"""
Script to populate the account_rankings table with initial data.
This ranks accounts based on follower count from the most recent profile data.
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

# Add parent directory to path so we can import database module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import get_connection

def populate_rankings():
    """Populate the account_rankings table with initial ranking data"""
    print("Populating account_rankings table with initial data...")
    
    # Get database connection
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # First check if the table exists
        cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'account_rankings')")
        if not cur.fetchone()[0]:
            print("❌ The account_rankings table does not exist. Please run create_rankings_table.py first.")
            return False
        
        # Read the SQL file
        script_dir = os.path.dirname(os.path.abspath(__file__))
        sql_file = os.path.join(script_dir, 'populate_rankings.sql')
        
        with open(sql_file, 'r') as f:
            sql_script = f.read()
        
        # Execute the SQL script
        cur.execute(sql_script)
        
        # Get number of affected rows
        affected_rows = cur.rowcount
        conn.commit()
        
        # Verify data was inserted
        cur.execute("SELECT COUNT(*) FROM account_rankings")
        count = cur.fetchone()[0]
        
        print(f"✅ Populated {affected_rows} account rankings successfully")
        print(f"Total records in account_rankings table: {count}")
        
        # Get top 5 ranked accounts for verification
        cur.execute("""
            SELECT username, follower_count, rank 
            FROM account_rankings 
            ORDER BY rank ASC 
            LIMIT 5
        """)
        
        print("\nTop 5 ranked accounts:")
        for row in cur.fetchall():
            print(f"Rank {row[2]}: {row[0]} with {row[1]} followers")
        
        cur.close()
        conn.close()
        
        return affected_rows > 0
        
    except Exception as e:
        print(f"Error populating account_rankings: {str(e)}")
        return False

if __name__ == "__main__":
    load_dotenv()
    if populate_rankings():
        print("✅ Initial ranking data population completed successfully")
        sys.exit(0)
    else:
        print("❌ Initial ranking data population failed")
        sys.exit(1)