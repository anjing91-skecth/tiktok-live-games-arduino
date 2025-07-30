#!/usr/bin/env python3
"""
Integrated Live Data Capture System
Menggabungkan pendekatan testing yang sukses dengan sistem program
"""

import asyncio
import time
import logging
from datetime import datetime
from TikTokLive import TikTokLiveClient
from TikTokLive.events import CommentEvent, GiftEvent, LikeEvent, ConnectEvent, DisconnectEvent
from src.core.database_manager import DatabaseManager

# Setup simple logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IntegratedDataCapture:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.clients = {}
        self.sessions = {}
        self.monitoring = False
        
    async def start_capture(self, username: str):
        """Start data capture using proven working approach"""
        logger.info(f"🚀 Starting integrated capture for @{username}")
        
        try:
            # Get account from database
            account = self.db_manager.get_account_by_username(username)
            if not account:
                logger.error(f"❌ Account {username} not found!")
                return False
            
            # Create session in database
            session_id = self.db_manager.create_live_session(
                account_id=account['id'],
                session_name=f"Live Capture {username} {datetime.now().strftime('%H:%M:%S')}"
            )
            
            logger.info(f"✅ Created session {session_id} for {username}")
            
            # Create TikTok client (same as successful testing)
            client = TikTokLiveClient(unique_id=username)
            
            # Store references
            self.clients[username] = client
            self.sessions[username] = {
                'session_id': session_id,
                'account_id': account['id'],
                'start_time': time.time(),
                'gift_count': 0,
                'comment_count': 0,
                'like_count': 0
            }
            
            # Setup event handlers
            await self.setup_events(client, username, session_id)
            
            # Start connection (same method as successful testing)
            logger.info(f"🔍 Checking if @{username} is live...")
            
            is_live = await client.is_live()
            if not is_live:
                logger.warning(f"⚠️ @{username} is not live, continuing in tracking mode")
            else:
                logger.info(f"✅ @{username} is LIVE!")
            
            # Connect to live stream
            logger.info(f"🔄 Connecting to @{username}...")
            await client.start()
            
            logger.info(f"🎉 Successfully connected to @{username}!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error starting capture for {username}: {e}")
            return False
    
    async def setup_events(self, client, username: str, session_id: int):
        """Setup event handlers for data capture"""
        logger.info(f"🔧 Setting up event handlers for {username}")
        
        @client.on(ConnectEvent)
        async def on_connect(event):
            logger.info(f"🎉 Connected to @{username} live stream!")
            logger.info(f"📺 Room ID: {event.room_id}")
        
        @client.on(CommentEvent)
        async def on_comment(event):
            try:
                comment_id = self.db_manager.log_comment(
                    session_id=session_id,
                    username=event.user.unique_id,
                    comment_text=event.comment
                )
                
                self.sessions[username]['comment_count'] += 1
                
                logger.info(f"💬 COMMENT #{comment_id}: {event.user.unique_id}: {event.comment}")
                
            except Exception as e:
                logger.error(f"❌ Error handling comment: {e}")
        
        @client.on(GiftEvent)
        async def on_gift(event):
            try:
                gift_id = self.db_manager.log_gift(
                    session_id=session_id,
                    username=event.user.unique_id,
                    gift_name=event.gift.name,
                    gift_value=event.gift.diamond_count
                )
                
                self.sessions[username]['gift_count'] += 1
                
                logger.info(f"🎁 GIFT #{gift_id}: {event.user.unique_id} sent {event.gift.name} (${event.gift.diamond_count})")
                
            except Exception as e:
                logger.error(f"❌ Error handling gift: {e}")
        
        @client.on(LikeEvent)
        async def on_like(event):
            try:
                # Safely extract like count with fallback options
                like_count = 1  # Default fallback
                
                # Try different possible attributes for like count
                if hasattr(event, 'like_count'):
                    like_count = getattr(event, 'like_count', 1)
                elif hasattr(event, 'count'):
                    like_count = getattr(event, 'count', 1)
                elif hasattr(event, 'total_likes'):
                    like_count = getattr(event, 'total_likes', 1)
                elif hasattr(event, 'likes'):
                    like_count = getattr(event, 'likes', 1)
                
                self.db_manager.update_like_tracking(
                    session_id=session_id,
                    current_count=like_count
                )
                
                self.sessions[username]['like_count'] = like_count
                
                logger.info(f"👍 LIKE: Total likes now {like_count}")
                
            except Exception as e:
                logger.error(f"❌ Error handling like: {e}")
        
        @client.on(DisconnectEvent)
        async def on_disconnect(event):
            logger.warning(f"🔌 Disconnected from @{username}")
        
        logger.info(f"✅ Event handlers ready for {username}")
    
    async def monitor_multiple_accounts(self, usernames: list):
        """Monitor multiple accounts simultaneously"""
        logger.info(f"🎯 Starting monitoring for {len(usernames)} accounts")
        
        self.monitoring = True
        
        # Start all captures
        tasks = []
        for username in usernames:
            task = asyncio.create_task(self.start_capture(username))
            tasks.append(task)
        
        # Wait for all to start
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful_starts = 0
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"❌ Failed to start {usernames[i]}: {result}")
            elif result:
                successful_starts += 1
        
        logger.info(f"✅ Started {successful_starts}/{len(usernames)} accounts successfully")
        
        # Monitor and show stats
        await self.show_periodic_stats()
    
    async def show_periodic_stats(self):
        """Show periodic statistics"""
        logger.info("📊 Starting periodic stats monitoring...")
        
        start_time = time.time()
        
        try:
            while self.monitoring:
                await asyncio.sleep(15)  # Every 15 seconds
                
                elapsed = int(time.time() - start_time)
                logger.info(f"\n📈 [{elapsed}s] LIVE STATISTICS:")
                
                total_gifts = 0
                total_comments = 0
                total_likes = 0
                
                for username, session in self.sessions.items():
                    gifts = session['gift_count']
                    comments = session['comment_count']
                    likes = session['like_count']
                    
                    total_gifts += gifts
                    total_comments += comments
                    total_likes += likes
                    
                    logger.info(f"   @{username}: 🎁{gifts} 💬{comments} 👍{likes}")
                
                logger.info(f"   TOTAL: 🎁{total_gifts} 💬{total_comments} 👍{total_likes}")
                
        except KeyboardInterrupt:
            logger.info("⏹️ Monitoring stopped by user")
        except Exception as e:
            logger.error(f"❌ Error in stats monitoring: {e}")
        finally:
            self.monitoring = False
            await self.cleanup()
    
    async def cleanup(self):
        """Cleanup connections and sessions"""
        logger.info("🧹 Cleaning up connections...")
        
        for username, client in self.clients.items():
            try:
                await client.disconnect()
                logger.info(f"✅ Disconnected {username}")
            except:
                pass
        
        # End database sessions
        for username, session in self.sessions.items():
            try:
                self.db_manager.end_live_session(session['session_id'])
                logger.info(f"✅ Ended session for {username}")
            except:
                pass
        
        logger.info("✅ Cleanup completed")

async def main():
    """Main function"""
    print("🎯 INTEGRATED LIVE DATA CAPTURE SYSTEM")
    print("=" * 50)
    
    capture = IntegratedDataCapture()
    
    # Test accounts
    accounts = ["rhianladiku19", "ayhiefachri"]
    
    print("\nAvailable accounts:")
    for i, account in enumerate(accounts, 1):
        print(f"{i}. {account}")
    
    try:
        choice = input("\nSelect account (1-2) or 'all' for both: ").strip()
        
        if choice == 'all':
            print(f"\n🚀 Starting monitoring for all accounts...")
            await capture.monitor_multiple_accounts(accounts)
        elif choice in ['1', '2']:
            account = accounts[int(choice) - 1]
            print(f"\n🚀 Starting monitoring for {account}...")
            await capture.monitor_multiple_accounts([account])
        else:
            print("❌ Invalid choice")
            
    except KeyboardInterrupt:
        print("\n⏹️ Stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
