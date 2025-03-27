#!/usr/bin/env python3
"""
Script to create the account_rankings table in the database.
This is part of the integration with the logic-service.
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

# Add parent directory to path so we can import database module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import get_connection

def create_rankings_table():
    """Create the account_rankings table and related indexes in the database"""
    print("Creating account_rankings table...")
    
    # Get database connection
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Read the SQL file
        script_dir = os.path.dirname(os.path.abspath(__file__))
        sql_file = os.path.join(script_dir, 'create_rankings_table.sql')
        
        with open(sql_file, 'r') as f:
            sql_script = f.read()
        
        # Execute the SQL script
        cur.execute(sql_script)
        conn.commit()
        
        # Verify table creation
        cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'account_rankings')")
        table_exists = cur.fetchone()[0]
        
        if table_exists:
            print("✅ account_rankings table created successfully")
        else:
            print("❌ Failed to create account_rankings table")
            return False
        
        # Verify indexes
        cur.execute("""
            SELECT indexname FROM pg_indexes 
            WHERE tablename = 'account_rankings' 
            AND indexname IN ('idx_account_rankings_username', 'idx_account_rankings_snapshot_date')
        """)
        indexes = cur.fetchall()
        index_names = [idx[0] for idx in indexes]
        
        if 'idx_account_rankings_username' in index_names:
            print("✅ Username index created successfully")
        else:
            print("❌ Failed to create username index")
        
        if 'idx_account_rankings_snapshot_date' in index_names:
            print("✅ Snapshot date index created successfully")
        else:
            print("❌ Failed to create snapshot date index")
        
        cur.close()
        conn.close()
        
        return table_exists and len(indexes) == 2
        
    except Exception as e:
        print(f"Error creating account_rankings table: {str(e)}")
        return False

if __name__ == "__main__":
    load_dotenv()
    if create_rankings_table():
        print("✅ Table creation completed successfully")
        sys.exit(0)
    else:
        print("❌ Table creation failed")
        sys.exit(1)