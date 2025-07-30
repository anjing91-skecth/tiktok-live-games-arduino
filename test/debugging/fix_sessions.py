#!/usr/bin/env python3
"""
Fix Sessions - Restart sessions dengan username yang benar
"""
import asyncio
import aiohttp
import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from src.core.database_manager import DatabaseManager

class SessionFixer:
    def __init__(self):
        """Initialize session fixer"""
        self.db_manager = DatabaseManager()
        self.base_url = "http://localhost:5000"
        
    async def stop_all_sessions(self):
        """Stop all active sessions"""
        print("🛑 Stopping all active sessions...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Get active sessions
                url = f"{self.base_url}/api/sessions/active"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        active_sessions = data.get('sessions', {})
                        
                        for session_key, session_data in active_sessions.items():
                            account_id = session_data.get('account_id')
                            username = session_data.get('username')
                            
                            if account_id:
                                print(f"  Stopping session for {username} (ID: {account_id})")
                                stop_url = f"{self.base_url}/api/sessions/stop/{account_id}"
                                
                                async with session.post(stop_url) as stop_response:
                                    if stop_response.status == 200:
                                        print(f"    ✅ Stopped")
                                    else:
                                        print(f"    ❌ Failed to stop")
                                        
                        print(f"✅ Stopped {len(active_sessions)} sessions")
                    else:
                        print("❌ Failed to get active sessions")
                        
        except Exception as e:
            print(f"❌ Error stopping sessions: {e}")
    
    async def start_correct_sessions(self):
        """Start sessions with correct usernames"""
        print("\n🚀 Starting sessions with correct usernames...")
        
        target_users = ["rhianladiku19", "ayhiefachri"]
        
        try:
            # Get accounts from database
            accounts = self.db_manager.get_all_accounts()
            
            for username in target_users:
                # Find account by username
                account = None
                for acc in accounts:
                    if acc['username'] == username:
                        account = acc
                        break
                
                if account:
                    account_id = account['id']
                    print(f"  Starting session for {username} (ID: {account_id})")
                    
                    async with aiohttp.ClientSession() as session:
                        url = f"{self.base_url}/api/sessions/start/{account_id}"
                        
                        async with session.post(url) as response:
                            if response.status == 200:
                                result = await response.json()
                                print(f"    ✅ Started: {result.get('message')}")
                            else:
                                try:
                                    result = await response.json()
                                    print(f"    ❌ Failed: {result.get('error')}")
                                except:
                                    print(f"    ❌ Failed: HTTP {response.status}")
                else:
                    print(f"  ❌ Account not found for {username}")
                    
        except Exception as e:
            print(f"❌ Error starting sessions: {e}")
    
    async def verify_sessions(self):
        """Verify sessions are running correctly"""
        print("\n🔍 Verifying sessions...")
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/api/sessions/active"
                
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        active_sessions = data.get('sessions', {})
                        
                        print(f"📊 Found {len(active_sessions)} active sessions:")
                        
                        for session_key, session_data in active_sessions.items():
                            username = session_data.get('username', 'Unknown')
                            account_id = session_data.get('account_id', 'Unknown')
                            tiktok_connected = session_data.get('tiktok_connected', False)
                            
                            status_icon = "✅" if tiktok_connected else "⚠️"
                            connection_status = "Connected" if tiktok_connected else "Not Connected"
                            
                            print(f"  {status_icon} {username} (ID: {account_id})")
                            print(f"     TikTok: {connection_status}")
                            
                        return len(active_sessions)
                    else:
                        print("❌ Failed to get session status")
                        return 0
                        
        except Exception as e:
            print(f"❌ Error verifying sessions: {e}")
            return 0
    
    async def run_fix(self):
        """Run complete session fix"""
        print("🔧 TikTok Live Session Fixer")
        print("="*50)
        
        # Step 1: Stop all sessions
        await self.stop_all_sessions()
        
        # Step 2: Wait a bit
        print("\n⏳ Waiting 3 seconds...")
        await asyncio.sleep(3)
        
        # Step 3: Start correct sessions
        await self.start_correct_sessions()
        
        # Step 4: Wait a bit
        print("\n⏳ Waiting 5 seconds for connections...")
        await asyncio.sleep(5)
        
        # Step 5: Verify
        active_count = await self.verify_sessions()
        
        print(f"\n{'='*50}")
        print("📊 RESULTS")
        print(f"{'='*50}")
        
        if active_count >= 2:
            print("🎉 Session fix completed successfully!")
            print("💡 Check dashboard at: http://localhost:5000")
        else:
            print("⚠️ Some sessions may not have started correctly")
            print("💡 Check server logs for TikTok connection errors")

async def main():
    """Main function"""
    fixer = SessionFixer()
    
    try:
        await fixer.run_fix()
    except KeyboardInterrupt:
        print("\n\n⏹️ Session fix interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
