#!/usr/bin/env python3
"""
TikTokLive API Study - Testing Folder
=====================================
Mempelajari cara library TikTokLive API bekerja untuk:
1. Connection ke live stream
2. Mendapatkan data gift
3. Mendapatkan data comment  
4. Mendapatkan data like
5. ROOM INFO DAN VIEWER COUNT TRACKING
"""

import asyncio
import time
from typing import Optional
from TikTokLive import TikTokLiveClient
from TikTokLive.events import (
    ConnectEvent, DisconnectEvent, CommentEvent, 
    GiftEvent, LikeEvent, FollowEvent, ShareEvent, UserStatsEvent,
    RoomUserSeqEvent, WebsocketResponseEvent, UnknownEvent
)

class TikTokLiveStudy:
    """Class untuk mempelajari TikTokLive API"""
    
    def __init__(self, username: str):
        self.username = username.replace('@', '')
        self.client: Optional[TikTokLiveClient] = None
        self.stats = {
            'comments': 0,
            'gifts': 0, 
            'likes': 0,
            'follows': 0,
            'shares': 0,
            'viewers': 0
        }
        
    def setup_client(self):
        """Setup TikTokLive client dengan event handlers"""
        print(f"🎯 Setting up client for @{self.username}")
        
        # Create client
        self.client = TikTokLiveClient(unique_id=self.username)
        
        # Setup event handlers
        self.client.on(ConnectEvent)(self.on_connect)
        self.client.on(DisconnectEvent)(self.on_disconnect)
        self.client.on(CommentEvent)(self.on_comment)
        self.client.on(GiftEvent)(self.on_gift)
        self.client.on(LikeEvent)(self.on_like)
        self.client.on(FollowEvent)(self.on_follow)
        self.client.on(ShareEvent)(self.on_share)
        self.client.on(UserStatsEvent)(self.on_user_stats)
        self.client.on(RoomUserSeqEvent)(self.on_room_user_seq)
        self.client.on(WebsocketResponseEvent)(self.on_websocket_response)
        
        print("✅ Client setup complete")
        
    async def on_connect(self, event: ConnectEvent):
        """Handler ketika berhasil connect"""
        print(f"🎉 SUCCESS: Connected to @{event.unique_id}!")
        print(f"📺 Room ID: {self.client.room_id}")
        print(f"🔗 Connected: {self.client.connected}")
        
        # Print room_info if available
        if hasattr(self.client, 'room_info') and self.client.room_info:
            print("📊 ROOM INFO AVAILABLE:")
            room_info = self.client.room_info
            print(f"   Type: {type(room_info)}")
            if hasattr(room_info, '__dict__'):
                for key, value in room_info.__dict__.items():
                    print(f"   {key}: {value}")
                    if 'viewer' in str(key).lower() or 'count' in str(key).lower():
                        print(f"   ⭐ POSSIBLE VIEWER COUNT: {key} = {value}")
            else:
                print(f"   Content: {room_info}")
        else:
            print("⚠️ No room_info available (need fetch_room_info=True)")
            
        print("-" * 50)
        
    async def on_disconnect(self, event: DisconnectEvent):
        """Handler ketika disconnect"""
        print(f"🔌 Disconnected from @{self.username}")
        print("📊 Final Stats:")
        for key, value in self.stats.items():
            print(f"   {key}: {value}")
            
    async def on_user_stats(self, event: UserStatsEvent):
        """Handler untuk user stats events - MUNGKIN ADA VIEWER COUNT"""
        print(f"📈 USER STATS EVENT:")
        print(f"   Type: {type(event)}")
        if hasattr(event, '__dict__'):
            for key, value in event.__dict__.items():
                print(f"   {key}: {value}")
                if 'viewer' in str(key).lower() or 'count' in str(key).lower():
                    print(f"   ⭐ POSSIBLE VIEWER COUNT: {key} = {value}")
    
    async def on_room_user_seq(self, event: RoomUserSeqEvent):
        """Handler untuk room user sequence events - REAL-TIME VIEWER COUNT"""
        print(f"👥 ROOM USER SEQ EVENT (Current viewer count information):")
        print(f"   Type: {type(event)}")
        if hasattr(event, '__dict__'):
            for key, value in event.__dict__.items():
                print(f"   {key}: {value}")
                if 'viewer' in str(key).lower() or 'count' in str(key).lower() or 'user' in str(key).lower():
                    print(f"   🎯 VIEWER COUNT CANDIDATE: {key} = {value}")
                    # Update our internal viewer count
                    if isinstance(value, (int, float)) and value > 0:
                        self.stats['viewers'] = int(value)
                        print(f"   ✅ UPDATED VIEWER COUNT: {value}")
    
    async def on_websocket_response(self, event: WebsocketResponseEvent):
        """Handler untuk semua websocket events - untuk debugging viewer count"""
        # Filter hanya events yang mungkin berkaitan dengan viewer/user count
        event_type = type(event.event).__name__ if hasattr(event, 'event') else 'Unknown'
        
        # Hanya log events yang mungkin berkaitan dengan viewer count
        if any(keyword in event_type.lower() for keyword in ['user', 'viewer', 'room', 'count', 'stats']):
            print(f"🔍 WEBSOCKET EVENT: {event_type}")
            
            if hasattr(event, 'event') and hasattr(event.event, '__dict__'):
                for key, value in event.event.__dict__.items():
                    if any(keyword in str(key).lower() for keyword in ['viewer', 'count', 'user', 'audience']):
                        print(f"   🎯 POTENTIAL VIEWER DATA: {key} = {value}")
                        if isinstance(value, (int, float)) and value > 0:
                            self.stats['viewers'] = int(value)
                            print(f"   ✅ UPDATED VIEWER COUNT FROM {event_type}: {value}")
        
    async def on_comment(self, event: CommentEvent):
        """Handler untuk comment events"""
        self.stats['comments'] += 1
        username = event.user.unique_id if hasattr(event.user, 'unique_id') else 'Unknown'
        nickname = event.user.nickname if hasattr(event.user, 'nickname') else username
        comment = event.comment if hasattr(event, 'comment') else 'No comment'
        
        print(f"💬 COMMENT #{self.stats['comments']}: {nickname} (@{username}): {comment}")
        
    async def on_gift(self, event: GiftEvent):
        """Handler untuk gift events"""
        self.stats['gifts'] += 1
        username = event.user.unique_id if hasattr(event.user, 'unique_id') else 'Unknown'
        nickname = event.user.nickname if hasattr(event.user, 'nickname') else username
        
        gift_name = event.gift.name if hasattr(event.gift, 'name') else 'Unknown Gift'
        
        # Handle gift streaks
        if hasattr(event.gift, 'streakable') and hasattr(event, 'streaking'):
            if event.gift.streakable and not event.streaking:
                # Streak finished
                repeat_count = event.repeat_count if hasattr(event, 'repeat_count') else 1
                print(f"🎁 GIFT #{self.stats['gifts']}: {nickname} sent {repeat_count}x \"{gift_name}\"")
            elif not event.gift.streakable:
                # Non-streakable gift
                print(f"🎁 GIFT #{self.stats['gifts']}: {nickname} sent \"{gift_name}\"")
        else:
            # Fallback for unknown gift structure
            print(f"🎁 GIFT #{self.stats['gifts']}: {nickname} sent \"{gift_name}\"")
        
    async def on_like(self, event: LikeEvent):
        """Handler untuk like events"""
        self.stats['likes'] += 1
        username = event.user.unique_id if hasattr(event.user, 'unique_id') else 'Unknown'
        nickname = event.user.nickname if hasattr(event.user, 'nickname') else username
        like_count = event.count if hasattr(event, 'count') else 1
        
        print(f"👍 LIKE #{self.stats['likes']}: {nickname} liked {like_count}x")
        
    async def on_follow(self, event: FollowEvent):
        """Handler untuk follow events"""
        self.stats['follows'] += 1
        username = event.user.unique_id if hasattr(event.user, 'unique_id') else 'Unknown'
        nickname = event.user.nickname if hasattr(event.user, 'nickname') else username
        
        print(f"➕ FOLLOW #{self.stats['follows']}: {nickname} (@{username}) followed!")
        
    async def on_share(self, event: ShareEvent):
        """Handler untuk share events"""
        self.stats['shares'] += 1
        username = event.user.unique_id if hasattr(event.user, 'unique_id') else 'Unknown'
        nickname = event.user.nickname if hasattr(event.user, 'nickname') else username
        
        print(f"📤 SHARE #{self.stats['shares']}: {nickname} shared the stream!")
        
    async def test_connection(self, timeout: int = 60):
        """Test connection dengan timeout dan fetch_room_info=True"""
        print(f"🚀 Testing connection to @{self.username} for {timeout} seconds...")
        print("📋 USING fetch_room_info=True to get viewer count data!")
        
        try:
            # Start connection dengan timeout DAN fetch_room_info=True
            await asyncio.wait_for(
                self.client.start(fetch_room_info=True),
                timeout=timeout
            )
            print("✅ Connection completed successfully")
            
        except asyncio.TimeoutError:
            print(f"⏰ Connection timeout after {timeout} seconds")
            return False
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
            
        return True
        
    async def check_if_live(self):
        """Check apakah user sedang live"""
        print(f"🔍 Checking if @{self.username} is live...")
        
        try:
            is_live = await self.client.is_live()
            if is_live:
                print(f"✅ @{self.username} is currently LIVE!")
                return True
            else:
                print(f"❌ @{self.username} is NOT live")
                return False
        except Exception as e:
            print(f"💥 Error checking live status: {e}")
            return False

