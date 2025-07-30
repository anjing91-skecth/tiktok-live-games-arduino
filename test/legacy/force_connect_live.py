#!/usr/bin/env python3
"""
Force Connect Live - Restart sessions dengan koneksi TikTok yang lebih kuat
"""
import asyncio
import aiohttp
import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from TikTokLive import TikTokLiveClient

class ForceConnectLive:
    def __init__(self):
        """Initialize force connect manager"""
        self.base_url = "http://localhost:5000"
        self.target_users = ["rhianladiku19", "ayhiefachri"]
        
    async def test_live_status(self, username):
        """Test if user is actually live with simple check"""
        print(f"🔍 Testing live status: {username}")
        
        try:
            client = TikTokLiveClient(unique_id=username)
            
            print(f"  📡 Connecting...")
            await client.start()
            
            print(f"  ✅ Connected! User is LIVE")
            
            # Simple monitor without complex event handlers
            print(f"  👀 Monitoring for 3 seconds...")
            await asyncio.sleep(3)
            
            await client.disconnect()
            
            print(f"  ✅ {username} is actively live streaming!")
            
            return True, 1
            
        except Exception as e:
            print(f"  ❌ Connection failed: {e}")
            return False, 0
    
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
        print(f"\n⏳ Waiting 3 seconds...")
        await asyncio.sleep(3)
        
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
    
    async def wait_and_check_connections(self):
        """Wait and check if TikTok connections establish"""
        print(f"\n⏰ Waiting for TikTok connections to establish...")
        
        for i in range(6):  # Check every 10 seconds for 60 seconds total
            wait_time = 10
            print(f"  ⏳ Waiting {wait_time} seconds... ({i+1}/6)")
            await asyncio.sleep(wait_time)
            
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
                                
                                if tiktok_connected:
                                    connected_count += 1
                                    print(f"    ✅ {username}: TikTok Connected!")
                                else:
                                    print(f"    ⏳ {username}: Still connecting...")
                            
                            if connected_count == len(self.target_users):
                                print(f"\n🎉 All {connected_count} TikTok connections established!")
                                return connected_count
                            elif connected_count > 0:
                                print(f"\n⚠️ Partial success: {connected_count}/{len(self.target_users)} connected")
                                
            except Exception as e:
                print(f"    ❌ Check error: {e}")
        
        print(f"\n⏰ Connection wait timeout reached")
        return 0
    
    async def run_force_connect(self):
        """Run force connection process"""
        print("⚡ Force Connect TikTok Live")
        print("="*50)
        print("Mode: Aggressive connection for live users")
        print("="*50)
        
        # Step 1: Test if users are actually live
        print("\n1️⃣ Verifying Live Status:")
        live_results = {}
        for username in self.target_users:
            is_live, events = await self.test_live_status(username)
            live_results[username] = {'live': is_live, 'events': events}
        
        live_count = sum(1 for r in live_results.values() if r['live'])
        print(f"\n📊 Live status: {live_count}/{len(self.target_users)} users are live")
        
        if live_count == 0:
            print("❌ No users are currently live!")
            print("💡 Cannot establish TikTok connections to offline users")
            return
        
        # Step 2: Force restart sessions
        print("\n2️⃣ Force Restarting Sessions:")
        await self.force_restart_sessions()
        
        # Step 3: Wait and monitor connections
        print("\n3️⃣ Monitoring TikTok Connections:")
        connected_count = await self.wait_and_check_connections()
        
        # Final summary
        print(f"\n{'='*50}")
        print("⚡ FORCE CONNECT RESULTS")
        print(f"{'='*50}")
        
        for username, result in live_results.items():
            live_status = "🟢 LIVE" if result['live'] else "🔴 OFFLINE"
            events = result['events']
            print(f"{username}: {live_status} ({events} events)")
        
        print(f"\nTikTok Connections: {connected_count}/{len(self.target_users)}")
        
        if connected_count == live_count:
            print("🎉 SUCCESS: All live users connected!")
            print("💡 Dashboard: http://localhost:5000")
        elif connected_count > 0:
            print("⚠️ PARTIAL: Some connections established")
            print("💡 TikTok anti-bot may be affecting some connections")
        else:
            print("❌ FAILED: No TikTok connections established")
            print("💡 TikTok is blocking automated connections")
            print("💡 Try again later or use VPN")

async def main():
    """Main function"""
    connector = ForceConnectLive()
    
    try:
        await connector.run_force_connect()
    except KeyboardInterrupt:
        print("\n\n⏹️ Force connect interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
