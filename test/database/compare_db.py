#!/usr/bin/env python3
"""
Ch        print(f"📊 Found {len(accounts)} accounts:")
        for acc in accounts:
            display_name = acc['display_name'] if 'display_name' in acc.keys() and acc['display_name'] else ''
            print(f"  ID: {acc['id']}, Username: '{acc['username']}', Display: '{display_name}'") and sync database files
"""
import sqlite3
import os

def check_database(db_path, name):
    """Check database content"""
    print(f"\n🔍 Checking {name} ({db_path}):")
    
    if not os.path.exists(db_path):
        print(f"❌ File does not exist!")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if accounts table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='accounts'")
        if not cursor.fetchone():
            print("❌ No accounts table found")
            conn.close()
            return
        
        # Get accounts
        cursor.execute("SELECT * FROM accounts ORDER BY id")
        accounts = cursor.fetchall()
        
        print(f"📊 Found {len(accounts)} accounts:")
        for acc in accounts:
            print(f"  ID: {acc['id']}, Username: '{acc['username']}', Display: '{acc.get('display_name', '')}'")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Main function"""
    print("🔍 Database Files Comparison")
    print("="*50)
    
    # Check both database files
    check_database("database/live_games.db", "Live Games DB")
    check_database("database/tiktok_games.db", "TikTok Games DB") 
    
    print(f"\n💡 The application should be using: database/live_games.db")

if __name__ == "__main__":
    main()
