"""
Tab Coordinator for TikTok Live Lite Application
==============================================

Manages tab creation, coordination, and integration.
Extracted from main.py for better maintainability.
"""

import tkinter as tk
from tkinter import ttk


class TabCoordinator:
    """Coordinates tab creation and management"""
    
    def __init__(self, notebook, app_instance):
        """
        Initialize Tab Coordinator
        
        Args:
            notebook: Main ttk.Notebook widget
            app_instance: Reference to main application instance
        """
        self.notebook = notebook
        self.app = app_instance
        self.logger = app_instance.logger
    
    def setup_all_tabs(self):
        """Setup all application tabs"""
        # Create Live Feed tab (main tab)
        self.setup_live_feed_tab()
        
        # Add Arduino tabs if Phase 4 components available
        self.setup_arduino_tabs()
    
    def setup_live_feed_tab(self):
        """Setup the main Live Feed tab"""
        try:
            # Initialize Tab Manager (Live Feed tab)
            self.app.tab_manager = self.app.TabManagerLite(self.notebook, self.app.status_var)
            
            # Create Live Feed tab
            self.app.tab_manager.create_live_feed_tab_only()
            
            self.logger.info("✅ Live Feed tab created successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to create Live Feed tab: {e}")
            raise
    
    def setup_arduino_tabs(self):
        """Add Arduino Phase 4 tabs to main interface"""
        if not self.app.arduino_available:
            self.logger.info("⚠️ Arduino Phase 4 components not available - skipping Arduino tabs")
            return
            
        try:
            # Add Arduino Control tab only (WITH UNIFIED DATABASE)
            if self.app.ArduinoControlTab:
                arduino_frame = ttk.Frame(self.notebook)
                self.notebook.add(arduino_frame, text="🔌 Arduino")
                self.app.arduino_tab = self.app.ArduinoControlTab(arduino_frame)
                self.logger.info("✅ Arduino Control tab added with unified database")
                
            self.app.arduino_status_label.config(text="Phase 4 Active + DB", foreground='blue')
            
        except Exception as e:
            self.logger.error(f"Failed to add Arduino tabs: {e}")
            self.app.arduino_status_label.config(text="Phase 4 Error", foreground='red')
    
    def setup_arduino_tracker_connection(self, live_feed_tab):
        """Setup connection between Arduino tab and TikTok tracker using Event Bridge"""
        try:
            if hasattr(self.app, 'arduino_tab') and self.app.arduino_tab:
                # Connect immediately if tracker is already active
                if hasattr(live_feed_tab, 'current_tracker') and live_feed_tab.current_tracker:
                    self.app.arduino_tab.set_tracker(live_feed_tab.current_tracker)
                    self.logger.info("✅ Arduino tab connected to active tracker via Event Bridge")
                
                # Set Arduino connection callback untuk auto-connect pada tracking baru
                def arduino_tracker_callback(tracker):
                    """Callback dipanggil saat tracker baru dibuat"""
                    try:
                        if tracker and self.app.arduino_tab:
                            self.app.arduino_tab.set_tracker(tracker)
                            self.logger.info("✅ Arduino Event Bridge connected to new tracker")
                    except Exception as e:
                        self.logger.error(f"Error in Arduino tracker callback: {e}")
                
                # Set callback di live feed tracker (correct property name)
                if hasattr(live_feed_tab, 'tracker'):
                    live_feed_tab.tracker.arduino_connection_callback = arduino_tracker_callback
                    self.logger.info("✅ Arduino connection callback registered")
                
                self.logger.info("✅ Arduino-tracker connection setup complete")
                
        except Exception as e:
            self.logger.error(f"Error setting up Arduino-tracker connection: {e}")
    
    def connect_arduino_to_account(self, username):
        """Connect Arduino tab to selected account"""
        try:
            # UPDATE ARDUINO TAB WITH SELECTED ACCOUNT (INTEGRATION)
            if hasattr(self.app, 'arduino_tab') and self.app.arduino_tab:
                self.app.arduino_tab.set_account(username)
                self.logger.info(f"✅ Arduino tab updated for account: @{username}")
                
        except Exception as e:
            self.logger.error(f"Error connecting Arduino to account: {e}")
