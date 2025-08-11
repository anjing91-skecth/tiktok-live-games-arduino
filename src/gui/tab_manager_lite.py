"""
Tab Manager Lite - Lightweight version with popup Account Manager
===============================================================

Simple tab management system:
- Live Feed Tab only
- Account Manager as popup dialog
- Basic tab management

Target: ~60 lines (simplified without cross-tab communication)
"""

import tkinter as tk
from tkinter import ttk
import logging
from typing import Optional

from live_feed_tab import LiveFeedTab


class TabManagerLite:
    """Lightweight Tab Manager - LIVE FEED ONLY"""
    
    def __init__(self, notebook: ttk.Notebook, status_var: tk.StringVar):
        self.notebook = notebook
        self.status_var = status_var
        self.logger = logging.getLogger(__name__)
        
        # Tab references
        self.live_feed_tab: Optional[LiveFeedTab] = None
        
        self.logger.info("TabManagerLite initialized")
    
    def create_live_feed_tab_only(self):
        """Create only Live Feed tab (Account Manager is now popup)"""
        try:
            # Create Live Feed tab
            self.live_feed_tab = LiveFeedTab(self.notebook, "Live Feed")
            self.logger.info("[OK] Live Feed tab created")
            
            # Select the tab
            self.notebook.select(0)
            self.status_var.set("Ready - Select account and start tracking")
            
            self.logger.info("[OK] Live Feed tab initialized")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create Live Feed tab: {e}")
            raise
    
    def cleanup(self):
        """Cleanup all tabs"""
        try:
            if self.live_feed_tab:
                self.live_feed_tab.cleanup()
            
            self.logger.info("Tab manager cleanup complete")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def get_live_feed_tab(self) -> Optional[LiveFeedTab]:
        """Get Live Feed tab reference"""
        return self.live_feed_tab