async def study_user(username: str, test_duration: int = 30):
    """Study specific user"""
    print("=" * 60)
    print(f"🎯 STUDYING USER: @{username}")
    print("=" * 60)
    
    study = TikTokLiveStudy(username)
    study.setup_client()
    
    # Check if live first
    is_live = await study.check_if_live()
    if not is_live:
        print("⚠️ User is not live, skipping connection test")
        return False
        
    # Test connection
    print(f"\n🔄 Starting {test_duration}s connection test...")
    success = await study.test_connection(timeout=test_duration)
    
    return success

async def main():
    """Main study function"""
    print("🚀 TikTokLive API Study Session")
    print("=" * 60)
    
    # Users to study (sesuai project kita)
    test_users = ["ayhiefachri"]
    
    results = {}
    
    for username in test_users:
        try:
            success = await study_user(username, test_duration=60)
            results[username] = success
            
            # Wait between tests
            if username != test_users[-1]:
                print("\n⏳ Waiting 15s before next test...")
                await asyncio.sleep(15)
                
        except KeyboardInterrupt:
            print(f"\n⚠️ Test interrupted for @{username}")
            break
        except Exception as e:
            print(f"\n💥 Unexpected error testing @{username}: {e}")
            results[username] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 STUDY RESULTS SUMMARY")
    print("=" * 60)
    
    for username, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"@{username}: {status}")
    
    successful = sum(results.values())
    total = len(results)
    print(f"\n📈 Overall: {successful}/{total} successful connections")
    
    if successful > 0:
        print("🎉 TikTokLive API study completed with successful connections!")
        print("💡 Key learnings:")
        print("   - ConnectEvent: Triggered on successful connection")
        print("   - CommentEvent: Real-time chat messages")
        print("   - GiftEvent: Virtual gifts (handle streaks!)")
        print("   - LikeEvent: Like events from viewers")
        print("   - FollowEvent: New followers")
        print("   - ShareEvent: Stream shares")
    else:
        print("⚠️ No successful connections - likely TikTok anti-bot protection")
        print("💡 Possible solutions:")
        print("   - Use different user agents")
        print("   - Add random delays")
        print("   - Use proxy servers")
        print("   - Implement session rotation")

if __name__ == "__main__":
    asyncio.run(main())
