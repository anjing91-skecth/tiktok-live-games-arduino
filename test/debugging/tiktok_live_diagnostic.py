#!/usr/bin/env python3
"""
TikTok Live Diagnostic Tool - Advanced Connection Testing
Testing koneksi TikTok Live dengan diagnosis detail
"""
import asyncio
import logging
import sys
from datetime import datetime

# Simple logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("TikTokLiveTest")

# Import TikTokLive
try:
    from TikTokLive import TikTokLiveClient
    logger.info("✅ TikTokLive imported successfully")
except ImportError as e:
    logger.error(f"❌ Failed to import TikTokLive: {e}")
    print("\n💡 Install TikTokLive dengan: pip install TikTokLive")
    sys.exit(1)

class TikTokLiveDiagnostic:
    def __init__(self):
        """Initialize diagnostic tool"""
        self.target_users = ["rhianladiku19", "ayhiefachri"]
        
    async def test_user_connection(self, username):
        """Test connection to specific user"""
        print(f"\n🔍 Testing: {username}")
        print("-" * 40)
        
        result = {
            'username': username,
            'success': False,
            'error': None,
            'events_received': [],
            'connection_duration': 0
        }
        
        start_time = datetime.now()
        
        try:
            # Step 1: Create client
            print("1️⃣ Creating TikTokLive client...")
            client = TikTokLiveClient(unique_id=username)
            print("   ✅ Client created")
            
            # Step 2: Set up event handlers
            print("2️⃣ Setting up event handlers...")
            
            @client.on("connect")
            async def on_connect(event):
                print("   🎉 Connected to live stream!")
                result['events_received'].append('connect')
            
            @client.on("disconnect")
            async def on_disconnect(event):
                print("   📡 Disconnected from stream")
                result['events_received'].append('disconnect')
            
            @client.on("comment")
            async def on_comment(event):
                comment = event.comment[:50] + "..." if len(event.comment) > 50 else event.comment
                print(f"   💬 Comment: {comment}")
                result['events_received'].append('comment')
            
            @client.on("gift")
            async def on_gift(event):
                print(f"   🎁 Gift: {event.gift.name}")
                result['events_received'].append('gift')
            
            @client.on("join")
            async def on_join(event):
                print(f"   👋 User joined: {event.user.nickname}")
                result['events_received'].append('join')
            
            print("   ✅ Event handlers set up")
            
            # Step 3: Attempt connection
            print("3️⃣ Attempting connection...")
            await client.start()
            print("   ✅ Connection initiated")
            
            # Step 4: Monitor for events
            print("4️⃣ Monitoring for 15 seconds...")
            
            for i in range(15):
                await asyncio.sleep(1)
                elapsed = i + 1
                if elapsed % 5 == 0:
                    print(f"   ⏱️  {elapsed}/15 seconds - Events: {len(result['events_received'])}")
            
            # Step 5: Disconnect
            print("5️⃣ Disconnecting...")
            await client.disconnect()
            print("   ✅ Disconnected cleanly")
            
            result['success'] = True
            result['connection_duration'] = (datetime.now() - start_time).total_seconds()
            
            print(f"\n📊 Result for {username}:")
            print(f"   ✅ SUCCESS")
            print(f"   ⏱️  Duration: {result['connection_duration']:.1f} seconds")
            print(f"   📥 Events: {len(result['events_received'])}")
            if result['events_received']:
                print(f"   📋 Types: {', '.join(set(result['events_received']))}")
            
        except Exception as e:
            error_msg = str(e)
            result['error'] = error_msg
            result['connection_duration'] = (datetime.now() - start_time).total_seconds()
            
            print(f"\n📊 Result for {username}:")
            print(f"   ❌ FAILED")
            print(f"   ⏱️  Duration: {result['connection_duration']:.1f} seconds")
            print(f"   ❌ Error: {error_msg}")
            
            # Analyze error
            if "offline" in error_msg.lower():
                print("   💡 User is not live")
            elif "not found" in error_msg.lower():
                print("   💡 Username not found")
            elif "forbidden" in error_msg.lower():
                print("   💡 Access restricted")
            elif "timeout" in error_msg.lower():
                print("   💡 Connection timeout")
        
        return result
    
    async def run_diagnostic(self):
        """Run complete diagnostic"""
        print("🔧 TikTok Live Diagnostic Tool")
        print(f"{'='*50}")
        print(f"Target users: {', '.join(self.target_users)}")
        print(f"Started: {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*50}")
        
        results = {}
        
        for i, username in enumerate(self.target_users, 1):
            print(f"\n🎯 Test {i}/{len(self.target_users)}")
            
            result = await self.test_user_connection(username)
            results[username] = result
            
            if i < len(self.target_users):
                print("\n⏳ Waiting 5 seconds...")
                await asyncio.sleep(5)
        
        # Summary
        print(f"\n{'='*50}")
        print("📋 DIAGNOSTIC SUMMARY")
        print(f"{'='*50}")
        
        successful = sum(1 for r in results.values() if r['success'])
        total = len(results)
        
        print(f"📊 Results: {successful}/{total} successful")
        print()
        
        for username, result in results.items():
            if result['success']:
                events = len(result['events_received'])
                duration = result['connection_duration']
                print(f"✅ {username}: SUCCESS ({events} events, {duration:.1f}s)")
            else:
                error = result['error'][:50] + "..." if result['error'] and len(result['error']) > 50 else result['error']
                print(f"❌ {username}: FAILED - {error}")
        
        print(f"\nCompleted: {datetime.now().strftime('%H:%M:%S')}")
        
        if successful == 0:
            print(f"\n💡 TROUBLESHOOTING:")
            print("• Users may not be live currently")
            print("• TikTok may be blocking connections")
            print("• Network issues or rate limiting")
            print("• Try again when users are streaming")
        else:
            print(f"\n🎉 {successful} connection(s) successful!")
            print("💡 System is working correctly")
        
        return results

async def main():
    """Main function"""
    diagnostic = TikTokLiveDiagnostic()
    
    try:
        await diagnostic.run_diagnostic()
    except KeyboardInterrupt:
        print("\n\n⏹️  Diagnostic interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
