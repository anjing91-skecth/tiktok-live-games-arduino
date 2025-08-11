"""
TikTok Tracker Core Component
Handles client management, connection, and public API
"""

import asyncio
import threading
import logging
from datetime import datetime
from typing import Dict, Any, List, Callable, Optional

try:
    from TikTokLive import TikTokLiveClient
    TIKTOK_LIVE_AVAILABLE = True
except ImportError:
    TIKTOK_LIVE_AVAILABLE = False
    TikTokLiveClient = None

from .tiktok_tracker_events import TikTokTrackerEvents


class TikTokTrackerCore:
    """Core tracker with client management and connection handling"""
    
    def __init__(self, username: str):
        """Initialize core tracker"""
        self.username = username
        self.logger = logging.getLogger(f'TikTokTracker.{username}')
        
        # Core state
        self.is_running = False
        self.is_connected = False
        self.stream_status = "unknown"
        self.room_id = None
        self.connect_time = None
        
        # Threading and async
        self.client_thread = None
        self.event_loop = None
        
        # Statistics
        self.stats = {
            'total_comments': 0,
            'total_gifts': 0,
            'total_likes': 0,
            'total_follows': 0,
            'total_shares': 0,
            'total_joins': 0,
            'current_viewers': 0,
            'peak_viewers': 0,
            'gift_value': 0.0,
            'errors': 0
        }
        
        # Callback management
        self.callbacks = {}
        
        # Event processor (initialize before client setup)
        self.event_processor = TikTokTrackerEvents(
            username=self.username,
            stats=self.stats,
            callbacks=self.callbacks,
            logger=self.logger
        )
        
        # Client setup
        self.client = None
        if TIKTOK_LIVE_AVAILABLE:
            self._setup_client()
    
    def _setup_client(self):
        """Setup TikTok Live client"""
        try:
            self.client = TikTokLiveClient(unique_id=self.username)
            self._setup_event_handlers()
            self.logger.info(f"✅ Client setup complete for @{self.username}")
        except Exception as e:
            self.logger.error(f"Client setup failed: {e}")
            raise
    
    def _setup_event_handlers(self):
        """Setup TikTok Live event handlers using event processor"""
        if not self.client:
            return
        
        # Use event processor to register all handlers
        self.event_processor.register_event_handlers(self.client)
    
    # ===========================================
    # CALLBACK MANAGEMENT
    # ===========================================
    
    def add_listener(self, event_type: str, callback: Callable):
        """Add event listener"""
        if event_type not in self.callbacks:
            self.callbacks[event_type] = []
        self.callbacks[event_type].append(callback)
        self.logger.debug(f"Added listener for {event_type}")
    
    def remove_listener(self, event_type: str, callback: Callable):
        """Remove event listener"""
        if event_type in self.callbacks and callback in self.callbacks[event_type]:
            self.callbacks[event_type].remove(callback)
            self.logger.debug(f"Removed listener for {event_type}")
    
    async def _execute_callbacks(self, event_type: str, data: Dict[str, Any]):
        """Execute callbacks for event type"""
        callbacks = self.callbacks.get(event_type, [])
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(data)
                else:
                    callback(data)
            except Exception as e:
                self.logger.error(f"Error in {event_type} callback: {e}")
    
    def execute_callbacks_sync(self, event_type: str, data: Dict[str, Any]):
        """Execute callbacks synchronously"""
        callbacks = self.callbacks.get(event_type, [])
        for callback in callbacks:
            try:
                if not asyncio.iscoroutinefunction(callback):
                    callback(data)
                else:
                    self.logger.warning(f"Async callback {callback} called in sync context")
            except Exception as e:
                self.logger.error(f"Error in {event_type} callback: {e}")
    
    # ===========================================
    # CONNECTION MANAGEMENT
    # ===========================================
    
    def start_async(self):
        """Start tracking in a separate thread"""
        if not TIKTOK_LIVE_AVAILABLE:
            raise ImportError("TikTokLive library not available")
        
        if self.is_running:
            self.logger.warning("Tracker is already running")
            return
        
        self.is_running = True
        self.client_thread = threading.Thread(target=self._run_client, daemon=True)
        self.client_thread.start()
        self.logger.info(f"🚀 Started tracking @{self.username}")
    
    def _run_client(self):
        """Run the client in async loop"""
        try:
            self.event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.event_loop)
            self.event_loop.run_until_complete(self._connect_and_run())
        except Exception as e:
            self.logger.error(f"Client error: {e}")
            # Execute error callbacks in sync context
            try:
                for callback in self.callbacks.get('on_error', []):
                    if not asyncio.iscoroutinefunction(callback):
                        callback({'error': str(e)})
            except Exception as callback_error:
                self.logger.error(f"Error in error callback: {callback_error}")
        finally:
            self.is_running = False
            if self.event_loop:
                self.event_loop.close()
    
    async def _connect_and_run(self):
        """Connect and maintain connection"""
        try:
            await self.client.connect()
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            await self._execute_callbacks('on_error', {'error': str(e)})
            raise
    
    def stop(self):
        """Stop tracking"""
        if not self.is_running:
            return
        
        self.logger.info(f"🛑 Stopping tracker for @{self.username}")
        self.is_running = False
        
        if self.client and hasattr(self.client, 'disconnect'):
            try:
                if self.event_loop and not self.event_loop.is_closed():
                    self.event_loop.create_task(self.client.disconnect())
            except Exception as e:
                self.logger.error(f"Error disconnecting client: {e}")
        
        if self.client_thread and self.client_thread.is_alive():
            self.client_thread.join(timeout=5.0)
    
    # ===========================================
    # STATUS & STATISTICS
    # ===========================================
    
    def get_status(self) -> Dict[str, Any]:
        """Get current tracker status"""
        return {
            'username': self.username,
            'is_running': self.is_running,
            'is_connected': self.is_connected,
            'stream_status': self.stream_status,
            'room_id': self.room_id,
            'connect_time': self.connect_time.isoformat() if self.connect_time else None,
            'stats': self.stats.copy()
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get tracking statistics"""
        return self.stats.copy()
    
    def reset_stats(self):
        """Reset statistics"""
        self.stats = {
            'total_comments': 0,
            'total_gifts': 0,
            'total_likes': 0,
            'total_follows': 0,
            'total_shares': 0,
            'total_joins': 0,
            'current_viewers': 0,
            'peak_viewers': 0,
            'gift_value': 0.0,
            'errors': 0
        }
        self.logger.info("📊 Statistics reset")
    
    # ===========================================
    # STATE MANAGEMENT
    # ===========================================
    
    def update_connection_state(self, connected: bool, room_id: Optional[str] = None):
        """Update connection state"""
        self.is_connected = connected
        if connected:
            self.connect_time = datetime.now()
            if room_id:
                self.room_id = room_id
        else:
            self.connect_time = None
            self.room_id = None
    
    def update_stream_status(self, status: str):
        """Update stream status"""
        self.stream_status = status
    
    def increment_stat(self, stat_name: str, value: int = 1):
        """Increment a statistic"""
        if stat_name in self.stats:
            self.stats[stat_name] += value
    
    def set_stat(self, stat_name: str, value: Any):
        """Set a statistic value"""
        if stat_name in self.stats:
            self.stats[stat_name] = value
    
    def update_viewer_count(self, count: int):
        """Update viewer count with peak tracking"""
        self.stats['current_viewers'] = count
        if count > self.stats['peak_viewers']:
            self.stats['peak_viewers'] = count
