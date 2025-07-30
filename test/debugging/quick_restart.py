#!/usr/bin/env python3
"""
Quick Live Restart - Restart sessions for confirmed live users
"""
import asyncio
import aiohttp
import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from TikTokLive import TikTokLiveClient

class QuickLiveRestart:
    def __init__(self):
        """Initialize quick restart manager"""
        self.base_url = "http://localhost:5000"
        self.target_users = ["rhianladiku19", "ayhiefachri"]
        
    async def test_basic_live(self, username):
        """Basic live test without events"""
        print(f"🔍 Testing: {username}")
        
        try:
            client = TikTokLiveClient(unique_id=username)
            is_live = await client.is_live()
            
            if is_live:
                print(f"  ✅ {username} is LIVE!")
                return True
            else:
                print(f"  ❌ {username} is not live")
                return False
                
        except Exception as e:
            print(f"  ❌ {username} failed: {e}")
            return False
    
    async def force_restart_sessions(self):
        """Force restart all sessions"""
        print("\n🔄 Force restarting sessions...")
        
        # Stop all sessions
        try:
            async with aiohttp.ClientSession() as session:
                active_url = f"{self.base_url}/api/sessions/active"
                async with session.get(active_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        sessions = data.get('sessions', {})
                        
                        for session_key, session_data in sessions.items():
                            account_id = session_data.get('account_id')
                            username = session_data.get('username')
                            
                            print(f"  🛑 Stopping {username}...")
                            stop_url = f"{self.base_url}/api/sessions/stop/{account_id}"
                            async with session.post(stop_url) as stop_response:
                                if stop_response.status == 200:
                                    print(f"    ✅ Stopped")
        except Exception as e:
            print(f"❌ Error stopping sessions: {e}")
        
        # Wait
        print(f"\n⏳ Waiting 5 seconds...")
        await asyncio.sleep(5)
        
        # Start fresh sessions
        print(f"\n🚀 Starting fresh sessions...")
        for username in self.target_users:
            try:
                async with aiohttp.ClientSession() as session:
                    # Get account ID
                    accounts_url = f"{self.base_url}/api/accounts"
                    async with session.get(accounts_url) as response:
                        if response.status == 200:
                            data = await response.json()
                            accounts = data.get('accounts', [])
                            
                            account_id = None
                            for acc in accounts:
                                if acc['username'] == username:
                                    account_id = acc['id']
                                    break
                            
                            if account_id:
                                print(f"  🚀 Starting {username} (ID: {account_id})...")
                                start_url = f"{self.base_url}/api/sessions/start/{account_id}"
                                async with session.post(start_url) as start_response:
                                    if start_response.status == 200:
                                        result = await start_response.json()
                                        print(f"    ✅ Started: {result.get('message')}")
                                    else:
                                        print(f"    ❌ Failed to start")
                            else:
                                print(f"  ❌ Account ID not found for {username}")
                                
            except Exception as e:
                print(f"  ❌ Error starting {username}: {e}")
    
    async def monitor_connections(self):
        """Monitor TikTok connections for 60 seconds"""
        print(f"\n⏰ Monitoring TikTok connections...")
        
        for i in range(6):  # Check every 10 seconds for 60 seconds
            print(f"  ⏳ Check {i+1}/6 (waiting 10s)...")
            await asyncio.sleep(10)
            
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"{self.base_url}/api/sessions/active"
                    async with session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            sessions = data.get('sessions', {})
                            
                            connected_count = 0
                            for session_key, session_data in sessions.items():
                                username = session_data.get('username')
                                tiktok_connected = session_data.get('tiktok_connected', False)
                                
                                status = "✅ CONNECTED" if tiktok_connected else "⏳ Connecting..."
                                print(f"    {username}: {status}")
                                
                                if tiktok_connected:
                                    connected_count += 1
                            
                            if connected_count == len(self.target_users):
                                print(f"\n🎉 ALL CONNECTED! ({connected_count}/{len(self.target_users)})")
                                return connected_count
                                
            except Exception as e:
                print(f"    ❌ Check error: {e}")
        
        print(f"\n⏰ Monitoring timeout reached")
        return 0
    
    async def run_quick_restart(self):
        """Run quick restart process"""
        print("⚡ QUICK LIVE RESTART")
        print("="*50)
        
        # Step 1: Quick live test
        print("\n1️⃣ Quick Live Test:")
        live_users = []
        for username in self.target_users:
            is_live = await self.test_basic_live(username)
            if is_live:
                live_users.append(username)
        
        print(f"\n📊 Live users: {len(live_users)}/{len(self.target_users)}")
        for user in live_users:
            print(f"  🟢 {user}")
        
        if len(live_users) == 0:
            print("❌ No users live - cannot proceed")
            return
        
        # Step 2: Force restart
        print("\n2️⃣ Force Restart Sessions:")
        await self.force_restart_sessions()
        
        # Step 3: Monitor
        print("\n3️⃣ Monitor Connections:")
        connected = await self.monitor_connections()
        
        # Results
        print(f"\n{'='*50}")
        print("RESULTS:")
        print(f"Live users: {len(live_users)}")
        print(f"Connected: {connected}")
        
        if connected == len(live_users):
            print("🎉 SUCCESS!")
            print("💡 Dashboard: http://localhost:5000")
        elif connected > 0:
            print("⚠️ PARTIAL SUCCESS")
        else:
            print("❌ CONNECTION FAILED")
            print("💡 TikTok may be blocking connections")

async def main():
    """Main function"""
    restart = QuickLiveRestart()
    
    try:
        await restart.run_quick_restart()
    except KeyboardInterrupt:
        print("\n\n⏹️ Interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
