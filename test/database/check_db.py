#!/usr/bin/env python3
"""
Check Database Content
"""
import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from src.core.database_manager import DatabaseManager

def main():
    """Check database content"""
    print("🔍 Database Content Check")
    print("="*30)
    
    db_manager = DatabaseManager()
    
    try:
        accounts = db_manager.get_all_accounts()
        print(f"📋 Found {len(accounts)} accounts:")
        
        for acc in accounts:
            print(f"  ID: {acc['id']}, Username: '{acc['username']}', Display: '{acc.get('display_name', '')}'")
        
        # Check if there's a caching issue
        print(f"\n🔍 Detailed check for account ID 1:")
        account_1 = db_manager.get_account(1)
        if account_1:
            print(f"  Direct query result: {account_1}")
        else:
            print("  Account ID 1 not found!")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
