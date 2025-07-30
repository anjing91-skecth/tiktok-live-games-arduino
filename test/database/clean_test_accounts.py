"""
Clean test accounts untuk fresh testing
"""

import sys
import os
sys.path.append('src')

from core.database_manager import DatabaseManager

def clean_test_accounts():
    """Clean up test accounts"""
    try:
        db = DatabaseManager()
        db.initialize_database()
        
        # Get all accounts
        accounts = db.get_all_accounts()
        print(f"Current accounts: {len(accounts)}")
        
        # Delete test accounts
        for acc in accounts:
            if acc['username'] in ['newuser123', 'testuser2']:
                print(f"Deleting: {acc['username']}")
                db.delete_account(acc['id'])
        
        # Show remaining
        remaining = db.get_all_accounts()
        print(f"\nRemaining accounts: {len(remaining)}")
        for acc in remaining:
            print(f"   - {acc['username']} ({acc['display_name']})")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    clean_test_accounts()
