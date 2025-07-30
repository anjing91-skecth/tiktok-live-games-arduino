"""
Setup test data untuk aplikasi desktop
Menambahkan account test dan konfigurasi basic
"""

import sys
import os
sys.path.append('src')

from core.database_manager import DatabaseManager

def setup_test_data():
    """Setup data testing untuk aplikasi"""
    try:
        db = DatabaseManager()
        db.initialize_database()
        
        print("Setting up test data...")
        
        # Add test account
        try:
            account_id = db.create_account("rhianladiku19", "Rhian Test Account", "COM3")
            print(f"✅ Added test account: rhianladiku19 (ID: {account_id})")
            
        except Exception as e:
            print(f"Account rhianladiku19 may already exist: {e}")
            
        try:
            account_id2 = db.create_account("testuser2", "Test User 2", "COM4")
            print(f"✅ Added test account: testuser2 (ID: {account_id2})")
            
        except Exception as e:
            print(f"Account testuser2 may already exist: {e}")
        
        # Test database connection
        accounts = db.get_all_accounts()
        print(f"\n📋 Total accounts in database: {len(accounts)}")
        for acc in accounts:
            print(f"   - {acc['username']} ({acc['display_name']}) - Port: {acc['arduino_port']} - Status: {acc['status']}")
        
        print("\n✅ Test data setup complete!")
        
    except Exception as e:
        print(f"❌ Error setting up test data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    setup_test_data()
