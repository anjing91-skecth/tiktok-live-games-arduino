#!/usr/bin/env python3
"""
Live TikTok Data Capture Monitor
Real-time monitoring untuk capture data gift, comment, dan like
"""

import asyncio
import time
import logging
from datetime import datetime
from src.core.database_manager import DatabaseManager
from src.core.session_manager import SessionManager
from src.core.tiktok_connector import TikTokConnector

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class LiveDataMonitor:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.session_manager = SessionManager(self.db_manager, arduino_enabled=False)
        self.connectors = {}
        self.monitoring = False
        
    async def start_live_monitoring(self, username: str):
        """Start live monitoring untuk username"""
        print(f"\n🔄 Starting live monitoring for: {username}")
        
        try:
            # Get account
            account = self.db_manager.get_account_by_username(username)
            if not account:
                print(f"❌ Account {username} not found!")
                return False
            
            # Initialize session manager
            if not self.session_manager.initialize():
                print("❌ Failed to initialize session manager")
                return False
            
            # Start account session
            session_started = self.session_manager.start_account_session(
                account_id=account['id'],
                username=username,
                arduino_port=None
            )
            
            if not session_started:
                print(f"❌ Failed to start session for {username}")
                return False
            
            print(f"✅ Live session started for {username}")
            
            # Get active sessions to find our session ID
            active_sessions = self.db_manager.get_active_sessions()
            our_session = None
            for session in active_sessions:
                if session['username'] == username:
                    our_session = session
                    break
            
            if not our_session:
                print(f"❌ Could not find active session for {username}")
                return False
            
            session_id = our_session['id']
            print(f"📊 Found session ID: {session_id}")
            
            # Start monitoring loop
            self.monitoring = True
            await self.monitor_real_data(username, session_id)
            
            return True
            
        except Exception as e:
            print(f"❌ Error starting live monitoring: {str(e)}")
            return False
    
    async def monitor_real_data(self, username: str, session_id: int):
        """Monitor real data dari TikTok live"""
        print(f"\n📡 Monitoring real TikTok data for {username}...")
        print("🎯 Looking for live gifts, comments, and likes...")
        print("Press Ctrl+C to stop\n")
        
        last_gift_count = 0
        last_comment_count = 0
        last_like_count = 0
        start_time = time.time()
        
        try:
            while self.monitoring:
                # Check for new data every 5 seconds
                await asyncio.sleep(5)
                
                # Count current data
                gift_count = self.count_session_data(session_id, 'gift_logs')
                comment_count = self.count_session_data(session_id, 'comment_logs')
                like_data = self.get_latest_like_count(session_id)
                current_like_count = like_data if like_data else 0
                
                # Check for new data
                new_gifts = gift_count - last_gift_count
                new_comments = comment_count - last_comment_count
                like_change = current_like_count - last_like_count
                
                if new_gifts > 0 or new_comments > 0 or like_change != 0:
                    print(f"\n🔔 [{datetime.now().strftime('%H:%M:%S')}] NEW ACTIVITY:")
                    
                    if new_gifts > 0:
                        print(f"  🎁 +{new_gifts} new gifts! (Total: {gift_count})")
                        # Show latest gifts
                        self.show_latest_gifts(session_id, new_gifts)
                    
                    if new_comments > 0:
                        print(f"  💬 +{new_comments} new comments! (Total: {comment_count})")
                        # Show latest comments
                        self.show_latest_comments(session_id, new_comments)
                    
                    if like_change != 0:
                        print(f"  👍 Like count: {current_like_count} ({like_change:+d})")
                
                # Update counters
                last_gift_count = gift_count
                last_comment_count = comment_count
                last_like_count = current_like_count
                
                # Show periodic status
                elapsed = time.time() - start_time
                if int(elapsed) % 30 == 0 and elapsed > 5:  # Every 30 seconds
                    print(f"\n📊 [{datetime.now().strftime('%H:%M:%S')}] Status Update:")
                    print(f"   🎁 Total Gifts: {gift_count}")
                    print(f"   💬 Total Comments: {comment_count}")
                    print(f"   👍 Current Likes: {current_like_count}")
                    print(f"   ⏱️  Monitoring time: {int(elapsed)}s")
                
        except KeyboardInterrupt:
            print("\n⏹️  Monitoring stopped by user")
        except Exception as e:
            print(f"❌ Error during monitoring: {str(e)}")
        finally:
            self.monitoring = False
            print(f"\n✅ Monitoring ended for {username}")
    
    def count_session_data(self, session_id: int, table: str) -> int:
        """Count data in specific table for session"""
        try:
            import sqlite3
            conn = sqlite3.connect(self.db_manager.db_path)
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE session_id = ?", (session_id,))
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except:
            return 0
    
    def get_latest_like_count(self, session_id: int) -> int:
        """Get latest like count for session"""
        try:
            import sqlite3
            conn = sqlite3.connect(self.db_manager.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT current_like_count FROM like_tracking 
                WHERE session_id = ? 
                ORDER BY timestamp DESC 
                LIMIT 1
            """, (session_id,))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else 0
        except:
            return 0
    
    def show_latest_gifts(self, session_id: int, count: int):
        """Show latest gifts"""
        try:
            import sqlite3
            conn = sqlite3.connect(self.db_manager.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT username, gift_name, gift_value, timestamp
                FROM gift_logs 
                WHERE session_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (session_id, count))
            
            for row in cursor.fetchall():
                print(f"    🎁 {row[0]} sent {row[1]} (${row[2]}) at {row[3]}")
            
            conn.close()
        except Exception as e:
            print(f"    ❌ Error showing gifts: {str(e)}")
    
    def show_latest_comments(self, session_id: int, count: int):
        """Show latest comments"""
        try:
            import sqlite3
            conn = sqlite3.connect(self.db_manager.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT username, comment_text, timestamp
                FROM comment_logs 
                WHERE session_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (session_id, count))
            
            for row in cursor.fetchall():
                comment = row[1][:50] + "..." if len(row[1]) > 50 else row[1]
                print(f"    💬 {row[0]}: {comment} at {row[2]}")
            
            conn.close()
        except Exception as e:
            print(f"    ❌ Error showing comments: {str(e)}")
    
    def cleanup(self):
        """Cleanup resources"""
        print("\n🧹 Cleaning up...")
        
        try:
            self.monitoring = False
            
            if hasattr(self.session_manager, 'cleanup'):
                self.session_manager.cleanup()
            
            print("✅ Cleanup completed")
            
        except Exception as e:
            print(f"❌ Error during cleanup: {str(e)}")

async def main():
    """Main monitoring function"""
    print("🎯 TikTok Live Data Capture Monitor")
    print("=" * 40)
    
    monitor = LiveDataMonitor()
    
    accounts = ["rhianladiku19", "ayhiefachri"]
    
    print("\nAvailable accounts:")
    for i, account in enumerate(accounts, 1):
        print(f"{i}. {account}")
    
    try:
        choice = input("\nSelect account (1-2): ").strip()
        
        if choice in ['1', '2']:
            account = accounts[int(choice) - 1]
            print(f"\n🚀 Starting live monitoring for {account}...")
            await monitor.start_live_monitoring(account)
        else:
            print("❌ Invalid choice")
            
    except KeyboardInterrupt:
        print("\n⏹️  Stopped by user")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        monitor.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
