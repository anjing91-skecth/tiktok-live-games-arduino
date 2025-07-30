#!/usr/bin/env python3
"""
Fix TikTok Games Database - Update the correct database used by server
"""
import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from src.core.database_manager import DatabaseManager

def main():
    """Fix tiktok_games.db which is used by the server"""
    print("🔧 Fixing TikTok Games Database")
    print("="*40)
    
    # Use the database that server actually uses
    db_manager = DatabaseManager("database/tiktok_games.db")
    
    try:
        print("📋 Current accounts in tiktok_games.db:")
        accounts = db_manager.get_all_accounts()
        for acc in accounts:
            print(f"  ID: {acc['id']}, Username: {acc['username']}")
        
        print("\n🔧 Updating accounts...")
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Update account ID 1 to rhianladiku19
            cursor.execute("""
                UPDATE accounts 
                SET username = ?, display_name = ?
                WHERE id = 1
            """, ("rhianladiku19", "Rhianladiku19"))
            
            print("✅ Account ID 1 updated to rhianladiku19")
            
            # Make sure account ID 2 is ayhiefachri
            cursor.execute("""
                UPDATE accounts 
                SET username = ?, display_name = ?
                WHERE id = 2
            """, ("ayhiefachri", "Ayhiefachri"))
            
            print("✅ Account ID 2 confirmed as ayhiefachri")
            
            conn.commit()
        
        print("\n📋 Updated accounts in tiktok_games.db:")
        accounts = db_manager.get_all_accounts()
        for acc in accounts:
            print(f"  ID: {acc['id']}, Username: {acc['username']}")
        
        print("\n🎉 TikTok Games Database fixed!")
        print("💡 Server should now use correct usernames")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
