#!/usr/bin/env python3
"""
Simplified TikTok Connector - Based on proven working approach
"""

import asyncio
import threading
import time
import logging
from typing import Callable, Optional, Dict, Any
from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, CommentEvent, GiftEvent, LikeEvent, DisconnectEvent

class SimpleTikTokConnector:
    """Simplified TikTok Live connector based on proven working approach"""
    
    def __init__(self, username: str):
        self.username = username.lower()
        self.client = TikTokLiveClient(unique_id=self.username)
        self.is_connected = False
        self.logger = logging.getLogger(__name__)
        
        # Stats tracking
        self.total_comments = 0
        self.total_gifts = 0
        self.total_likes = 0
        
        # Event handlers
        self.on_gift_handler: Optional[Callable] = None
        self.on_comment_handler: Optional[Callable] = None
        self.on_like_handler: Optional[Callable] = None
        self.on_connection_status_handler: Optional[Callable] = None
        
        # Setup event listeners (simplified)
        self._setup_simple_events()
    
    def _setup_simple_events(self):
        """Setup simple event handlers like in testing script"""
        
        @self.client.on(ConnectEvent)
        async def on_connect(event: ConnectEvent):
            self.is_connected = True
            self.logger.info(f"✅ Connected to @{event.unique_id}")
            if self.on_connection_status_handler:
                self.on_connection_status_handler(True)
        
        @self.client.on(DisconnectEvent)
        async def on_disconnect(event: DisconnectEvent):
            self.is_connected = False
            self.logger.warning(f"❌ Disconnected from @{self.username}")
            if self.on_connection_status_handler:
                self.on_connection_status_handler(False)
        
        @self.client.on(CommentEvent)
        async def on_comment(event: CommentEvent):
            self.total_comments += 1
            
            # Simple comment data extraction
            comment_data = {
                'username': getattr(event.user, 'unique_id', 'Unknown'),
                'nickname': getattr(event.user, 'nickname', 'Unknown'),
                'comment': getattr(event, 'comment', ''),
                'timestamp': time.time(),
                'event_id': f"comment_{self.total_comments}_{int(time.time())}"
            }
            
            if self.on_comment_handler:
                self.on_comment_handler(comment_data)
        
        @self.client.on(GiftEvent)
        async def on_gift(event: GiftEvent):
            self.total_gifts += 1
            
            # Simple gift data extraction
            gift_data = {
                'username': getattr(event.user, 'unique_id', 'Unknown'),
                'nickname': getattr(event.user, 'nickname', 'Unknown'),
                'gift_name': getattr(event.gift, 'name', 'Unknown Gift'),
                'gift_value': getattr(event.gift, 'diamond_count', 0),
                'repeat_count': getattr(event, 'repeat_count', 1),
                'timestamp': time.time(),
                'event_id': f"gift_{self.total_gifts}_{int(time.time())}"
            }
            
            # Handle streakable gifts
            if hasattr(event.gift, 'streakable') and hasattr(event, 'streaking'):
                if event.gift.streakable and not event.streaking:
                    # Only process when streak is finished
                    if self.on_gift_handler:
                        self.on_gift_handler(gift_data)
            else:
                # Non-streakable or unknown structure
                if self.on_gift_handler:
                    self.on_gift_handler(gift_data)
        
        @self.client.on(LikeEvent)
        async def on_like(event: LikeEvent):
            self.total_likes += 1
            
            # Simple like data extraction
            like_data = {
                'username': getattr(event.user, 'unique_id', 'Unknown'),
                'nickname': getattr(event.user, 'nickname', 'Unknown'),
                'like_count': getattr(event, 'count', 1),
                'total_likes': getattr(event, 'total', 0),
                'timestamp': time.time(),
                'event_id': f"like_{self.total_likes}_{int(time.time())}"
            }
            
            if self.on_like_handler:
                self.on_like_handler(like_data)
    
    def set_event_handlers(self, on_gift: Callable = None, on_comment: Callable = None, on_like: Callable = None, on_connection_status: Callable = None):
        """Set event handlers"""
        self.on_gift_handler = on_gift
        self.on_comment_handler = on_comment
        self.on_like_handler = on_like
        self.on_connection_status_handler = on_connection_status
    
    async def _connect_async(self, timeout: int = 30):
        """Async connection method using proven approach"""
        try:
            # Check if live first
            is_live = await self.client.is_live()
            if not is_live:
                self.logger.warning(f"@{self.username} is not live")
                return False
            
            self.logger.info(f"✅ @{self.username} is live, connecting...")
            
            # Connect with timeout (use same timeout as successful testing script)
            await asyncio.wait_for(self.client.start(), timeout=timeout)
            return True
            
        except asyncio.TimeoutError:
            self.logger.warning(f"⏰ Connection timeout after {timeout}s - continuing in tracking mode")
            return False
        except Exception as e:
            self.logger.error(f"❌ Connection error: {e}")
            return False
    
    def connect(self) -> bool:
        """Connect to TikTok Live using simplified approach"""
        try:
            self.logger.info(f"🚀 Attempting simplified connection to @{self.username}")
            
            # Use threading to avoid event loop conflicts
            def run_connection():
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    return loop.run_until_complete(self._connect_async(timeout=30))
                except Exception as e:
                    self.logger.error(f"Thread connection error: {e}")
                    return False
                finally:
                    loop.close()
            
            # Run in separate thread to avoid conflicts
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_connection)
                result = future.result(timeout=35)  # Give extra 5s for thread overhead
                return result
                
        except Exception as e:
            self.logger.error(f"❌ Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from TikTok Live"""
        try:
            if hasattr(self.client, 'disconnect'):
                self.client.disconnect()
            self.is_connected = False
            self.logger.info(f"🔌 Disconnected from @{self.username}")
        except Exception as e:
            self.logger.error(f"Error disconnecting: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            'connected': self.is_connected,
            'total_comments': self.total_comments,
            'total_gifts': self.total_gifts,
            'total_likes': self.total_likes,
            'username': self.username
        }

# Test function
async def test_simple_connector():
    """Test the simplified connector"""
    print("🧪 TESTING SIMPLIFIED CONNECTOR")
    print("=" * 50)
    
    connector = SimpleTikTokConnector("rhianladiku19")
    
    # Set simple handlers
    def on_comment(data):
        print(f"💬 {data['nickname']}: {data['comment']}")
    
    def on_gift(data):
        print(f"🎁 {data['nickname']} sent {data['repeat_count']}x {data['gift_name']}")
    
    def on_like(data):
        print(f"👍 {data['nickname']} liked {data['like_count']}x")
    
    connector.set_event_handlers(
        on_comment=on_comment,
        on_gift=on_gift,
        on_like=on_like
    )
    
    result = connector.connect()
    print(f"✅ Connection result: {result}")
    
    if result:
        # Keep alive for a few seconds to see events
        await asyncio.sleep(10)
        connector.disconnect()
    
    return result

if __name__ == "__main__":
    asyncio.run(test_simple_connector())
