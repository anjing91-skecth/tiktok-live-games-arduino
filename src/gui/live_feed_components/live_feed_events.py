"""
Live Feed Event Handlers Component
=================================

Handles all TikTok Live events while maintaining exact same functionality.
This component processes comments, gifts, likes, follows, shares, joins, and viewer updates.
"""

import logging
from typing import Dict, Any, Optional

class LiveFeedEventHandlers:
    """Handles all TikTok Live events for the Live Feed tab"""
    
    def __init__(self, statistics: Dict, widgets: Dict, logger: logging.Logger = None):
        self.statistics = statistics
        self.widgets = widgets
        self.logger = logger or logging.getLogger(__name__)
        
        # Callback functions to be set by parent
        self.add_event_log_callback = None
        self.update_statistic_callback = None
        self.update_leaderboard_callback = None
        self.stop_tracking_callback = None
    
    def set_callbacks(self, add_event_log, update_statistic, update_leaderboard, stop_tracking):
        """Set callback functions for UI updates"""
        self.add_event_log_callback = add_event_log
        self.update_statistic_callback = update_statistic
        self.update_leaderboard_callback = update_leaderboard
        self.stop_tracking_callback = stop_tracking
    
    def on_connect(self, event, current_username: str = ""):
        """Handle successful connection to TikTok Live"""
        # Update UI to connected state
        self.widgets['track_button'].config(text="🟢 Stop Tracking", state='normal')
        self.widgets['status_label'].config(text="🟢 Connected")
        
        # Extract room ID safely
        room_id = getattr(event, 'room_id', 'Unknown')
        unique_id = getattr(event, 'unique_id', current_username)
        
        if self.add_event_log_callback:
            self.add_event_log_callback(f"🎭 Connected to @{unique_id} (Room: {room_id})")
    
    def on_disconnect(self, event, current_tracker=None):
        """Handle disconnection from TikTok Live"""
        # Update UI to disconnected state but keep stop button until fully stopped
        self.widgets['status_label'].config(text="🔴 Disconnected")
        
        if self.add_event_log_callback:
            self.add_event_log_callback(f"📤 Disconnected from live stream")
        
        # Check if this is an intentional stop or connection lost
        if current_tracker and hasattr(current_tracker, 'is_running') and not current_tracker.is_running:
            # Intentional stop - reset button
            self.widgets['track_button'].config(text="🔴 Start Tracking", state='normal')
            self.widgets['status_label'].config(text="🔴 Not Tracking")
    
    def on_live_end(self, event):
        """Handle when live stream ends"""
        self.widgets['status_label'].config(text="🔚 Stream Ended")
        
        if self.add_event_log_callback:
            self.add_event_log_callback(f"📺 Live stream has ended")
        
        # Auto stop tracking when stream ends
        if self.stop_tracking_callback:
            self.stop_tracking_callback()
    
    def on_comment(self, event):
        """Handle comment event with enhanced data"""
        try:
            username = event.user.unique_id if hasattr(event, 'user') and hasattr(event.user, 'unique_id') else 'Unknown'
            comment_text = event.comment if hasattr(event, 'comment') else event.content
            
            self.statistics['comments'] += 1
            
            if self.update_statistic_callback:
                self.update_statistic_callback('comments', self.statistics['comments'])
            
            if self.add_event_log_callback:
                self.add_event_log_callback(f"💬 {username}: {comment_text}")
            
        except Exception as e:
            self.logger.error(f"Error handling comment event: {e}")
            if self.add_event_log_callback:
                self.add_event_log_callback(f"💬 Comment received (error in display)")
    
    def on_gift(self, event):
        """Handle gift event with diamond/coin display"""
        try:
            username = event.user.unique_id if hasattr(event, 'user') and hasattr(event.user, 'unique_id') else 'Unknown'
            gift_name = event.gift.name if hasattr(event, 'gift') and hasattr(event.gift, 'name') else 'Unknown Gift'
            repeat_count = getattr(event, 'repeat_count', 1)
            
            # Get diamond count (TikTok's virtual currency)
            diamond_count = 0
            if hasattr(event, 'gift') and hasattr(event.gift, 'diamond_count'):
                diamond_count = event.gift.diamond_count * repeat_count
                
                # Update statistics
                self.statistics['gifts'] += repeat_count
                self.statistics['coins'] += diamond_count  # Use diamonds as coins
                
                if self.update_statistic_callback:
                    self.update_statistic_callback('gifts', self.statistics['gifts'])
                    self.update_statistic_callback('coins', self.statistics['coins'])
                
                # Add to leaderboard
                if self.update_leaderboard_callback:
                    self.update_leaderboard_callback(username, diamond_count, repeat_count)
                
                # Display with diamond count
                if self.add_event_log_callback:
                    self.add_event_log_callback(f"🎁 {username} sent {repeat_count}x {gift_name} ({diamond_count} diamonds)")
                
            else:
                # Fallback without diamond count
                self.statistics['gifts'] += repeat_count
                
                if self.update_statistic_callback:
                    self.update_statistic_callback('gifts', self.statistics['gifts'])
                
                if self.add_event_log_callback:
                    self.add_event_log_callback(f"🎁 {username} sent {repeat_count}x {gift_name}")
            
        except Exception as e:
            self.logger.error(f"Error handling gift event: {e}")
            if self.add_event_log_callback:
                self.add_event_log_callback(f"🎁 Gift received (error in display)")
    
    def on_like(self, event):
        """Handle like event with enhanced data"""
        try:
            username = event.user.unique_id if hasattr(event, 'user') and hasattr(event.user, 'unique_id') else 'Unknown'
            like_count = getattr(event, 'count', 1)
            
            self.statistics['likes'] += like_count
            
            if self.update_statistic_callback:
                self.update_statistic_callback('likes', self.statistics['likes'])
            
            if self.add_event_log_callback:
                if like_count > 1:
                    self.add_event_log_callback(f"❤️ {username} liked! (+{like_count})")
                else:
                    self.add_event_log_callback(f"❤️ {username} liked!")
            
        except Exception as e:
            self.logger.error(f"Error handling like event: {e}")
            if self.add_event_log_callback:
                self.add_event_log_callback(f"❤️ Like received")
    
    def on_follow(self, event):
        """Handle follow event with enhanced data"""
        try:
            username = event.user.unique_id if hasattr(event, 'user') and hasattr(event.user, 'unique_id') else 'Unknown'
            
            self.statistics['followers'] += 1
            
            if self.update_statistic_callback:
                self.update_statistic_callback('followers', self.statistics['followers'])
            
            if self.add_event_log_callback:
                self.add_event_log_callback(f"➕ {username} followed the stream!")
            
        except Exception as e:
            self.logger.error(f"Error handling follow event: {e}")
            if self.add_event_log_callback:
                self.add_event_log_callback(f"➕ New follower!")
    
    def on_share(self, event):
        """Handle share event"""
        try:
            username = event.user.unique_id if hasattr(event, 'user') and hasattr(event.user, 'unique_id') else 'Unknown'
            
            self.statistics['shares'] += 1
            
            if self.update_statistic_callback:
                self.update_statistic_callback('shares', self.statistics['shares'])
            
            if self.add_event_log_callback:
                self.add_event_log_callback(f"📤 {username} shared the stream!")
            
        except Exception as e:
            self.logger.error(f"Error handling share event: {e}")
            if self.add_event_log_callback:
                self.add_event_log_callback(f"📤 Stream shared!")
    
    def on_join(self, event):
        """Handle join event - don't display in GUI as requested"""
        try:
            # Don't add to event log as requested by user
            # username = event.user.unique_id if hasattr(event, 'user') and hasattr(event.user, 'unique_id') else 'Unknown'
            # self.add_event_log_callback(f"👋 {username} joined the stream!")
            pass
            
        except Exception as e:
            self.logger.error(f"Error handling join event: {e}")
            if self.add_event_log_callback:
                self.add_event_log_callback(f"👋 Someone joined the stream!")
    
    def on_viewer_update(self, event):
        """Handle viewer count update with enhanced anti-fluctuation"""
        try:
            # Use m_total field as confirmed from optimized tracker study
            viewer_count = getattr(event, 'm_total', 0)
            
            # Enhanced anti-fluctuation logic from main program
            current_viewers = self.statistics.get('viewers', 0)
            
            # Ignore sudden drops of more than 20%
            if viewer_count > 0 and current_viewers > 0:
                percentage_change = abs(viewer_count - current_viewers) / current_viewers
                
                # Enhanced anti-fluctuation: ignore drops > 20% but accept all increases
                if viewer_count < current_viewers and percentage_change > 0.2:
                    # Log the ignored fluctuation for debugging
                    self.logger.debug(f"Ignored viewer fluctuation: {current_viewers} -> {viewer_count} ({percentage_change:.1%})")
                    return
            
            # Update statistics and peak tracking
            self.statistics['viewers'] = viewer_count
            
            # Track peak viewers
            if viewer_count > self.statistics.get('peak_viewers', 0):
                self.statistics['peak_viewers'] = viewer_count
                if self.update_statistic_callback:
                    self.update_statistic_callback('peak_viewers', viewer_count)
            
            # Update current viewer display
            if self.update_statistic_callback:
                self.update_statistic_callback('viewers', viewer_count)
                
        except Exception as e:
            self.logger.error(f"Error handling viewer update event: {e}")
