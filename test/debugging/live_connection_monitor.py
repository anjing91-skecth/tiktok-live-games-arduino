#!/usr/bin/env python3
"""
Live Connection Monitor - Advanced TikTok Live Stream Testing
Monitoring dan troubleshooting untuk koneksi TikTok Live
"""
import asyncio
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from src.core.tiktok_connector import TikTokConnector
from src.core.database_manager import DatabaseManager
from src.core.unicode_logger import setup_unicode_logging, get_safe_emoji_logger
from TikTokLive import TikTokLiveClient

class LiveConnectionMonitor:
    def __init__(self):
        """Initialize live connection monitor"""
        setup_unicode_logging()
        self.logger = get_safe_emoji_logger("LiveMonitor")
        self.db_manager = DatabaseManager()
        self.target_users = ["rhianladiku19", "ayhiefachri"]
        self.connection_attempts = {}
        
    async def check_user_live_status(self, username):
        """Check if user is currently live"""
        try:
            self.logger.info(f"🔍 Checking live status for: {username}")
            
            # Create a temporary client to check status
            client = TikTokLiveClient(unique_id=username)
            
            # Try to get room info without connecting
            try:
                await client.start()
                await asyncio.sleep(2)  # Give it time to get info
                await client.stop()
                
                self.logger.info(f"✅ {username} appears to be live!")
                return True
                
            except Exception as e:
                error_msg = str(e).lower()
                if "offline" in error_msg or "not live" in error_msg:
                    self.logger.warning(f"📴 {username} is not live currently")
                    return False
                else:
                    self.logger.error(f"❌ Error checking {username}: {e}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"❌ Failed to check {username}: {e}")
            return None
    
    async def test_connection_detailed(self, username):
        """Test connection with detailed diagnostics"""
        self.logger.info(f"🔬 Starting detailed connection test for: {username}")
        
        connection_info = {
            'username': username,
            'start_time': datetime.now(),
            'steps': [],
            'success': False,
            'final_status': None
        }
        
        try:
            # Step 1: Basic client creation
            connection_info['steps'].append('Creating client...')
            self.logger.info(f"Step 1: Creating TikTokLive client for {username}")
            
            client = TikTokLiveClient(unique_id=username)
            connection_info['steps'].append('Client created ✅')
            
            # Step 2: Connection attempt
            connection_info['steps'].append('Attempting connection...')
            self.logger.info(f"Step 2: Attempting to connect to {username}")
            
            await client.start()
            connection_info['steps'].append('Connection established ✅')
            self.logger.info(f"✅ Successfully connected to {username}!")
            
            # Step 3: Test message receiving
            connection_info['steps'].append('Testing message reception...')
            
            message_received = False
            start_time = time.time()
            timeout = 10  # 10 seconds timeout
            
            @client.on("connect")
            async def on_connect(event):
                self.logger.info(f"🎉 Connected to {username}'s live stream!")
                connection_info['steps'].append('Connected to live stream ✅')
            
            @client.on("comment")
            async def on_comment(event):
                nonlocal message_received
                message_received = True
                self.logger.info(f"💬 Comment from {event.user.nickname}: {event.comment}")
                connection_info['steps'].append('Received live comment ✅')
            
            @client.on("gift")
            async def on_gift(event):
                self.logger.info(f"🎁 Gift from {event.user.nickname}: {event.gift.name}")
                connection_info['steps'].append('Received gift event ✅')
            
            # Wait for events
            self.logger.info(f"Monitoring {username} for {timeout} seconds...")
            await asyncio.sleep(timeout)
            
            # Step 4: Cleanup
            connection_info['steps'].append('Disconnecting...')
            await client.stop()
            connection_info['steps'].append('Disconnected cleanly ✅')
            
            connection_info['success'] = True
            connection_info['final_status'] = 'Connection successful'
            
            self.logger.info(f"🎉 Connection test completed successfully for {username}")
            
        except Exception as e:
            error_msg = str(e)
            connection_info['steps'].append(f'Error: {error_msg}')
            connection_info['final_status'] = error_msg
            
            self.logger.error(f"❌ Connection test failed for {username}: {e}")
            
            # Analyze error type
            if "offline" in error_msg.lower():
                self.logger.warning(f"📴 {username} is offline")
            elif "not found" in error_msg.lower():
                self.logger.warning(f"❓ Username {username} not found")
            elif "blocked" in error_msg.lower():
                self.logger.warning(f"🚫 Access blocked for {username}")
            else:
                self.logger.error(f"🔥 Unknown error for {username}: {error_msg}")
        
        connection_info['end_time'] = datetime.now()
        connection_info['duration'] = (connection_info['end_time'] - connection_info['start_time']).total_seconds()
        
        return connection_info
    
    def save_account_if_not_exists(self, username):
        """Save account to database if it doesn't exist"""
        try:
            accounts = self.db_manager.get_all_accounts()
            existing_usernames = [acc['username'] for acc in accounts]
            
            if username not in existing_usernames:
                self.logger.info(f"💾 Adding {username} to database")
                account_data = {
                    'username': username,
                    'display_name': username,
                    'followers_count': 0,
                    'is_verified': False,
                    'profile_pic_url': '',
                    'bio': ''
                }
                self.db_manager.save_account(account_data)
                self.logger.info(f"✅ {username} added to database")
            else:
                self.logger.info(f"✅ {username} already exists in database")
                
        except Exception as e:
            self.logger.error(f"❌ Failed to save account {username}: {e}")
    
    async def run_comprehensive_test(self):
        """Run comprehensive test for all target users"""
        self.logger.info("🚀 Starting comprehensive live connection test")
        self.logger.info(f"Target users: {', '.join(self.target_users)}")
        
        print(f"\n{'='*60}")
        print("🎯 TikTok Live Connection Monitor")
        print(f"{'='*60}")
        print(f"Testing users: {', '.join(self.target_users)}")
        print(f"Started at: {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*60}\n")
        
        results = {}
        
        for username in self.target_users:
            print(f"\n🔍 Testing: {username}")
            print("-" * 40)
            
            # Save account first
            self.save_account_if_not_exists(username)
            
            # Check live status
            live_status = await self.check_user_live_status(username)
            
            if live_status is True:
                print(f"✅ {username} is LIVE! Proceeding with connection test...")
                # Do detailed connection test
                result = await self.test_connection_detailed(username)
            elif live_status is False:
                print(f"📴 {username} is OFFLINE")
                result = {
                    'username': username,
                    'success': False,
                    'final_status': 'User is offline',
                    'steps': ['User is not live']
                }
            else:
                print(f"❓ Unable to determine status for {username}")
                result = {
                    'username': username,
                    'success': False,
                    'final_status': 'Status check failed',
                    'steps': ['Failed to check live status']
                }
            
            results[username] = result
            
            # Print result summary
            print(f"\nResult for {username}:")
            for step in result.get('steps', []):
                print(f"  • {step}")
            print(f"  Final: {result.get('final_status', 'Unknown')}")
            
            # Wait between tests
            if username != self.target_users[-1]:
                print("\n⏳ Waiting 3 seconds before next test...")
                await asyncio.sleep(3)
        
        # Print final summary
        print(f"\n{'='*60}")
        print("📊 FINAL SUMMARY")
        print(f"{'='*60}")
        
        successful_connections = sum(1 for r in results.values() if r.get('success', False))
        total_tests = len(results)
        
        print(f"✅ Successful connections: {successful_connections}/{total_tests}")
        
        for username, result in results.items():
            status = "SUCCESS" if result.get('success', False) else "FAILED"
            print(f"  {username}: {status} - {result.get('final_status', 'Unknown')}")
        
        print(f"\nTest completed at: {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*60}")
        
        return results

async def main():
    """Main function"""
    monitor = LiveConnectionMonitor()
    
    try:
        results = await monitor.run_comprehensive_test()
        
        # Check if any connections were successful
        any_success = any(r.get('success', False) for r in results.values())
        
        if any_success:
            print("\n🎉 At least one connection was successful!")
            print("💡 You can now start the main application to begin live tracking.")
        else:
            print("\n⚠️  No successful connections found.")
            print("💡 Possible reasons:")
            print("   - Users are not currently live")
            print("   - TikTok rate limiting")
            print("   - Network connectivity issues")
            print("   - Username changes")
            
            print("\n🔄 Recommendations:")
            print("   - Try again when users are live")
            print("   - Use different test usernames")
            print("   - Check your internet connection")
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Run the monitor
    asyncio.run(main())
