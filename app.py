from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
from typing import List, Optional
import os
import requests
import json
from bs4 import BeautifulSoup
from datetime import datetime
import psycopg2
from database import get_connection
from smartproxy_config import get_smartproxy_proxies, get_smartproxy_api_headers
from dotenv import load_dotenv
import uvicorn

load_dotenv()
app = FastAPI()

def get_profile_data(username: str) -> dict:
    """
    Get Instagram profile data using SmartProxy's Scraper API
    Returns a dictionary with follower_count, profile_pic_url, full_name, and biography
    """
    print(f"Fetching data for {username} using SmartProxy Scraper API")
    
    default_result = {
        "follower_count": -1,
        "profile_pic_url": "",
        "full_name": "",
        "biography": ""
    }
    
    try:
        # Use SmartProxy's Scraper API directly
        api_url = "https://scraper-api.smartproxy.com/v2/scrape"
        headers = get_smartproxy_api_headers()
        
        payload = {
            "target": "instagram_graphql_profile",
            "query": username
        }
        
        print(f"Sending request to SmartProxy API for {username}")
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        print(f"SmartProxy API response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Error from SmartProxy API: {response.text}")
            return default_result
            
        try:
            data = response.json()
            print(f"Response data keys: {list(data.keys())}")
            
            # Parse the response data
            if "results" in data and len(data["results"]) > 0:
                result = data["results"][0]
                if "content" in result and "data" in result["content"]:
                    content_data = result["content"]["data"]
                    if "user" in content_data:
                        user_data = content_data["user"]
                        
                        # Initialize result with default values
                        profile_result = default_result.copy()
                        
                        # Extract follower count
                        if "edge_followed_by" in user_data and "count" in user_data["edge_followed_by"]:
                            profile_result["follower_count"] = user_data["edge_followed_by"]["count"]
                            print(f"Found follower count: {profile_result['follower_count']}")
                        
                        # Extract profile picture URL
                        if "profile_pic_url_hd" in user_data:
                            profile_result["profile_pic_url"] = user_data["profile_pic_url_hd"]
                        elif "profile_pic_url" in user_data:
                            profile_result["profile_pic_url"] = user_data["profile_pic_url"]
                        
                        # Extract full name
                        if "full_name" in user_data:
                            profile_result["full_name"] = user_data["full_name"]
                        
                        # Extract biography
                        if "biography" in user_data:
                            profile_result["biography"] = user_data["biography"]
                        
                        print(f"Successfully extracted profile data for {username}")
                        return profile_result
            
            # Log more detailed info about the structure if we couldn't find all the data
            print("Could not find all profile data in expected path. Debugging response structure:")
            if "results" in data and len(data["results"]) > 0:
                result = data["results"][0]
                if "content" in result and "data" in result["content"] and "user" in result["content"]["data"]:
                    user = result["content"]["data"]["user"]
                    print(f"User data keys: {list(user.keys())}")
                    
                    # Try to find follower count in various locations
                    follower_keys = [k for k in user.keys() if "follow" in k.lower()]
                    if follower_keys:
                        print(f"Potential follower keys: {follower_keys}")
                        for key in follower_keys:
                            if isinstance(user[key], dict) and "count" in user[key]:
                                default_result["follower_count"] = user[key]["count"]
                                print(f"Found follower count in {key}: {default_result['follower_count']}")
            
            print("Could not extract complete profile data from response")
            return default_result
                
        except json.JSONDecodeError as json_error:
            print(f"Error decoding JSON response: {json_error}")
            print(f"Response content: {response.text[:500]}...")
            return default_result
            
    except Exception as e:
        print(f"Error fetching data for {username}: {str(e)}")
        return default_result

@app.get("/")
async def root():
    return {"message": "Instagram Scraper Service API"}

# Define models for API requests and responses
class Account(BaseModel):
    username: str
    status: Optional[str] = "active"

class AccountList(BaseModel):
    accounts: List[Account]

