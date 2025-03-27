#!/usr/bin/env python3
"""
Script to verify the account_rankings table and its data.
This checks that the table exists, has the correct structure, and contains valid data.
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv
from tabulate import tabulate

# Add parent directory to path so we can import database module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import get_connection

def verify_rankings():
    """Verify the account_rankings table and its data"""
    print("Verifying account_rankings table and data...")
    
    # Get database connection
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Check if the table exists
        cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'account_rankings')")
        if not cur.fetchone()[0]:
            print("❌ The account_rankings table does not exist")
            return False
        
        # Verify table structure
        cur.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'account_rankings'
            ORDER BY ordinal_position
        """)
        
        columns = cur.fetchall()
        expected_columns = {
            'id': 'integer',
            'account_id': 'integer',
            'username': 'character varying',
            'follower_count': 'integer',
            'rank': 'integer',
            'previous_rank': 'integer',
            'position_change': 'integer',
            'snapshot_date': 'timestamp without time zone'
        }
        
        print("\nTable Structure:")
        table_data = []
        all_columns_present = True
        
        for col in columns:
            col_name, col_type = col
            expected_type = expected_columns.get(col_name)
            status = "✅" if expected_type and expected_type in col_type else "❌"
            
            if status == "❌":
                all_columns_present = False
                
            table_data.append([col_name, col_type, status])
        
        print(tabulate(table_data, headers=["Column", "Type", "Status"]))
        
        # Verify data exists
        cur.execute("SELECT COUNT(*) FROM account_rankings")
        count = cur.fetchone()[0]
        
        if count == 0:
            print("\n❌ The account_rankings table has no data")
            return False
        
        print(f"\nFound {count} records in account_rankings table")
        
        # Verify ranking order matches follower count
        cur.execute("""
            SELECT 
                a.username, a.follower_count, a.rank,
                b.username, b.follower_count, b.rank
            FROM 
                account_rankings a
            JOIN 
                account_rankings b ON a.follower_count > b.follower_count AND a.rank > b.rank
            WHERE 
                a.snapshot_date = (SELECT MAX(snapshot_date) FROM account_rankings)
            AND 
                b.snapshot_date = (SELECT MAX(snapshot_date) FROM account_rankings)
            LIMIT 1
        """)
        
        inconsistency = cur.fetchone()
        if inconsistency:
            print("\n❌ Found ranking inconsistency:")
            print(f"  Account '{inconsistency[0]}' has {inconsistency[1]} followers with rank {inconsistency[2]}")
            print(f"  Account '{inconsistency[3]}' has {inconsistency[4]} followers with rank {inconsistency[5]}")
            print("  This violates the rule that higher follower counts should have lower ranks")
            return False
        
        # Show top 10 ranked accounts
        cur.execute("""
            SELECT username, follower_count, rank 
            FROM account_rankings 
            WHERE snapshot_date = (SELECT MAX(snapshot_date) FROM account_rankings)
            ORDER BY rank ASC 
            LIMIT 10
        """)
        
        print("\nTop 10 ranked accounts:")
        top_accounts = []
        for row in cur.fetchall():
            top_accounts.append([row[0], row[1], row[2]])
        
        print(tabulate(top_accounts, headers=["Username", "Followers", "Rank"]))
        
        cur.close()
        conn.close()
        
        return all_columns_present and count > 0 and not inconsistency
        
    except Exception as e:
        print(f"Error verifying account_rankings: {str(e)}")
        return False

if __name__ == "__main__":
    load_dotenv()
    try:
        import tabulate
    except ImportError:
        print("The tabulate package is required. Please install it with 'pip install tabulate'")
        sys.exit(1)
        
    if verify_rankings():
        print("\n✅ Account rankings verification completed successfully")
        sys.exit(0)
    else:
        print("\n❌ Account rankings verification failed")
        sys.exit(1)