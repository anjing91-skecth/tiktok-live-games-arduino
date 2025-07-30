#!/usr/bin/env python3
"""
Fix Database - Update usernames in database
"""
import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from src.core.database_manager import DatabaseManager

def check_database_files():
    """Check all database files"""
    print("� Checking Database Files")
    print("="*40)
    
    db_files = [
        "database/live_games.db",
        "database/tiktok_games.db"
    ]
    
    for db_file in db_files:
        print(f"\n📁 Checking {db_file}:")
        try:
            db_manager = DatabaseManager(db_file)
            accounts = db_manager.get_all_accounts()
            print(f"  Found {len(accounts)} accounts:")
            for acc in accounts:
                print(f"    ID: {acc['id']}, Username: {acc['username']}")
        except Exception as e:
            print(f"  ❌ Error: {e}")

def sync_databases():
    """Sync target accounts to both databases"""
    print("\n🔄 Syncing Target Accounts to All Databases")
    print("="*50)
    
    target_accounts = [
        {"username": "rhianladiku19", "display_name": "Rhianladiku19"},
        {"username": "ayhiefachri", "display_name": "Ayhiefachri"}
    ]
    
    db_files = [
        "database/live_games.db",
        "database/tiktok_games.db"
    ]
    
    for db_file in db_files:
        print(f"\n� Syncing {db_file}:")
        try:
            db_manager = DatabaseManager(db_file)
            
            # Initialize database
            db_manager.initialize_database()
            
            # Get existing accounts
            existing_accounts = db_manager.get_all_accounts()
            existing_usernames = [acc['username'] for acc in existing_accounts]
            
            for i, target in enumerate(target_accounts, 1):
                username = target['username']
                display_name = target['display_name']
                
                if username in existing_usernames:
                    # Update existing account
                    print(f"  🔄 Updating {username}...")
                    with db_manager.get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE accounts 
                            SET username = ?, display_name = ?
                            WHERE id = ?
                        """, (username, display_name, i))
                        conn.commit()
                else:
                    # Create new account
                    print(f"  ➕ Creating {username}...")
                    db_manager.create_account(username, display_name)
                
                print(f"    ✅ {username} ready")
                
        except Exception as e:
            print(f"  ❌ Error syncing {db_file}: {e}")

def main():
    """Fix database usernames and sync all databases"""
    print("🚀 TikTok Live Integration - Database Setup")
    print("="*50)
    
    # Step 1: Check current state
    check_database_files()
    
    # Step 2: Sync databases
    sync_databases()
    
    # Step 3: Verify final state
    print("\n✅ Final Verification:")
    check_database_files()
    
    print(f"\n🎯 Ready for TikTok Live Integration!")
    print("Target accounts: rhianladiku19, ayhiefachri")

if __name__ == "__main__":
    main()