@app.get("/profiles")
async def get_profiles():
    """Get the latest profile data for all Instagram accounts"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Get latest profile data for each account
        cur.execute("""
            SELECT a.username, p.follower_count, p.profile_pic_url, p.full_name, p.biography, p.checked_at
            FROM instagram_accounts a
            JOIN (
                SELECT DISTINCT ON (account_id) account_id, follower_count, profile_pic_url, full_name, biography, checked_at
                FROM instagram_profiles
                ORDER BY account_id, checked_at DESC
            ) p ON a.id = p.account_id
            WHERE a.status = 'active'
            ORDER BY p.follower_count DESC
        """)
        
        profiles = []
        for row in cur.fetchall():
            profiles.append({
                "username": row[0],
                "follower_count": row[1],
                "profile_pic_url": row[2],
                "full_name": row[3],
                "biography": row[4],
                "checked_at": row[5].isoformat() if row[5] else None
            })
        
        cur.close()
        conn.close()
        
        return {"profiles": profiles}
    except Exception as e:
        print(f"ERROR retrieving profiles: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/scrape-accounts")
def scrape_accounts():
    """
    Triggers scraping of all active Instagram accounts.
    It fetches all accounts from the 'instagram_accounts' table where status is 'active',
    scrapes profile data for each, and then stores the results.
    """
    try:
        print("Starting scraping process...")
        conn = get_connection()
        cur = conn.cursor()
        
        try:
            # Check if the tables exist
            cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'instagram_accounts')")
            accounts_table_exists = cur.fetchone()[0]
            
            cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'instagram_profiles')")
            profiles_table_exists = cur.fetchone()[0]
            
            if not accounts_table_exists:
                print("Table 'instagram_accounts' does not exist. Creating it...")
                # Create the instagram_accounts table if it doesn't exist
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS instagram_accounts (
                        id SERIAL PRIMARY KEY,
                        username VARCHAR(255) NOT NULL,
                        status VARCHAR(50) DEFAULT 'active',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Insert sample accounts for testing
                sample_accounts = ["nba", "kingjames", "nike", "cristiano"]
                for account in sample_accounts:
                    cur.execute("INSERT INTO instagram_accounts (username) VALUES (%s)", (account,))
                
                conn.commit()
                print(f"Table created and sample accounts added: {', '.join(sample_accounts)}")
            
            if not profiles_table_exists:
                print("Table 'instagram_profiles' does not exist. Creating it...")
                # Create a comprehensive profiles table that stores all profile data
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS instagram_profiles (
                        id SERIAL PRIMARY KEY,
                        account_id INTEGER REFERENCES instagram_accounts(id),
                        follower_count INTEGER,
                        profile_pic_url TEXT,
                        full_name VARCHAR(255),
                        biography TEXT,
                        checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
                print("Profiles table created.")
                
        except Exception as setup_error:
            print(f"Error setting up database: {setup_error}")
            # Continue execution even if setup failed - tables may already exist
        
        # Retrieve all active accounts
        print("Fetching active accounts...")
        cur.execute("SELECT id, username FROM instagram_accounts WHERE status='active'")
        accounts = cur.fetchall()
        
        if not accounts:
            print("No active accounts found.")
            return {"message": "No active accounts found."}

        print(f"Found {len(accounts)} active accounts. Starting to scrape...")
        for account_id, username in accounts:
            print(f"Processing account {username} (ID: {account_id})...")
            profile_data = get_profile_data(username)
            
            if profile_data["follower_count"] == -1:
                print(f"Skipping {username} due to an error during scraping.")
                continue
                
            # Insert the scraped data into the database
            print(f"Saving profile data for {username}...")
            cur.execute(
                """
                INSERT INTO instagram_profiles 
                (account_id, follower_count, profile_pic_url, full_name, biography, checked_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    account_id, 
                    profile_data["follower_count"],
                    profile_data["profile_pic_url"],
                    profile_data["full_name"],
                    profile_data["biography"],
                    datetime.now()
                )
            )
            conn.commit()
            print(f"Successfully processed {username}")
            
        cur.close()
        conn.close()
        print("Scraping process completed successfully!")
        return {"message": "Scraping completed successfully."}
    except Exception as e:
        print(f"ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/accounts")
async def add_accounts(account_list: AccountList):
    """Add new Instagram accounts to be scraped"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Ensure the accounts table exists
        cur.execute("""
            CREATE TABLE IF NOT EXISTS instagram_accounts (
                id SERIAL PRIMARY KEY,
                username VARCHAR(255) NOT NULL UNIQUE,
                status VARCHAR(50) DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        added_accounts = []
        skipped_accounts = []
        
        for account in account_list.accounts:
            try:
                # Check if account already exists
                cur.execute("SELECT id FROM instagram_accounts WHERE username = %s", (account.username,))
                existing = cur.fetchone()
                
                if existing:
                    # Update status if the account exists
                    cur.execute(
                        "UPDATE instagram_accounts SET status = %s WHERE username = %s",
                        (account.status, account.username)
                    )
                    skipped_accounts.append({"username": account.username, "reason": "Account already exists, status updated"})
                else:
                    # Insert new account
                    cur.execute(
                        "INSERT INTO instagram_accounts (username, status) VALUES (%s, %s)",
                        (account.username, account.status)
                    )
                    added_accounts.append(account.username)
                
                conn.commit()
            except Exception as e:
                conn.rollback()
                skipped_accounts.append({"username": account.username, "reason": str(e)})
        
        cur.close()
        conn.close()
        
        return {
            "message": f"Added {len(added_accounts)} new accounts, skipped {len(skipped_accounts)}",
            "added": added_accounts,
            "skipped": skipped_accounts
        }
    except Exception as e:
        print(f"ERROR adding accounts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/accounts")
async def list_accounts():
    """List all Instagram accounts in the database"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, username, status, created_at 
            FROM instagram_accounts 
            ORDER BY created_at DESC
        """)
        
        accounts = []
        for row in cur.fetchall():
            accounts.append({
                "id": row[0],
                "username": row[1],
                "status": row[2],
                "created_at": row[3].isoformat() if row[3] else None
            })
        
        cur.close()
        conn.close()
        
        return {"accounts": accounts}
    except Exception as e:
        print(f"ERROR listing accounts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)