"""
Live Feed Tracker Component
==========================

Handles tracking controls (start/stop/toggle) while maintaining exact same functionality.
This component manages TikTok Live connection and tracker lifecycle.
"""

import tkinter as tk
import logging
from typing import Dict, Any, Optional
from src.tracker.tiktok_tracker_optimized import TikTokTrackerOptimized

class LiveFeedTracker:
    """Manages TikTok Live tracking controls for the Live Feed tab"""
    
    def __init__(self, widgets: Dict, statistics: Dict, logger: logging.Logger = None):
        self.widgets = widgets
        self.statistics = statistics
        self.logger = logger or logging.getLogger(__name__)
        
        # Tracking state
        self.current_tracker: Optional[TikTokTrackerOptimized] = None
        self.current_username = ""
        self.current_account = {'username': 'demo', 'arduino_port': 'N/A', 'id': 0}
        
        # Callback functions to be set by parent
        self.add_event_log_callback = None
        self.event_handlers = None
        
        # Arduino integration callback
        self.arduino_connection_callback = None
    
    def set_callbacks(self, add_event_log, event_handlers):
        """Set callback functions and event handlers"""
        self.add_event_log_callback = add_event_log
        self.event_handlers = event_handlers
    
    def set_current_username(self, username: str):
        """Set the current username for tracking"""
        self.current_username = username
    
    def toggle_tracking(self):
        """Start or stop tracking"""
        if self.current_tracker and hasattr(self.current_tracker, 'is_running') and self.current_tracker.is_running:
            self.stop_tracking()
        else:
            self.start_tracking()
    
    def start_tracking(self):
        """Start TikTok Live tracking"""
        if not self.current_username:
            if self.add_event_log_callback:
                self.add_event_log_callback("❌ No account selected. Please select an account from dropdown.")
            return
        
        # Prevent multiple starts
        if self.current_tracker and hasattr(self.current_tracker, 'is_running') and self.current_tracker.is_running:
            if self.add_event_log_callback:
                self.add_event_log_callback("⚠️ Tracking is already running")
            return
        
        try:
            # Update UI immediately to show starting state
            self.widgets['track_button'].config(text="🟡 Connecting...", state=tk.DISABLED)
            self.widgets['status_label'].config(text="🟡 Starting...")
            
            # Create new enhanced tracker using current selected username
            self.current_tracker = TikTokTrackerOptimized(self.current_username)
            
            # ARDUINO INTEGRATION HOOK: Connect Arduino tab to new tracker
            if hasattr(self, 'arduino_connection_callback') and self.arduino_connection_callback:
                try:
                    self.arduino_connection_callback(self.current_tracker)
                except Exception as e:
                    print(f"Error in Arduino connection callback: {e}")
            
            # Add event callbacks using the enhanced API if event handlers are available
            if self.event_handlers:
                self.current_tracker.add_listener('on_connect', 
                    lambda event: self.event_handlers.on_connect(event, self.current_username))
                self.current_tracker.add_listener('on_disconnect', 
                    lambda event: self.event_handlers.on_disconnect(event, self.current_tracker))
                self.current_tracker.add_listener('on_comment', self.event_handlers.on_comment)
                self.current_tracker.add_listener('on_gift', self.event_handlers.on_gift)
                self.current_tracker.add_listener('on_like', self.event_handlers.on_like)
                self.current_tracker.add_listener('on_follow', self.event_handlers.on_follow)
                self.current_tracker.add_listener('on_share', self.event_handlers.on_share)
                self.current_tracker.add_listener('on_join', self.event_handlers.on_join)
                self.current_tracker.add_listener('on_viewer_update', self.event_handlers.on_viewer_update)
                self.current_tracker.add_listener('on_live_end', self.event_handlers.on_live_end)
            
            # Start tracking
            self.current_tracker.start_async()
            
            # Update current account info
            self.current_account['username'] = self.current_username
            
            # Reset statistics
            self._reset_statistics()
            
            if self.add_event_log_callback:
                self.add_event_log_callback(f"🚀 Starting tracking for @{self.current_username}...")
                
        except Exception as e:
            self.logger.error(f"Error starting tracking: {e}")
            if self.add_event_log_callback:
                self.add_event_log_callback(f"❌ Failed to start tracking: {e}")
            # Reset button on error
            self.widgets['track_button'].config(text="🔴 Start Tracking", state=tk.NORMAL)
            self.widgets['status_label'].config(text="🔴 Not Tracking")
    
    def stop_tracking(self):
        """Stop TikTok Live tracking"""
        if self.current_tracker:
            try:
                # Update UI immediately
                self.widgets['track_button'].config(text="🟡 Stopping...", state=tk.DISABLED)
                self.widgets['status_label'].config(text="🟡 Stopping...")
                
                self.current_tracker.stop()  # Use optimized tracker method
                if self.add_event_log_callback:
                    self.add_event_log_callback(f"⏹️ Stopped tracking @{self.current_username}")
            except Exception as e:
                self.logger.error(f"Error stopping tracking: {e}")
                if self.add_event_log_callback:
                    self.add_event_log_callback(f"❌ Error stopping tracking: {e}")
            finally:
                self.current_tracker = None
        
        # Update UI to stopped state
        self.widgets['track_button'].config(text="🔴 Start Tracking", state=tk.NORMAL)
        self.widgets['status_label'].config(text="🔴 Not Tracking")
    
    def _reset_statistics(self):
        """Reset all statistics to zero"""
        for stat in self.statistics:
            self.statistics[stat] = 0
            if stat in self.widgets.get('stats_labels', {}):
                self.widgets['stats_labels'][stat].config(text="0")
    
    def get_current_tracker(self):
        """Get the current tracker instance"""
        return self.current_tracker
    
    def get_current_username(self):
        """Get the current username being tracked"""
        return self.current_username
    
    def get_current_account(self):
        """Get the current account information"""
        return self.current_account
