"""
TikTok Tracker Event Processing Component
========================================

Handles all TikTok Live events processing while maintaining exact same functionality.
This component processes all 9 essential events with unified callback system.
"""

import asyncio
import logging
from typing import Dict, Any, Callable, List, Optional
from datetime import datetime

try:
    from TikTokLive.events import (
        # Essential Connection Events
        ConnectEvent, DisconnectEvent, LiveEndEvent,
        # Core Social Events
        CommentEvent, GiftEvent, LikeEvent, JoinEvent,
        # Additional Social Events
        FollowEvent, ShareEvent,
        # Viewer Tracking
        RoomUserSeqEvent
    )
    TIKTOK_LIVE_AVAILABLE = True
except ImportError:
    TIKTOK_LIVE_AVAILABLE = False
    # Create dummy classes for type hints
    class ConnectEvent: pass
    class DisconnectEvent: pass
    class LiveEndEvent: pass
    class CommentEvent: pass
    class GiftEvent: pass
    class LikeEvent: pass
    class JoinEvent: pass
    class FollowEvent: pass
    class ShareEvent: pass
    class RoomUserSeqEvent: pass

class TikTokTrackerEvents:
    """Handles all TikTok Live event processing for the tracker"""
    
    def __init__(self, username: str, stats: Dict, callbacks: Dict, logger: Optional[logging.Logger] = None):
        self.username = username
        self.stats = stats
        self.callbacks = callbacks
        self.logger = logger or logging.getLogger(__name__)
        
        # Connection state
        self.is_connected = False
        self.connect_time = None
        self.room_id = None
        self.stream_status = "offline"
    
    # ===========================================
    # UNIFIED CALLBACK SYSTEM
    # ===========================================
    
    async def _execute_callbacks(self, event_type: str, event: Any) -> None:
        """Unified callback execution with error handling"""
        for callback in self.callbacks.get(event_type, []):
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                self.logger.error(f"Error in {event_type} callback: {e}")
                self.stats['errors'] += 1
    
    def _safe_get_user_field(self, event: Any, field: str, default: str = 'Unknown') -> str:
        """Safely extract user field from event"""
        try:
            if hasattr(event, 'user') and hasattr(event.user, field):
                return getattr(event.user, field)
        except:
            pass
        return default
    
    def _safe_get_event_field(self, event: Any, fields: List[str], default: Any = '') -> Any:
        """Safely extract event field with fallback options"""
        for field in fields:
            try:
                if hasattr(event, field):
                    return getattr(event, field)
            except:
                continue
        return default
    
    # ===========================================
    # ESSENTIAL EVENT HANDLERS
    # ===========================================
    
    async def _on_connect(self, event: ConnectEvent):
        """Handle connection"""
        self.is_connected = True
        self.connect_time = datetime.now()
        self.room_id = getattr(event, 'room_id', None)
        self.stream_status = "live"
        
        self.logger.info(f"🔗 Connected to @{self.username} (Room: {self.room_id})")
        await self._execute_callbacks('on_connect', event)
    
    async def _on_disconnect(self, event: DisconnectEvent):
        """Handle disconnection"""
        self.is_connected = False
        self.stream_status = "offline"
        
        duration = ""
        if self.connect_time:
            elapsed = datetime.now() - self.connect_time
            duration = f" (Duration: {elapsed.total_seconds():.0f}s)"
        
        self.logger.info(f"❌ Disconnected from @{self.username}{duration}")
        await self._execute_callbacks('on_disconnect', event)
    
    async def _on_live_end(self, event: LiveEndEvent):
        """Handle live stream end"""
        self.stream_status = "ended"
        self.logger.info(f"🔴 Live stream ended for @{self.username}")
        await self._execute_callbacks('on_live_end', event)
    
    async def _on_comment(self, event: CommentEvent):
        """Handle comment events"""
        self.stats['total_comments'] += 1
        
        username = self._safe_get_user_field(event, 'unique_id')
        comment_text = self._safe_get_event_field(event, ['comment', 'content'])
        
        self.logger.info(f"💬 {username}: {comment_text}")
        await self._execute_callbacks('on_comment', event)
    
    async def _on_gift(self, event: GiftEvent):
        """Handle gift events with proper streak handling to prevent double counting"""
        username = self._safe_get_user_field(event, 'unique_id')
        gift_name = 'Unknown Gift'
        repeat_count = getattr(event, 'repeat_count', 1)
        diamond_count = 0
        is_streaking = False
        
        # Extract gift info from m_gift field (primary) or gift field (fallback)
        if hasattr(event, 'm_gift') and event.m_gift:
            gift_name = getattr(event.m_gift, 'name', gift_name)
            diamond_count = getattr(event.m_gift, 'diamond_count', 0)
            # Check if gift is streakable
            is_streakable = getattr(event.m_gift, 'streakable', False)
            
            # Proper streak detection based on repeat_end field
            repeat_end = getattr(event, 'repeat_end', 1)  # 1 = streak finished, 0 = still streaking
            is_streaking = is_streakable and (repeat_end == 0)
        elif hasattr(event, 'gift'):
            # Fallback to gift field if m_gift not available
            gift_name = getattr(event.gift, 'name', gift_name)
            diamond_count = getattr(event.gift, 'diamond_count', 0)
        
        total_diamonds = diamond_count * repeat_count
        
        # Only process and send callback for finished gifts (not streaking)
        if not is_streaking:
            self.stats['total_gifts'] += repeat_count  # Count actual number of gifts sent
            
            if total_diamonds > 0:
                usd_value = total_diamonds * 0.005  # USD conversion
                self.stats['gift_value'] += usd_value
                self.logger.info(f"🎁 {username} → {gift_name} x{repeat_count} ({total_diamonds}💎 = ${usd_value:.3f})")
            else:
                self.logger.info(f"🎁 {username} → {gift_name} x{repeat_count}")
                
            # Only send callback when gift streak is finished
            await self._execute_callbacks('on_gift', event)
    
    async def _on_like(self, event: LikeEvent):
        """Handle like events"""
        self.stats['total_likes'] += 1
        
        username = self._safe_get_user_field(event, 'unique_id')
        like_count = getattr(event, 'count', 1)
        
        self.logger.info(f"👍 {username} liked ({like_count})")
        await self._execute_callbacks('on_like', event)
    
    async def _on_join(self, event: JoinEvent):
        """Handle join events - update stats only, no log display"""
        self.stats['total_joins'] += 1
        # Don't log join events as requested - just update stats
        await self._execute_callbacks('on_join', event)
    
    async def _on_follow(self, event: FollowEvent):
        """Handle follow events"""
        self.stats['total_follows'] += 1
        
        username = self._safe_get_user_field(event, 'unique_id')
        self.logger.info(f"❤️ {username} followed")
        await self._execute_callbacks('on_follow', event)
    
    async def _on_share(self, event: ShareEvent):
        """Handle share events"""
        self.stats['total_shares'] += 1
        
        username = self._safe_get_user_field(event, 'unique_id')
        self.logger.info(f"📤 {username} shared the stream")
        await self._execute_callbacks('on_share', event)
    
    async def _on_viewer_update(self, event: RoomUserSeqEvent):
        """Handle real-time viewer count updates - stats only, no log"""
        # Use m_total field (confirmed from library study)
        viewer_count = getattr(event, 'm_total', 0)
        
        if viewer_count > 0:
            self.stats['current_viewers'] = viewer_count
            
            # Update peak viewers
            if viewer_count > self.stats['peak_viewers']:
                self.stats['peak_viewers'] = viewer_count
            
            # Debug: Log viewer updates untuk troubleshooting (DISABLED for clean output)
            # self.logger.info(f"🔢 [DEBUG] Viewer update: {viewer_count} viewers")
            
            # Don't log viewer updates as requested - just update stats
            await self._execute_callbacks('on_viewer_update', event)
    
    # ===========================================
    # EVENT REGISTRATION METHODS
    # ===========================================
    
    def register_event_handlers(self, client):
        """Register all event handlers with the TikTokLive client"""
        if not TIKTOK_LIVE_AVAILABLE:
            self.logger.warning("TikTokLive not available - events will not be processed")
            return
            
        try:
            # Register essential event handlers
            client.on(ConnectEvent)(self._on_connect)
            client.on(DisconnectEvent)(self._on_disconnect)
            client.on(LiveEndEvent)(self._on_live_end)
            client.on(CommentEvent)(self._on_comment)
            client.on(GiftEvent)(self._on_gift)
            client.on(LikeEvent)(self._on_like)
            client.on(JoinEvent)(self._on_join)
            client.on(FollowEvent)(self._on_follow)
            client.on(ShareEvent)(self._on_share)
            client.on(RoomUserSeqEvent)(self._on_viewer_update)
            
            self.logger.info(f"✅ Event handlers registered for @{self.username}")
            
        except Exception as e:
            self.logger.error(f"Failed to register event handlers: {e}")
            raise
    
    # ===========================================
    # STATE ACCESS METHODS
    # ===========================================
    
    def get_connection_state(self):
        """Get current connection state"""
        return {
            'is_connected': self.is_connected,
            'connect_time': self.connect_time,
            'room_id': self.room_id,
            'stream_status': self.stream_status
        }
