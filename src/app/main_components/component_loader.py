"""
Component Loader
===============

Handles dynamic importing and loading of all application components.
Extracted from main.py for better maintainability.
"""

import logging
from tkinter import messagebox
import sys


class ComponentLoader:
    """Handles loading and importing of application components"""
    
    def __init__(self, app_instance):
        """Initialize component loader"""
        self.app = app_instance
        self.logger = logging.getLogger(__name__)
    
    def load_core_components(self):
        """Load core TikTok and database components"""
        try:
            # Database management (UNIFIED DATABASE INTEGRATION)
            from src.core.database_manager import DatabaseManager
            self.app.DatabaseManager = DatabaseManager
            self.logger.info("✅ Core database components loaded")
            
            # Core TikTok components
            from src.tracker.tiktok_tracker_optimized import TikTokTrackerOptimized
            from src.gui.live_feed_tab import LiveFeedTab
            from src.gui.tab_manager_lite import TabManagerLite
            
            self.app.TikTokTrackerLite = TikTokTrackerOptimized
            self.app.LiveFeedTab = LiveFeedTab
            self.app.TabManagerLite = TabManagerLite
            
            self.logger.info("✅ Core TikTok components loaded")
            return True
            
        except ImportError as e:
            self.logger.error(f"❌ Failed to load core components: {e}")
            messagebox.showerror("Import Error", f"Failed to load core components:\n{e}")
            return False
    
    def load_arduino_components(self):
        """Load Arduino Phase 4 components (optional)"""
        try:
            from src.gui.arduino_tab import ArduinoControlTab
            from arduino.controller import ArduinoController
            
            self.app.ArduinoControlTab = ArduinoControlTab
            self.app.ArduinoController = ArduinoController
            self.app.arduino_available = True
            
            self.logger.info("✅ Arduino Phase 4 components loaded")
            return True
            
        except ImportError as e:
            self.app.arduino_available = False
            self.app.ArduinoControlTab = None
            self.app.ArduinoController = None
            
            self.logger.warning(f"⚠️ Arduino components not available: {e}")
            return False
    
    def load_managers(self):
        """Load refactored manager components"""
        try:
            from src.app.menu_manager import MenuManager
            from src.app.tab_coordinator import TabCoordinator
            from src.app.account_coordinator import AccountCoordinator
            
            self.app.MenuManager = MenuManager
            self.app.TabCoordinator = TabCoordinator
            self.app.AccountCoordinator = AccountCoordinator
            
            self.logger.info("✅ Manager components loaded")
            return True
            
        except ImportError as e:
            self.logger.error(f"❌ Failed to load managers: {e}")
            messagebox.showerror("Import Error", f"Failed to load managers:\n{e}")
            return False
    
    def load_all_components(self):
        """Load all application components"""
        success = True
        
        # Load core components (required)
        if not self.load_core_components():
            success = False
        
        # Load managers (required)
        if not self.load_managers():
            success = False
        
        # Load Arduino components (optional)
        self.load_arduino_components()
        
        if success:
            self.logger.info("🎯 All components loaded successfully")
        else:
            self.logger.error("❌ Some critical components failed to load")
            sys.exit(1)
        
        return success
