#!/usr/bin/env python3
"""
Auto Start Live Sessions - Automatically start sessions for target users
"""
import asyncio
import json
import sys
import time
from pathlib import Path
import aiohttp

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from src.core.database_manager import DatabaseManager

class AutoSessionStarter:
    def __init__(self):
        """Initialize auto session starter"""
        self.db_manager = DatabaseManager()
        self.base_url = "http://localhost:5000"
        self.target_users = ["rhianladiku19", "ayhiefachri"]
        
    def ensure_accounts_exist(self):
        """Ensure target accounts exist in database"""
        print("📋 Checking accounts in database...")
        
        try:
            accounts = self.db_manager.get_all_accounts()
            existing_usernames = [acc['username'] for acc in accounts]
            
            for username in self.target_users:
                if username not in existing_usernames:
                    print(f"💾 Adding {username} to database...")
                    
                    # Use create_account method
                    account_id = self.db_manager.create_account(
                        username=username,
                        display_name=username.title()
                    )
                    
                    print(f"✅ {username} added to database with ID: {account_id}")
                else:
                    print(f"✅ {username} already exists in database")
                    
        except Exception as e:
            print(f"❌ Error managing accounts: {e}")
            # Try to initialize database first
            print("🔧 Attempting to initialize database...")
            try:
                self.db_manager.initialize_database()
                print("✅ Database initialized")
                
                # Retry after initialization
                accounts = self.db_manager.get_all_accounts()
                existing_usernames = [acc['username'] for acc in accounts]
                
                for username in self.target_users:
                    if username not in existing_usernames:
                        print(f"💾 Adding {username} to database...")
                        account_id = self.db_manager.create_account(
                            username=username,
                            display_name=username.title()
                        )
                        print(f"✅ {username} added with ID: {account_id}")
                    else:
                        print(f"✅ {username} already exists")
                        
            except Exception as e2:
                print(f"❌ Failed to initialize database: {e2}")
                raise
    
    async def start_session_via_api(self, username):
        """Start session via API call"""
        print(f"🚀 Starting session for {username}...")
        
        try:
            # Get account ID
            accounts = self.db_manager.get_all_accounts()
            account_id = None
            
            for account in accounts:
                if account['username'] == username:
                    account_id = account['id']
                    break
            
            if not account_id:
                print(f"❌ Account ID not found for {username}")
                return False
            
            print(f"🔍 Found account ID: {account_id} for {username}")
            
            # Make API call to start session
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/api/sessions/start/{account_id}"
                
                print(f"📡 Making API call to: {url}")
                async with session.post(url) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ Session started successfully for {username}")
                        print(f"   Response: {result.get('message', 'No message')}")
                        return True
                    else:
                        try:
                            result = await response.json()
                            error_msg = result.get('error', f'HTTP {response.status}')
                        except:
                            error_msg = f'HTTP {response.status}'
                        
                        print(f"❌ Failed to start session for {username}")
                        print(f"   Error: {error_msg}")
                        return False
                        
        except Exception as e:
            print(f"❌ Exception starting session for {username}: {e}")
            return False
    
    async def check_session_status(self, username):
        """Check if user has active session"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/api/sessions/active"
                
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        active_sessions = data.get('sessions', [])
                        
                        for sess in active_sessions:
                            if sess.get('username') == username and sess.get('status') == 'active':
                                print(f"✅ {username} already has active session")
                                return True
                        
                        return False
                    else:
                        print(f"❌ Failed to check sessions: {response.status}")
                        return False
                        
        except Exception as e:
            print(f"❌ Error checking session status: {e}")
            return False
    
    async def run_auto_start(self):
        """Run automatic session starting"""
        print("🚀 Auto Session Starter")
        print(f"{'='*50}")
        print(f"Target users: {', '.join(self.target_users)}")
        print(f"{'='*50}")
        
        # Step 1: Ensure accounts exist
        self.ensure_accounts_exist()
        
        # Step 2: Wait for server to be ready
        print("\n⏳ Waiting for server to be ready...")
        await asyncio.sleep(3)
        
        # Step 3: Start sessions
        results = {}
        
        for username in self.target_users:
            print(f"\n🎯 Processing {username}...")
            
            # Check if already active
            is_active = await self.check_session_status(username)
            
            if is_active:
                results[username] = 'already_active'
                continue
            
            # Start new session
            success = await self.start_session_via_api(username)
            results[username] = 'started' if success else 'failed'
            
            # Wait between requests
            await asyncio.sleep(2)
        
        # Summary
        print(f"\n{'='*50}")
        print("📊 SESSION START SUMMARY")
        print(f"{'='*50}")
        
        for username, status in results.items():
            if status == 'started':
                print(f"✅ {username}: Session started successfully")
            elif status == 'already_active':
                print(f"🔄 {username}: Session was already active")
            else:
                print(f"❌ {username}: Failed to start session")
        
        successful = sum(1 for status in results.values() if status in ['started', 'already_active'])
        total = len(results)
        
        print(f"\n📊 Total: {successful}/{total} sessions active")
        
        if successful == total:
            print("🎉 All sessions are now active!")
            print("💡 You can monitor them at: http://localhost:5000")
        else:
            print("⚠️ Some sessions failed to start")
            print("💡 Check server logs for details")
        
        return results

async def main():
    """Main function"""
    starter = AutoSessionStarter()
    
    try:
        await starter.run_auto_start()
    except KeyboardInterrupt:
        print("\n\n⏹️ Auto start interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
