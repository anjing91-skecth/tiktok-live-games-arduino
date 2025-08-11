"""
Arduino Event Bridge
===================

Bridge untuk menghubungkan TikTok Live events dengan Arduino tab.
Handles semua event yang relevan untuk Arduino control: viewer count, gifts, 
comments, likes, follows, shares.
"""

import logging
from typing import Optional, Callable, Dict, Any


class ArduinoEventBridge:
    """Bridge untuk menghubungkan Live Feed tracker dengan Arduino tab"""
    
    def __init__(self, arduino_tab):
        """
        Initialize Arduino Event Bridge
        
        Args:
            arduino_tab: Reference ke Arduino tab instance
        """
        self.arduino_tab = arduino_tab
        self.tracker = None
        self.logger = logging.getLogger(__name__)
        
        # Event callbacks untuk Arduino
        self.event_callbacks = {
            'viewer_update': self._handle_viewer_update,
            'gift_received': self._handle_gift_received,
            'comment_received': self._handle_comment_received,
            'like_received': self._handle_like_received,
            'follow_received': self._handle_follow_received,
            'share_received': self._handle_share_received,
            'connect': self._handle_connect,
            'disconnect': self._handle_disconnect
        }
    
    def connect_tracker(self, tracker):
        """Connect tracker dan setup event listeners"""
        try:
            if self.tracker == tracker:
                return  # Already connected
                
            # Disconnect previous tracker if any
            if self.tracker:
                self.disconnect_tracker()
                
            self.tracker = tracker
            
            if tracker:
                # Add all event listeners
                tracker.add_listener('on_viewer_update', self.event_callbacks['viewer_update'])
                tracker.add_listener('on_gift', self.event_callbacks['gift_received'])
                tracker.add_listener('on_comment', self.event_callbacks['comment_received'])
                tracker.add_listener('on_like', self.event_callbacks['like_received'])
                tracker.add_listener('on_follow', self.event_callbacks['follow_received'])
                tracker.add_listener('on_share', self.event_callbacks['share_received'])
                tracker.add_listener('on_connect', self.event_callbacks['connect'])
                tracker.add_listener('on_disconnect', self.event_callbacks['disconnect'])
                
                self.arduino_tab.log_message("🌉 Arduino Event Bridge connected to tracker")
                self.logger.info("Arduino Event Bridge connected to tracker")
                
        except Exception as e:
            self.logger.error(f"Error connecting tracker to Arduino bridge: {e}")
            self.arduino_tab.log_message(f"❌ Bridge connection error: {e}")
    
    def disconnect_tracker(self):
        """Disconnect dari tracker"""
        if self.tracker:
            try:
                # Remove all event listeners
                for event_name, callback in self.event_callbacks.items():
                    self.tracker.remove_listener(f'on_{event_name}', callback)
                    
                self.arduino_tab.log_message("🌉 Arduino Event Bridge disconnected")
                self.logger.info("Arduino Event Bridge disconnected")
                
            except Exception as e:
                self.logger.error(f"Error disconnecting tracker from Arduino bridge: {e}")
            finally:
                self.tracker = None
    
    # ===========================================
    # EVENT HANDLERS
    # ===========================================
    
    def _handle_viewer_update(self, event):
        """Handle viewer count update"""
        try:
            viewer_count = getattr(event, 'm_total', 0)
            if viewer_count > 0:
                self.arduino_tab.current_viewer_count = viewer_count
                self.arduino_tab.update_viewer_display(viewer_count)
                
                # Check stage progression berdasarkan viewer count
                self.arduino_tab.check_stage_progression(viewer_count)
                
                # Log viewer update (throttled)
                if not hasattr(self, '_last_viewer_log') or abs(viewer_count - self._last_viewer_log) >= 5:
                    self.arduino_tab.log_message(f"👥 Viewers: {viewer_count}")
                    self._last_viewer_log = viewer_count
                    
        except Exception as e:
            self.logger.error(f"Error handling viewer update: {e}")
    
    def _safe_get_username(self, user):
        """Safely extract username from user object"""
        if isinstance(user, dict):
            return user.get('nickname', user.get('unique_id', 'Unknown'))
        elif hasattr(user, 'nickname'):
            return user.nickname
        elif hasattr(user, 'unique_id'):
            return user.unique_id
        else:
            return 'Unknown'
    
    def _extract_gift_info(self, event):
        """Extract gift information from event using same logic as tracker"""
        gift_name = 'Unknown Gift'
        gift_count = getattr(event, 'repeat_count', 1)
        diamond_count = 0
        gift_id = None
        is_streakable = False
        
        # Extract gift info from m_gift field (primary) or gift field (fallback)
        if hasattr(event, 'm_gift') and event.m_gift:
            gift_name = getattr(event.m_gift, 'name', gift_name)
            diamond_count = getattr(event.m_gift, 'diamond_count', 0)
            gift_id = getattr(event.m_gift, 'id', None)
            is_streakable = getattr(event.m_gift, 'streakable', False)
        elif hasattr(event, 'gift'):
            # Fallback to gift field if m_gift not available
            gift_name = getattr(event.gift, 'name', gift_name)
            diamond_count = getattr(event.gift, 'diamond_count', 0)
            gift_id = getattr(event.gift, 'id', None)
            is_streakable = getattr(event.gift, 'streakable', False)
        
        # Register gift in database if we have valid data
        if gift_name != 'Unknown Gift' and hasattr(self.arduino_tab, 'db_manager'):
            try:
                self.arduino_tab.db_manager.register_gift(
                    gift_id=str(gift_id) if gift_id else f"name_{gift_name}",
                    gift_name=gift_name,
                    diamond_count=diamond_count,
                    is_streakable=is_streakable
                )
            except Exception as e:
                self.logger.debug(f"Could not register gift {gift_name}: {e}")
        
        return {
            'name': gift_name,
            'count': gift_count,
            'diamond_count': diamond_count,
            'gift_id': gift_id,
            'total_diamonds': diamond_count * gift_count,
            'is_streakable': is_streakable
        }

    def _handle_gift_received(self, event):
        """Handle gift received event"""
        try:
            # Extract gift info using same logic as tracker
            gift_info = self._extract_gift_info(event)
            user = getattr(event, 'user', {})
            username = self._safe_get_username(user)
            
            # Format gift message with value if available
            if gift_info['total_diamonds'] > 0:
                usd_value = gift_info['total_diamonds'] * 0.005
                gift_message = f"🎁 {username} → {gift_info['name']} x{gift_info['count']} ({gift_info['total_diamonds']}💎 = ${usd_value:.3f})"
            else:
                gift_message = f"🎁 {username} → {gift_info['name']} x{gift_info['count']}"
            
            # Log ke Arduino tab
            self.arduino_tab.log_message(gift_message)
            
            # Trigger Arduino action untuk gift
            self.arduino_tab.trigger_gift_action(gift_info['name'], gift_info['count'], username)
            
        except Exception as e:
            self.logger.error(f"Error handling gift received: {e}")
    
    def _handle_comment_received(self, event):
        """Handle comment received event"""
        try:
            comment = getattr(event, 'comment', '')
            user = getattr(event, 'user', {})
            username = self._safe_get_username(user)
            
            # Log ke Arduino tab
            self.arduino_tab.log_message(f"💬 {username}: {comment[:50]}{'...' if len(comment) > 50 else ''}")
            
            # Trigger Arduino action untuk comment (jika ada rule)
            self.arduino_tab.trigger_comment_action(comment, username)
            
        except Exception as e:
            self.logger.error(f"Error handling comment received: {e}")
    
    def _handle_like_received(self, event):
        """Handle like received event"""
        try:
            user = getattr(event, 'user', {})
            username = self._safe_get_username(user)
            like_count = getattr(event, 'count', 1)
            
            # Log ke Arduino tab
            self.arduino_tab.log_message(f"👍 {username} liked ({like_count})")
            
            # Trigger Arduino action untuk like
            self.arduino_tab.trigger_like_action(like_count, username)
            
        except Exception as e:
            self.logger.error(f"Error handling like received: {e}")
    
    def _handle_follow_received(self, event):
        """Handle follow received event"""
        try:
            user = getattr(event, 'user', {})
            username = self._safe_get_username(user)
            
            # Log ke Arduino tab
            self.arduino_tab.log_message(f"➕ {username} followed!")
            
            # Trigger Arduino action untuk follow
            self.arduino_tab.trigger_follow_action(username)
            
        except Exception as e:
            self.logger.error(f"Error handling follow received: {e}")
    
    def _handle_share_received(self, event):
        """Handle share received event"""
        try:
            user = getattr(event, 'user', {})
            username = self._safe_get_username(user)
            
            # Log ke Arduino tab
            self.arduino_tab.log_message(f"📤 {username} shared the stream!")
            
            # Trigger Arduino action untuk share
            self.arduino_tab.trigger_share_action(username)
            
        except Exception as e:
            self.logger.error(f"Error handling share received: {e}")
    
    def _handle_connect(self, event):
        """Handle tracker connection"""
        try:
            username = getattr(event, 'username', 'Unknown')
            room_id = getattr(event, 'room_id', 'Unknown')
            
            self.arduino_tab.log_message(f"🔗 Connected to @{username} (Room: {room_id})")
            
            # Update tracker status to connected
            self.arduino_tab.update_tracker_status(True)
            
            # Reset viewer count display
            self.arduino_tab.current_viewer_count = 0
            self.arduino_tab.update_viewer_display(0)
            
        except Exception as e:
            self.logger.error(f"Error handling connect event: {e}")
    
    def _handle_disconnect(self, event):
        """Handle tracker disconnection"""
        try:
            username = getattr(event, 'username', 'Unknown')
            duration = getattr(event, 'duration', 0)
            
            self.arduino_tab.log_message(f"❌ Disconnected from @{username} (Duration: {duration}s)")
            
            # Update tracker status to disconnected
            self.arduino_tab.update_tracker_status(False)
            
            # Reset displays
            self.arduino_tab.current_viewer_count = 0
            self.arduino_tab.update_viewer_display(0)
            
        except Exception as e:
            self.logger.error(f"Error handling disconnect event: {e}")
    
    def is_connected(self) -> bool:
        """Check if bridge is connected to tracker"""
        return self.tracker is not None
    
    def get_tracker_info(self) -> Dict[str, Any]:
        """Get current tracker information"""
        if self.tracker:
            return {
                'connected': True,
                'tracker_type': type(self.tracker).__name__,
                'username': getattr(self.tracker, 'username', 'Unknown')
            }
        return {'connected': False}
