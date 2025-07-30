#!/usr/bin/env python3
"""
Clean TikTok Games Database - Remove duplicates and fix accounts
"""
import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from src.core.database_manager import DatabaseManager

def main():
    """Clean and fix tiktok_games.db"""
    print("🧹 Cleaning TikTok Games Database")
    print("="*40)
    
    db_manager = DatabaseManager("database/tiktok_games.db")
    
    try:
        print("📋 Current accounts:")
        accounts = db_manager.get_all_accounts()
        for acc in accounts:
            print(f"  ID: {acc['id']}, Username: {acc['username']}")
        
        print("\n🧹 Cleaning database...")
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Delete all accounts first to avoid conflicts
            cursor.execute("DELETE FROM accounts")
            print("✅ Cleared all accounts")
            
            # Insert target accounts with correct IDs
            cursor.execute("""
                INSERT INTO accounts (id, username, display_name, arduino_port, status, created_at)
                VALUES (1, 'rhianladiku19', 'Rhianladiku19', NULL, 'inactive', datetime('now'))
            """)
            print("✅ Added rhianladiku19 as ID 1")
            
            cursor.execute("""
                INSERT INTO accounts (id, username, display_name, arduino_port, status, created_at)
                VALUES (2, 'ayhiefachri', 'Ayhiefachri', NULL, 'inactive', datetime('now'))
            """)
            print("✅ Added ayhiefachri as ID 2")
            
            conn.commit()
        
        print("\n📋 Final accounts:")
        accounts = db_manager.get_all_accounts()
        for acc in accounts:
            print(f"  ID: {acc['id']}, Username: {acc['username']}")
        
        print("\n🎉 Database cleaned and ready!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
