"""
TikTok Tracker Optimized - Modular Version
==========================================

Optimized tracker using modular components for better maintainability.
"""

import logging
from typing import Dict, Any, Callable, Optional

# Import modular components
from .tracker_components.tiktok_tracker_core import TikTokTrackerCore


def is_library_available():
    """Check if TikTokLive library is available"""
    try:
        import TikTokLive
        return True
    except ImportError:
        return False


def create_tracker(username: str, callbacks: Optional[Dict[str, Callable]] = None, **kwargs):
    """Create TikTok tracker instance"""
    return TikTokTrackerOptimized(username, callbacks or {}, **kwargs)


class TikTokTrackerOptimized(TikTokTrackerCore):
    """
    Modular tracker using component architecture for better maintainability
    """
    
    def __init__(self, username: str, callbacks: Optional[Dict[str, Callable]] = None, **kwargs):
        """Initialize optimized tracker with modular components"""
        # Call parent constructor (creates event_processor)
        super().__init__(username)
        
        # Update callbacks if provided
        if callbacks:
            self.callbacks.update(callbacks)
            
        # Update event processor callbacks
        if hasattr(self, 'event_processor') and self.event_processor:
            self.event_processor.callbacks = self.callbacks
            
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"🔧 Phase 3 Modular Tracker initialized for @{username}")
        
    def get_stats(self) -> Dict[str, Any]:
        """Get tracker statistics"""
        return self.stats.copy()
    
    def add_listener(self, event_type: str, callback: Callable):
        """Add event listener with proper event processor integration"""
        # Call parent method first
        super().add_listener(event_type, callback)
        
        # Update event processor callbacks if it exists
        if hasattr(self, 'event_processor') and self.event_processor:
            self.event_processor.callbacks = self.callbacks

# Re-export key components
__all__ = ['TikTokTrackerOptimized', 'create_tracker', 'is_library_available']
