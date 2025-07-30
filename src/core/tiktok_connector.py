"""
TikTok Live Connector
Menghubungkan ke TikTok Live API dan menangkap events
"""

import asyncio
import threading
import logging
import time
from typing import Callable, Dict, Any, Optional
from TikTokLive import TikTokLiveClient
from TikTokLive.events import CommentEvent, GiftEvent, LikeEvent, ConnectEvent, DisconnectEvent, UserStatsEvent, RoomUserSeqEvent
from .unicode_logger import get_safe_emoji_logger, SafeEmojiFormatter
from .analytics_manager import AnalyticsManager

class TikTokConnector:
    def __init__(self, username: str):
        self.username = username
        self.client = TikTokLiveClient(unique_id=username)
        self.logger = get_safe_emoji_logger(__name__)
        self.is_connected_flag = False
        self.event_loop = None
        self.loop_thread = None
        
        # Analytics integration
        self.analytics_manager: Optional[AnalyticsManager] = None
        self.analytics_enabled = False
        
        # Enhanced tracking metrics
        self.connection_attempts = 0
        self.last_connection_time = None
        self.session_start_time = None
        self.total_gifts_received = 0
        self.total_comments_received = 0
        self.total_likes_received = 0
        self.total_like_count = 0  # Accumulated like count
        self.current_viewers = 0
        self.peak_viewers = 0
        self.connection_quality = "unknown"
        
        # Top gifters leaderboard (username -> total gift value)
        self.top_gifters = {}
        # Gift count per user (username -> gift count)
        self.user_gift_counts = {}
        
        # Gift value mapping for better analytics
        self.gift_values = {
            # Standard gifts (common)
            'Rose': 1,
            'Like': 1,
            'Heart': 1,
            'TikTok': 1,
            'Clap': 1,
            
            # Medium value gifts
            'Swan': 5,
            'Kiss': 5,
            'Love Bang': 25,
            'Dancing Love': 25,
            'Star': 5,
            
            # High value gifts
            'Castle': 50,
            'Rocket': 100,
            'Sports Car': 100,
            'Yacht': 500,
            'Planet': 500,
            'Universe': 1000,
            'Alien': 2000,
            'Lion': 2000,
            'Whale': 5000,
            'Dragon': 5000,
            'Phoenix': 10000
        }
        
        # Event loop and threading
        self.event_loop = None
        self.connection_thread = None
        
        # Real-time event buffers for batch processing
        self.event_buffer = {
            'gifts': [],
            'comments': [],
            'likes': []
        }
        self.buffer_flush_interval = 1.0  # seconds
        self.last_buffer_flush = time.time()
        
        # Event handlers
        self.on_gift_handler: Optional[Callable] = None
        self.on_comment_handler: Optional[Callable] = None
        self.on_like_handler: Optional[Callable] = None
        self.on_connection_status_handler: Optional[Callable] = None
        
        # Setup event listeners
        self._setup_event_listeners()
        
        # Start buffer flush timer
        self._start_buffer_timer()
    
    def enable_analytics(self, analytics_manager: AnalyticsManager):
        """Enable analytics integration"""
        self.analytics_manager = analytics_manager
        self.analytics_enabled = True
        self.logger.info("Analytics integration enabled")
    
    def disable_analytics(self):
        """Disable analytics integration"""
        self.analytics_enabled = False
        self.analytics_manager = None
        self.logger.info("Analytics integration disabled")
    
    def get_gift_value_estimate(self, gift_name: str, gift_diamond_count: int = None) -> float:
        """Get estimated gift value in coins"""
        # Priority 1: Use API diamond count if available
        if gift_diamond_count is not None and gift_diamond_count > 0:
            # Convert diamonds to coins (typical ratio is 1:1 or 1:0.5)
            return float(gift_diamond_count)
        
        # Priority 2: Use our mapping
        if gift_name in self.gift_values:
            return float(self.gift_values[gift_name])
        
        # Priority 3: Estimate based on gift name patterns
        gift_name_lower = gift_name.lower()
        if any(word in gift_name_lower for word in ['universe', 'galaxy', 'cosmic']):
            return 1000.0
        elif any(word in gift_name_lower for word in ['dragon', 'phoenix', 'lion']):
            return 2000.0
        elif any(word in gift_name_lower for word in ['rocket', 'car', 'yacht']):
            return 100.0
        elif any(word in gift_name_lower for word in ['castle', 'crown']):
            return 50.0
        elif any(word in gift_name_lower for word in ['love', 'heart', 'kiss']):
            return 25.0
        elif any(word in gift_name_lower for word in ['star', 'flower', 'swan']):
            return 5.0
        
        # Default value
        return 1.0
    
    def track_analytics_event(self, event_type: str, event_data: Dict[str, Any]):
        """Track event for analytics if enabled"""
        if self.analytics_enabled and self.analytics_manager:
            try:
                self.analytics_manager.track_event(event_type, event_data)
            except Exception as e:
                self.logger.warning(f"Analytics tracking failed for {event_type}: {e}")
    
    def _setup_event_listeners(self):
        """Setup enhanced TikTok Live event listeners with real-time processing"""
        
        @self.client.on(ConnectEvent)
        async def on_connect(event: ConnectEvent):
            self.logger.info(f"✅ Connected to @{self.username} live stream")
            self.is_connected_flag = True
            self.last_connection_time = time.time()
            self.session_start_time = time.time()  # Track session start
            self.connection_quality = "excellent"
            
            # Extract viewer count from room_info in ConnectEvent
            room_info = None
            if hasattr(event, 'room_info') and event.room_info:
                room_info = event.room_info
                self.logger.info("📊 Room info available in ConnectEvent, extracting viewer data...")
            elif hasattr(self.client, 'room_info') and self.client.room_info:
                room_info = self.client.room_info
                self.logger.info("📊 Room info available in client, extracting viewer data...")
            
            if room_info:
                # Try to find viewer count in room_info
                viewer_count = self._extract_viewer_count_from_room_info(room_info)
                if viewer_count > 0:
                    self._update_viewer_count(viewer_count)
                    self.logger.info(f"👥 Initial viewer count from room_info: {viewer_count}")
                else:
                    self.logger.warning("⚠️ Could not extract viewer count from room_info")
            else:
                self.logger.warning("⚠️ No room_info available in ConnectEvent or client")
            
            # Notify connection status
            if self.on_connection_status_handler:
                threading.Thread(
                    target=self.on_connection_status_handler,
                    args=({
                        'connected': True,
                        'username': self.username,
                        'quality': self.connection_quality,
                        'timestamp': self.last_connection_time
                    },),
                    daemon=True
                ).start()
        
        @self.client.on(DisconnectEvent)
        async def on_disconnect(_: DisconnectEvent):
            self.logger.warning(f"❌ Disconnected from @{self.username} live stream")
            self.is_connected_flag = False
            self.connection_quality = "disconnected"
            
            # Notify connection status
            if self.on_connection_status_handler:
                threading.Thread(
                    target=self.on_connection_status_handler,
                    args=({
                        'connected': False,
                        'username': self.username,
                        'quality': self.connection_quality,
                        'timestamp': time.time()
                    },),
                    daemon=True
                ).start()
        
        @self.client.on(CommentEvent)
        async def on_comment(event: CommentEvent):
            try:
                self.total_comments_received += 1
                
                username = getattr(event.user, 'nickname', 'Unknown') if hasattr(event, 'user') else 'Unknown'
                user_id = getattr(event.user, 'user_id', '') if hasattr(event, 'user') else ''
                unique_id = getattr(event.user, 'unique_id', '') if hasattr(event, 'user') else ''
                
                comment_data = {
                    'username': username,
                    'user_id': user_id,
                    'unique_id': unique_id,
                    'comment': getattr(event, 'comment', ''),
                    'timestamp': time.time(),
                    'event_id': f"comment_{self.total_comments_received}_{int(time.time())}"
                }
                
                # Clean comment logging (format yang jelas untuk GUI)
                comment_text = comment_data['comment']
                self.logger.info(f"COMMENT #{self.total_comments_received}: {username} (@{unique_id}): {comment_text}")
                
                # Analytics tracking
                self.track_analytics_event("comment", {
                    'username': unique_id,
                    'nickname': username,
                    'comment': comment_text
                })
                
                # Add to buffer for batch processing
                self.event_buffer['comments'].append(comment_data)
                
                # Immediate processing for real-time feel
                if self.on_comment_handler:
                    threading.Thread(
                        target=self.on_comment_handler,
                        args=(comment_data,),
                        daemon=True
                    ).start()
                    
            except Exception as e:
                self.logger.error(f"Error handling comment event: {e}")
        
        @self.client.on(GiftEvent)
        async def on_gift(event: GiftEvent):
            try:
                # Enhanced gift processing with streak handling to avoid double counting
                gift_name = "unknown"
                gift_id = 0
                gift_value = 1
                repeat_count = 1
                gift_icon = ""
                gift_category = "standard"
                
                # Safely extract comprehensive gift information
                if hasattr(event, 'gift') and event.gift:
                    try:
                        gift_name = getattr(event.gift, 'name', 'unknown')
                        gift_id = getattr(event.gift, 'id', 0)
                        gift_value = getattr(event.gift, 'diamond_count', 1)
                        gift_icon = getattr(event.gift, 'icon', '')
                        
                        # Determine gift category based on value
                        if gift_value >= 1000:
                            gift_category = "premium"
                        elif gift_value >= 100:
                            gift_category = "special"
                        else:
                            gift_category = "standard"
                            
                    except Exception as gift_err:
                        self.logger.warning(f"Error extracting gift details: {gift_err}")
                
                # Enhanced repeat count handling
                try:
                    repeat_count = max(1, getattr(event, 'repeat_count', 1))
                except:
                    repeat_count = 1
                
                # IMPORTANT: Handle gift streaks properly to avoid double counting
                # Based on TikTok-Live-Connector documentation and implementation study
                should_process = False
                
                # Check for repeat_end attribute (similar to JavaScript library)
                repeat_end = getattr(event, 'repeat_end', True)  # Default to True for safety
                is_streaking = getattr(event, 'streaking', False)
                
                # Enhanced gift type detection
                gift_type = 0  # Default to non-streakable
                if hasattr(event, 'gift') and event.gift:
                    # Try to determine if this is a streakable gift (gift_type = 1 in JS library)
                    is_streakable = getattr(event.gift, 'streakable', False)
                    if is_streakable:
                        gift_type = 1
                
                # Apply the same logic as TikTok Chat Reader reference implementation
                if gift_type == 1:
                    # Streakable gift logic (like JavaScript: giftType === 1 && !repeatEnd)
                    if repeat_end or not is_streaking:
                        # Streak finished - process the final count
                        should_process = True
                    else:
                        # Streak in progress - skip to avoid double counting
                        should_process = False
                else:
                    # Non-streakable gift - process immediately
                    should_process = True
                
                if should_process:
                    self.total_gifts_received += 1
                    
                    # Enhanced gift data with debugging info
                    username = getattr(event.user, 'nickname', 'Unknown') if hasattr(event, 'user') else 'Unknown'
                    user_id = getattr(event.user, 'user_id', '') if hasattr(event, 'user') else ''
                    unique_id = getattr(event.user, 'unique_id', '') if hasattr(event, 'user') else ''
                    
                    gift_data = {
                        'username': username,
                        'user_id': user_id,
                        'unique_id': unique_id,
                        'gift_name': gift_name,
                        'gift_id': gift_id,
                        'gift_value': gift_value,
                        'repeat_count': repeat_count,
                        'gift_icon': gift_icon,
                        'gift_category': gift_category,
                        'gift_type': gift_type,
                        'is_pending_streak': self._is_pending_streak(event),
                        'repeat_end': repeat_end,
                        'is_streaking': is_streaking,
                        'timestamp': time.time(),
                        'event_id': f"gift_{self.total_gifts_received}_{int(time.time())}"
                    }
                    
                    # Calculate enhanced metrics
                    total_value = gift_data['gift_value'] * gift_data['repeat_count']
                    gift_data['total_value'] = total_value
                    gift_data['value_tier'] = self._get_value_tier(total_value)
                    
                    # Use our improved gift value estimation
                    estimated_coin_value = self.get_gift_value_estimate(gift_name, gift_value)
                    gift_data['estimated_coin_value'] = estimated_coin_value * repeat_count
                    
                    # Track top gifters
                    if username != 'Unknown':
                        self.top_gifters[username] = self.top_gifters.get(username, 0) + gift_data['estimated_coin_value']
                        # Track gift count per user
                        self.user_gift_counts[username] = self.user_gift_counts.get(username, 0) + 1
                    
                    # Analytics tracking with detailed gift data
                    self.track_analytics_event("gift", {
                        'username': unique_id,
                        'nickname': username,
                        'user_id': user_id,
                        'gift_name': gift_name,
                        'repeat_count': repeat_count,
                        'estimated_value': gift_data['estimated_coin_value']
                    })
                    
                    # Clean gift logging (format yang jelas untuk GUI)  
                    if repeat_count > 1:
                        log_message = f"GIFT #{self.total_gifts_received}: {username} sent {repeat_count}x \"{gift_name}\" (≈{gift_data['estimated_coin_value']:.1f} coins)"
                    else:
                        log_message = f"GIFT #{self.total_gifts_received}: {username} sent \"{gift_name}\" (≈{estimated_coin_value:.1f} coins)"
                    
                    self.logger.info(log_message)
                    
                    # Add to buffer
                    self.event_buffer['gifts'].append(gift_data)
                    
                    # Real-time processing
                    if self.on_gift_handler:
                        threading.Thread(
                            target=self.on_gift_handler,
                            args=(gift_data,),
                            daemon=True
                        ).start()
                        
            except Exception as e:
                self.logger.error(f"Error handling gift event: {e}")
                self.logger.debug(f"Gift event details: {event}")
        
        @self.client.on(LikeEvent)
        async def on_like(event: LikeEvent):
            try:
                self.total_likes_received += 1
                
                # Safely extract like count with multiple fallback options
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
                
                # Add to total like count (accumulated count for statistics)
                self.total_like_count += like_count
                
                username = getattr(event.user, 'nickname', 'Unknown') if hasattr(event, 'user') else 'Unknown'
                user_id = getattr(event.user, 'user_id', '') if hasattr(event, 'user') else ''
                unique_id = getattr(event.user, 'unique_id', '') if hasattr(event, 'user') else ''
                
                like_data = {
                    'username': username,
                    'user_id': user_id,
                    'unique_id': unique_id,
                    'like_count': like_count,
                    'total_likes': self.total_like_count,  # Add accumulated count
                    'timestamp': time.time(),
                    'event_id': f"like_{self.total_likes_received}_{int(time.time())}"
                }
                
                # Analytics tracking
                self.track_analytics_event("like", {
                    'username': unique_id,
                    'nickname': username,
                    'count': like_count
                })
                
                self.logger.debug(f"❤️ Like #{self.total_likes_received} from {username} (count: {like_count}, total: {self.total_like_count})")
                
                # Add to buffer
                self.event_buffer['likes'].append(like_data)
                
                # Real-time processing
                if self.on_like_handler:
                    threading.Thread(
                        target=self.on_like_handler,
                        args=(like_data,),
                        daemon=True
                    ).start()
                    
            except Exception as e:
                self.logger.error(f"Error handling like event: {e}")
    
        @self.client.on(UserStatsEvent)
        async def on_userstats(event: UserStatsEvent):
            """Handle user stats events (viewer count updates)"""
            try:
                viewer_count = None
                if hasattr(event, 'viewerCount'):
                    viewer_count = event.viewerCount
                elif hasattr(event, 'viewer_count'):
                    viewer_count = event.viewer_count
                else:
                    viewer_count = getattr(event, 'user_count', 0)
                
                if viewer_count > 0:
                    self._update_viewer_count(viewer_count)
                    
                    # Log viewer update untuk debugging
                    if viewer_count > self.peak_viewers:
                        self.logger.info(f"VIEWERS: Current {viewer_count:,} (New Peak!)")
                    
            except Exception as e:
                self.logger.error(f"Error handling user stats event: {e}")
        
        @self.client.on(RoomUserSeqEvent)
        async def on_room_user_seq(event: RoomUserSeqEvent):
            """Handle room user sequence events (real-time viewer count)"""
            try:
                viewer_count = None
                
                # Based on our debugging, RoomUserSeqEvent has these key attributes:
                # - m_total: Current real-time viewer count
                # - total_user: Total cumulative users who visited the stream
                
                if hasattr(event, 'm_total'):
                    viewer_count = event.m_total
                    self.logger.debug(f"RoomUserSeqEvent: Current viewers (m_total): {viewer_count}")
                elif hasattr(event, 'total_user'):
                    # Fallback to total_user if m_total not available
                    viewer_count = event.total_user
                    self.logger.debug(f"RoomUserSeqEvent: Using total_user as fallback: {viewer_count}")
                
                # If we still don't have viewer count, try other possible attributes
                if viewer_count is None:
                    viewer_attrs = [
                        'viewerCount', 'viewer_count', 'viewers', 'userCount', 'user_count',
                        'audienceCount', 'audience_count', 'onlineCount', 'online_count',
                        'participantCount', 'participant_count'
                    ]
                    
                    for attr in viewer_attrs:
                        if hasattr(event, attr):
                            viewer_count = getattr(event, attr)
                            self.logger.debug(f"RoomUserSeqEvent: Found viewer count via {attr}: {viewer_count}")
                            break
                
                if viewer_count is not None and viewer_count > 0:
                    self._update_viewer_count(viewer_count)
                    
                    # Analytics tracking for viewer updates
                    self.track_analytics_event("viewer_update", {
                        'count': viewer_count
                    })
                    
                    # Log significant viewer changes
                    if viewer_count > self.peak_viewers:
                        self.logger.info(f"VIEWERS: Current {viewer_count:,} (New Peak!)")
                    elif abs(viewer_count - self.current_viewers) > 10:  # Log changes > 10 viewers
                        change = viewer_count - self.current_viewers
                        direction = "↗" if change > 0 else "↘"
                        self.logger.info(f"VIEWERS: {self.current_viewers:,} → {viewer_count:,} ({direction} {change:+,})")
                
            except Exception as e:
                self.logger.error(f"Error handling room user seq event: {e}")
        
        # Add FollowEvent and ShareEvent handlers for analytics
        try:
            from TikTokLive.events import FollowEvent, ShareEvent
            
            @self.client.on(FollowEvent)
            async def on_follow(event: FollowEvent):
                """Handle follow events"""
                try:
                    username = getattr(event.user, 'nickname', 'Unknown') if hasattr(event, 'user') else 'Unknown'
                    unique_id = getattr(event.user, 'unique_id', '') if hasattr(event, 'user') else ''
                    
                    # Analytics tracking
                    self.track_analytics_event("follow", {
                        'username': unique_id,
                        'nickname': username
                    })
                    
                    self.logger.info(f"NEW FOLLOWER: {username} (@{unique_id})")
                    
                except Exception as e:
                    self.logger.error(f"Error handling follow event: {e}")
            
            @self.client.on(ShareEvent)
            async def on_share(event: ShareEvent):
                """Handle share events"""
                try:
                    username = getattr(event.user, 'nickname', 'Unknown') if hasattr(event, 'user') else 'Unknown'
                    unique_id = getattr(event.user, 'unique_id', '') if hasattr(event, 'user') else ''
                    
                    # Analytics tracking
                    self.track_analytics_event("share", {
                        'username': unique_id,
                        'nickname': username
                    })
                    
                    self.logger.info(f"STREAM SHARED: {username} (@{unique_id}) shared the stream")
                    
                except Exception as e:
                    self.logger.error(f"Error handling share event: {e}")
                    
        except ImportError:
            self.logger.warning("FollowEvent and ShareEvent not available in this TikTokLive version")
    
    def _extract_viewer_count_from_room_info(self, room_info) -> int:
        """Extract viewer count from room_info object"""
        try:
            # Try different possible attributes for viewer count
            possible_attrs = [
                'viewer_count', 'viewerCount', 'viewers', 'user_count', 
                'userCount', 'audience_count', 'audienceCount', 
                'participant_count', 'participantCount', 'online_count',
                'onlineCount', 'total_user', 'totalUser'
            ]
            
            # Check if room_info has __dict__ (is an object with attributes)
            if hasattr(room_info, '__dict__'):
                for attr in possible_attrs:
                    if hasattr(room_info, attr):
                        value = getattr(room_info, attr)
                        if isinstance(value, (int, float)) and value > 0:
                            self.logger.info(f"Found viewer count in room_info.{attr}: {value}")
                            return int(value)
                
                # Log all available attributes for debugging
                self.logger.debug("Available room_info attributes:")
                for key, value in room_info.__dict__.items():
                    self.logger.debug(f"  {key}: {value} ({type(value)})")
                    
            # Check if room_info is a dict
            elif isinstance(room_info, dict):
                for attr in possible_attrs:
                    if attr in room_info:
                        value = room_info[attr]
                        if isinstance(value, (int, float)) and value > 0:
                            self.logger.info(f"Found viewer count in room_info[{attr}]: {value}")
                            return int(value)
                
                # Log all available keys for debugging
                self.logger.debug("Available room_info keys:")
                for key, value in room_info.items():
                    self.logger.debug(f"  {key}: {value} ({type(value)})")
            
            self.logger.warning("No viewer count found in room_info")
            return 0
            
        except Exception as e:
            self.logger.error(f"Error extracting viewer count from room_info: {e}")
            return 0
    
    def _is_pending_streak(self, event) -> bool:
        """
        Determine if gift is in pending streak (similar to JavaScript isPendingStreak function)
        Based on TikTok-Live-Connector reference implementation
        """
        try:
            # Get gift type (1 = streakable, 0 = non-streakable)
            gift_type = 0
            if hasattr(event, 'gift') and event.gift:
                is_streakable = getattr(event.gift, 'streakable', False)
                if is_streakable:
                    gift_type = 1
            
            # Get repeat_end status
            repeat_end = getattr(event, 'repeat_end', True)
            
            # JavaScript equivalent: data.giftType === 1 && !data.repeatEnd
            return gift_type == 1 and not repeat_end
            
        except Exception as e:
            self.logger.warning(f"Error checking pending streak: {e}")
            return False
    
    def _get_value_tier(self, value: int) -> str:
        """Determine value tier for gifts"""
        if value >= 10000:
            return "legendary"
        elif value >= 5000:
            return "epic"
        elif value >= 1000:
            return "rare"
        elif value >= 100:
            return "uncommon"
        else:
            return "common"
    
    def _update_viewer_count(self, viewer_count: int):
        """Update current and peak viewer count"""
        self.current_viewers = viewer_count
        if viewer_count > self.peak_viewers:
            self.peak_viewers = viewer_count
            self.logger.debug(f"👥 New peak viewers: {self.peak_viewers}")
    
    def _start_buffer_timer(self):
        """Start background timer for buffer flushing"""
        def flush_buffer():
            while True:
                try:
                    current_time = time.time()
                    if current_time - self.last_buffer_flush >= self.buffer_flush_interval:
                        self._flush_event_buffer()
                        self.last_buffer_flush = current_time
                    time.sleep(0.1)  # Check every 100ms
                except Exception as e:
                    self.logger.error(f"Error in buffer timer: {e}")
                    time.sleep(1)
        
        buffer_thread = threading.Thread(target=flush_buffer, daemon=True)
        buffer_thread.start()
    
    def _flush_event_buffer(self):
        """Flush buffered events for batch processing"""
        try:
            if any(self.event_buffer.values()):
                # Log buffer stats
                gift_count = len(self.event_buffer['gifts'])
                comment_count = len(self.event_buffer['comments'])
                like_count = len(self.event_buffer['likes'])
                
                if gift_count > 0 or comment_count > 0 or like_count > 0:
                    self.logger.debug(f"📊 Buffer flush: {gift_count} gifts, {comment_count} comments, {like_count} likes")
                
                # Clear buffers
                self.event_buffer = {
                    'gifts': [],
                    'comments': [],
                    'likes': []
                }
        except Exception as e:
            self.logger.error(f"Error flushing buffer: {e}")
    
    def set_event_handlers(self, on_gift: Callable = None, on_comment: Callable = None, on_like: Callable = None, on_connection_status: Callable = None):
        """Set enhanced event handlers for TikTok Live events"""
        self.on_gift_handler = on_gift
        self.on_comment_handler = on_comment
        self.on_like_handler = on_like
        self.on_connection_status_handler = on_connection_status
    
    def connect(self) -> bool:
        """Connect to TikTok Live stream using proven approach with persistent event loop"""
        try:
            self.connection_attempts += 1
            self.logger.info(SafeEmojiFormatter.safe_format(
                "{loading} Attempting persistent connection #{attempts} to @{username}...",
                loading='loading',
                attempts=self.connection_attempts,
                username=self.username
            ))
            
            # Start persistent event loop in background thread for listening
            def run_persistent_connection():
                try:
                    self.event_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(self.event_loop)
                    
                    async def persistent_connect():
                        # Check if live first (critical step from successful testing)
                        is_live = await self.client.is_live()
                        if not is_live:
                            self.logger.warning(f"@{self.username} is not currently live")
                            return False
                        
                        self.logger.info(f"✅ @{self.username} confirmed live, connecting...")
                        
                        # Start connection with room info fetch untuk mendapatkan viewer data
                        await self.client.start(fetch_room_info=True)
                        
                        # Set connected flag when successfully connected
                        self.is_connected_flag = True
                        
                        # Keep event loop alive to listen for events (like debug script)
                        self.logger.info(f"🎧 Now listening for events from @{self.username}...")
                        
                        # Start viewer count monitoring
                        last_viewer_check = time.time()
                        
                        while self.is_connected_flag:
                            await asyncio.sleep(1)  # Keep loop alive like debug script
                            
                            # Update viewer count every 10 seconds
                            if time.time() - last_viewer_check >= 10:
                                try:
                                    if hasattr(self.client, 'room_info') and self.client.room_info:
                                        viewer_count = getattr(self.client.room_info, 'user_count', 0)
                                        self._update_viewer_count(viewer_count)
                                except:
                                    pass
                                last_viewer_check = time.time()
                            
                        return True
                    
                    return self.event_loop.run_until_complete(persistent_connect())
                    
                except asyncio.TimeoutError:
                    self.logger.warning(f"⏰ Connection timeout - retrying")
                    return False
                except Exception as e:
                    self.logger.error(f"❌ Connection error: {e}")
                    return False
                # NOTE: Don't close loop here - keep it alive for events!
            
            # Start event loop in daemon thread
            self.connection_thread = threading.Thread(target=run_persistent_connection, daemon=True)
            self.connection_thread.start()
            
            # Wait for initial connection (max 10 seconds)
            start_time = time.time()
            while time.time() - start_time < 10:
                if self.is_connected_flag:
                    break
                time.sleep(0.1)
            
            success = self.is_connected_flag
            
            if success:
                self.last_connection_time = time.time()
                self.connection_quality = "good"
                # Clean connection logging (format yang jelas)
                self.logger.info(f"SUCCESS: Connected to @{self.username}!")
                
                if self.on_connection_status_handler:
                    self.on_connection_status_handler({
                        'connected': True,
                        'username': self.username,
                        'quality': self.connection_quality,
                        'timestamp': self.last_connection_time
                    })
            else:
                self.logger.warning(SafeEmojiFormatter.safe_format(
                    "{warning} Connection failed or timeout",
                    warning='warning'
                ))
                
                if self.on_connection_status_handler:
                    self.on_connection_status_handler({
                        'connected': False,
                        'username': self.username,
                        'quality': 'failed',
                        'timestamp': time.time()
                    })
                    
            return success
                
        except Exception as e:
            self.logger.error(f"❌ Connection failed: {e}")
            return False
            return False
    
    def _run_event_loop(self):
        """Run TikTok Live client in event loop with enhanced error handling"""
        try:
            # Create new event loop for this thread
            self.event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.event_loop)
            
            self.logger.info(SafeEmojiFormatter.safe_format(
                "{loading} Starting TikTok Live client event loop...",
                loading='loading'
            ))
            
            # Run with timeout based on our successful test results
            async def connect_with_timeout():
                try:
                    # Check if user is live first (like our successful test)
                    is_live = await self.client.is_live()
                    if not is_live:
                        self.logger.warning(f"@{self.username} is not currently live")
                        return False
                    
                    self.logger.info(f"✅ @{self.username} confirmed live, connecting...")
                    
                    # Start connection with 60s timeout (successful in our test)
                    await asyncio.wait_for(self.client.start(fetch_room_info=True), timeout=60)
                    return True
                    
                except asyncio.TimeoutError:
                    self.logger.warning(f"⏰ Connection timeout for @{self.username}")
                    return False
                except Exception as e:
                    self.logger.error(f"❌ Connection error for @{self.username}: {e}")
                    return False
            
            # Run the connection
            success = self.event_loop.run_until_complete(connect_with_timeout())
            if not success:
                self.is_connected_flag = False
            
        except Exception as e:
            self.logger.error(SafeEmojiFormatter.safe_format(
                "{error} Error in TikTok Live event loop: {exception}",
                error='error',
                exception=str(e)
            ))
            self.logger.debug(f"Exception type: {type(e).__name__}")
            self.is_connected_flag = False
        finally:
            if self.event_loop and not self.event_loop.is_closed():
                self.event_loop.close()
    
    def disconnect(self):
        """Disconnect from TikTok Live stream and cleanup persistent event loop"""
        try:
            self.logger.info(f"Disconnecting from @{self.username}")
            
            # Set flag to stop event loop
            self.is_connected_flag = False
            
            # Stop client if running
            if self.event_loop and not self.event_loop.is_closed():
                try:
                    # Schedule client stop in the event loop
                    future = asyncio.run_coroutine_threadsafe(self.client.stop(), self.event_loop)
                    future.result(timeout=3)  # Wait max 3 seconds
                except Exception as e:
                    self.logger.warning(f"Client stop warning: {e}")
            
            # Wait for connection thread to finish
            if self.connection_thread and self.connection_thread.is_alive():
                self.connection_thread.join(timeout=5)
            
            # Close event loop if still open
            if self.event_loop and not self.event_loop.is_closed():
                try:
                    self.event_loop.call_soon_threadsafe(self.event_loop.stop)
                    time.sleep(1)  # Give time to stop
                except Exception as e:
                    self.logger.warning(f"Event loop close warning: {e}")
            
            self.logger.info(f"Disconnected from @{self.username}")
            
        except Exception as e:
            self.logger.error(f"Error disconnecting from TikTok Live: {e}")
    
    def reconnect(self) -> bool:
        """Reconnect to TikTok Live stream"""
        self.logger.info(f"Attempting to reconnect to @{self.username}")
        
        # Disconnect first
        self.disconnect()
        time.sleep(2)
        
        # Reconnect
        return self.connect()
    
    def is_connected(self) -> bool:
        """Check if connected to TikTok Live"""
        return self.is_connected_flag
    
    def get_client_info(self) -> Dict[str, Any]:
        """Get enhanced client information and statistics"""
        session_duration = 0
        if self.session_start_time:
            session_duration = time.time() - self.session_start_time
            
        return {
            'username': self.username,
            'connected': self.is_connected_flag,
            'connection_quality': self.connection_quality,
            'connection_attempts': self.connection_attempts,
            'last_connection_time': self.last_connection_time,
            'session_duration': session_duration,
            'session_duration_formatted': self.get_session_duration_formatted(),
            'client_id': id(self.client),
            'statistics': {
                'total_gifts': self.total_gifts_received,
                'total_comments': self.total_comments_received,
                'total_likes': self.total_like_count,  # Use accumulated like count, not user count
                'total_like_count': self.total_like_count,  # Total accumulated likes
                'peak_viewers': self.peak_viewers,
                'events_per_minute': self._calculate_events_per_minute()
            },
            'room_info': {
                'user_count': self.current_viewers,  # Current viewers untuk real-time display
                'peak_viewers': self.peak_viewers
            },
            'gift_statistics': self.get_gift_statistics(),
            'leaderboards': {
                'top_gifters': self.get_top_gifters(20),
                'total_gift_value': sum(self.top_gifters.values())
            },
            'buffer_status': {
                'gifts_buffered': len(self.event_buffer['gifts']),
                'comments_buffered': len(self.event_buffer['comments']),
                'likes_buffered': len(self.event_buffer['likes']),
                'buffer_health': self._get_buffer_health()
            }
        }
    
    def _calculate_events_per_minute(self) -> float:
        """Calculate events per minute for performance monitoring"""
        try:
            if self.last_connection_time:
                elapsed_minutes = (time.time() - self.last_connection_time) / 60
                if elapsed_minutes > 0:
                    total_events = self.total_gifts_received + self.total_comments_received + self.total_likes_received
                    return round(total_events / elapsed_minutes, 2)
            return 0.0
        except:
            return 0.0
    
    def get_real_time_stats(self) -> Dict[str, Any]:
        """Get real-time statistics for dashboard"""
        return {
            'connection_status': {
                'connected': self.is_connected_flag,
                'quality': self.connection_quality,
                'uptime': time.time() - self.last_connection_time if self.last_connection_time else 0
            },
            'event_counts': {
                'gifts': self.total_gifts_received,
                'comments': self.total_comments_received,
                'likes': self.total_like_count  # Use accumulated like count (total value), not user count
            },
            'performance': {
                'events_per_minute': self._calculate_events_per_minute(),
                'buffer_health': self._get_buffer_health()
            }
        }
    
    def get_top_gifters(self, limit: int = 20) -> list:
        """Get top gifters leaderboard"""
        sorted_gifters = sorted(
            self.top_gifters.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        return [
            {
                'rank': i + 1,
                'username': username,
                'total_value': value,
                'gift_count': self.user_gift_counts.get(username, 0),
                'percentage': round((value / sum(self.top_gifters.values())) * 100, 1) if self.top_gifters else 0
            }
            for i, (username, value) in enumerate(sorted_gifters[:limit])
        ]
    
    def get_top_gifters_with_timestamps(self, limit: int = 20) -> list:
        """Get top gifters leaderboard with last gift timestamps for Statistics tab"""
        try:
            # Get sorted gifters
            sorted_gifters = sorted(
                self.top_gifters.items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            
            # Build leaderboard with timestamp information
            leaderboard = []
            for i, (username, total_value) in enumerate(sorted_gifters[:limit]):
                # Find the most recent gift from this user
                last_gift_time = None
                nickname = username  # Default nickname sama dengan username
                
                # Search through gift event buffer for most recent gift from this user
                user_gifts = [g for g in self.event_buffer['gifts'] if g.get('username') == username]
                
                if user_gifts:
                    # Get most recent gift (last one in list)
                    latest_gift = user_gifts[-1]
                    last_gift_time = latest_gift.get('timestamp')
                    if 'username' in latest_gift and latest_gift['username']:
                        nickname = latest_gift['username']
                
                # Format timestamp untuk display
                last_gift_formatted = "Never"
                if last_gift_time:
                    try:
                        from datetime import datetime
                        gift_datetime = datetime.fromtimestamp(last_gift_time)
                        last_gift_formatted = gift_datetime.strftime("%H:%M:%S")
                    except Exception as e:
                        last_gift_formatted = "Error"
                
                leaderboard.append({
                    'rank': i + 1,
                    'username': username,
                    'nickname': nickname,
                    'total_value': total_value,
                    'gift_count': self.user_gift_counts.get(username, 0),
                    'percentage': round((total_value / sum(self.top_gifters.values())) * 100, 1) if self.top_gifters else 0,
                    'last_gift_time': last_gift_formatted,
                    'last_gift_timestamp': last_gift_time
                })
            
            return leaderboard
            
        except Exception as e:
            self.logger.error(f"Error getting top gifters with timestamps: {e}")
            return []
    
    def get_gift_statistics(self) -> Dict[str, Any]:
        """Get comprehensive gift statistics following TikTok Chat Reader patterns"""
        total_gift_value = sum(self.top_gifters.values())
        
        # Build top gifters list untuk GUI
        top_gifters_list = []
        for username, total_value in sorted(self.top_gifters.items(), key=lambda x: x[1], reverse=True):
            gift_count = self.user_gift_counts.get(username, 0)
            top_gifters_list.append({
                'username': username,
                'total_value': total_value,
                'gift_count': gift_count
            })
        
        return {
            'total_gifts_processed': self.total_gifts_received,
            'total_gift_value': total_gift_value,
            'total_coins': total_gift_value,  # Alias untuk GUI compatibility
            'unique_gifters': len(self.top_gifters),
            'average_gift_value': round(total_gift_value / max(1, self.total_gifts_received), 2),
            'top_gifter': max(self.top_gifters.items(), key=lambda x: x[1]) if self.top_gifters else ('None', 0),
            'top_gifters': top_gifters_list,  # List untuk GUI display
            'gift_distribution': self._get_gift_distribution()
        }
    
    def _get_gift_distribution(self) -> Dict[str, int]:
        """Get gift value distribution by tiers"""
        distribution = {
            'legendary': 0,    # >= 10000
            'epic': 0,         # >= 5000
            'rare': 0,         # >= 1000
            'uncommon': 0,     # >= 100
            'common': 0        # < 100
        }
        
        for value in self.top_gifters.values():
            tier = self._get_value_tier(value)
            if tier in distribution:
                distribution[tier] += 1
        
        return distribution

    def get_session_duration(self) -> float:
        """Get current session duration in seconds"""
        if self.session_start_time:
            return time.time() - self.session_start_time
        return 0.0
    
    def get_session_duration_formatted(self) -> str:
        """Get formatted session duration"""
        duration = self.get_session_duration()
        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)
        seconds = int(duration % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    def _get_buffer_health(self) -> str:
        """Get buffer health status"""
        total_buffered = sum(len(buffer) for buffer in self.event_buffer.values())
        if total_buffered == 0:
            return "optimal"
        elif total_buffered < 10:
            return "good"
        elif total_buffered < 50:
            return "moderate"
        else:
            return "high_load"

# Helper function to test TikTok Live connection
def test_connection(username: str) -> bool:
    """Test connection to TikTok Live user"""
    logging.basicConfig(level=logging.INFO)
    
    connector = TikTokConnector(username)
    
    def on_comment(comment_data):
        print(f"Comment: {comment_data}")
    
    def on_gift(gift_data):
        print(f"Gift: {gift_data}")
    
    def on_like(like_data):
        print(f"Like: {like_data}")
    
    connector.set_event_handlers(
        on_gift=on_gift,
        on_comment=on_comment,
        on_like=on_like
    )
    
    if connector.connect():
        print(f"Connected to @{username}. Listening for events...")
        try:
            # Keep alive for testing
            time.sleep(60)
        except KeyboardInterrupt:
            print("\\nInterrupted by user")
        finally:
            connector.disconnect()
        return True
    else:
        print(f"Failed to connect to @{username}")
        return False

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        username = sys.argv[1]
        test_connection(username)
    else:
        print("Usage: python tiktok_connector.py <username>")
