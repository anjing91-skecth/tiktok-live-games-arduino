"""
Debugging Script untuk Real-time Viewer Count
Test khusus untuk RoomUserSeqEvent dan viewer count extraction
"""

import asyncio
import logging
from TikTokLive import TikTokLiveClient
from TikTokLive.events import (
    ConnectEvent, RoomUserSeqEvent, WebsocketResponseEvent,
    CommentEvent, GiftEvent, LikeEvent, UserStatsEvent
)

# Setup logging untuk debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ViewerCountDebugger:
    def __init__(self, username: str):
        self.username = username
        self.client = TikTokLiveClient(unique_id=username)
        self.viewer_count = 0
        self.events_captured = 0
        
        # Register event handlers
        self.client.on(ConnectEvent, self.on_connect)
        self.client.on(RoomUserSeqEvent, self.on_room_user_seq)
        self.client.on(WebsocketResponseEvent, self.on_websocket_response)
        self.client.on(CommentEvent, self.on_comment)
        self.client.on(GiftEvent, self.on_gift)
        self.client.on(LikeEvent, self.on_like)
        self.client.on(UserStatsEvent, self.on_user_stats)

    async def on_connect(self, event: ConnectEvent):
        logger.info(f"🔗 CONNECTED to @{self.username}")
        
        # Check room_info
        room_info = event.room_info if hasattr(event, 'room_info') else None
        if room_info:
            logger.info(f"📊 ROOM INFO Available: {type(room_info)}")
            
            # Try to extract viewer count from room_info
            viewer_attrs = [
                'viewer_count', 'viewerCount', 'viewers', 'user_count', 
                'userCount', 'audience_count', 'audienceCount', 
                'participant_count', 'participantCount', 'online_count',
                'onlineCount', 'total_user', 'totalUser', 'stats'
            ]
            
            found_attrs = []
            if hasattr(room_info, '__dict__'):
                for attr in dir(room_info):
                    if not attr.startswith('_'):
                        try:
                            value = getattr(room_info, attr)
                            found_attrs.append(f"{attr}: {value} ({type(value)})")
                            
                            # Check if this looks like viewer count
                            if any(keyword in attr.lower() for keyword in ['viewer', 'user', 'count', 'audience']):
                                if isinstance(value, (int, float)) and value > 0:
                                    logger.info(f"🎯 POTENTIAL VIEWER COUNT in room_info.{attr}: {value}")
                                    self.viewer_count = int(value)
                        except:
                            pass
            
            logger.info(f"📋 ROOM_INFO ATTRIBUTES: {found_attrs[:10]}")  # Show first 10
        else:
            logger.warning("❌ No room_info in ConnectEvent")

    async def on_room_user_seq(self, event: RoomUserSeqEvent):
        self.events_captured += 1
        logger.info(f"👥 ROOM_USER_SEQ EVENT #{self.events_captured}")
        
        # Inspect all attributes of the event
        event_attrs = []
        for attr in dir(event):
            if not attr.startswith('_'):
                try:
                    value = getattr(event, attr)
                    event_attrs.append(f"{attr}: {value}")
                    
                    # Check for viewer count related data
                    if any(keyword in attr.lower() for keyword in ['viewer', 'user', 'count', 'audience', 'total']):
                        if isinstance(value, (int, float)) and value > 0:
                            logger.info(f"🎯 VIEWER DATA in event.{attr}: {value}")
                            if value != self.viewer_count:
                                self.viewer_count = value
                                logger.info(f"📈 VIEWER COUNT UPDATED: {self.viewer_count}")
                except:
                    pass
        
        logger.info(f"📋 RoomUserSeqEvent attributes: {event_attrs}")

    async def on_websocket_response(self, event: WebsocketResponseEvent):
        # Filter for potential viewer-related websocket messages
        response_data = str(event).lower()
        
        if any(keyword in response_data for keyword in ['viewer', 'user', 'count', 'audience', 'room']):
            logger.info(f"🌐 WEBSOCKET with viewer data: {str(event)[:200]}...")

    async def on_comment(self, event: CommentEvent):
        logger.info(f"💬 Comment from {event.user.nickname}: {event.comment}")

    async def on_gift(self, event: GiftEvent):
        logger.info(f"🎁 Gift from {event.user.nickname}: {event.gift.name} x{event.gift.count}")

    async def on_like(self, event: LikeEvent):
        logger.info(f"❤️ Like from {event.user.nickname}")

    async def on_user_stats(self, event: UserStatsEvent):
        logger.info(f"📊 USER_STATS EVENT")
        
        # Check all attributes for viewer data
        for attr in dir(event):
            if not attr.startswith('_'):
                try:
                    value = getattr(event, attr)
                    if any(keyword in attr.lower() for keyword in ['viewer', 'user', 'count', 'audience']):
                        if isinstance(value, (int, float)) and value > 0:
                            logger.info(f"🎯 USER STATS viewer data in {attr}: {value}")
                except:
                    pass

    async def run_debug_session(self, duration: int = 120):
        """Run debugging session for specified duration"""
        logger.info(f"🚀 Starting viewer count debug session for {duration}s")
        logger.info(f"🎯 Target: @{self.username}")
        
        try:
            # Connect with room info
            await self.client.connect(fetch_room_info=True)
            
            # Wait for events
            await asyncio.sleep(duration)
            
        except Exception as e:
            logger.error(f"❌ Error during debug session: {e}")
        finally:
            await self.client.disconnect()
            logger.info(f"🏁 Debug session completed. Events captured: {self.events_captured}")
            logger.info(f"📊 Final viewer count: {self.viewer_count}")

async def main():
    # Test dengan user yang sedang live
    username = "ayhiefachri"  # User yang kita tahu sedang live
    
    debugger = ViewerCountDebugger(username)
    await debugger.run_debug_session(duration=120)  # 2 minutes

if __name__ == "__main__":
    asyncio.run(main())
