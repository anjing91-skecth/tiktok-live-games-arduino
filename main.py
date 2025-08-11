"""
TikTok Live Lite - Main Entry Point (MODULAR VERSION)
=====================================================

Lightweight TikTok Live tracking application with Phase 4 Arduino features.
Clean modular architecture with separated components for better maintenance.
PHASE 4 REFACTORED VERSION - Main entry point now uses modular components.
"""

import sys
import tkinter as tk
from tkinter import messagebox
import logging

# Import modular components
from src.app.main_components import AppInitializer, ComponentLoader, UIBuilder


class TikTokLiteApp:
    """Main TikTok Live Lite Application - MODULAR VERSION"""
    
    def __init__(self):
        """Initialize application with modular components"""
        # Initialize core components
        self.initializer = AppInitializer()
        self.logger = self.initializer.initialize()
        
        # Create main window
        self.root = tk.Tk()
        
        # Load all components
        self.loader = ComponentLoader(self)
        self.loader.load_all_components()
        
        # Build UI
        self.ui_builder = UIBuilder(self)
        self.ui_builder.build_complete_ui()
        
        # Initialize application logic
        self._initialize_application()
    
    def _initialize_application(self):
        """Initialize application logic and coordinators"""
        try:
            # Initialize unified database
            db_path = "data/tiktok_live_lite.db"
            self.db_manager = self.DatabaseManager(db_path)
            self.db_manager.initialize_database()
            self.logger.info("✅ Unified database initialized")
            
            # Initialize coordinators (UI components are already created by UIBuilder)
            self.tab_coordinator = self.TabCoordinator(self.notebook, self)
            self.tab_coordinator.setup_all_tabs()
            
            self.account_coordinator = self.AccountCoordinator(self.account_combo, self.status_var, self)
            self.account_coordinator.load_accounts()
            
            # Connect button events (UI components should exist now)
            if hasattr(self, 'manage_accounts_btn'):
                self.manage_accounts_btn.config(command=self.account_coordinator.open_account_manager)
            if hasattr(self, 'arduino_center_btn') and hasattr(self, 'menu_manager'):
                self.arduino_center_btn.config(command=self.menu_manager.launch_arduino_center)
            
            self.logger.info("🎯 Application initialization completed successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize application: {e}")
            messagebox.showerror("Initialization Error", f"Failed to initialize:\n{e}")
            sys.exit(1)
    
    def run(self):
        """Run the application"""
        try:
            self.logger.info("🚀 [START] TikTok Live Lite Application")
            self.root.mainloop()
        except KeyboardInterrupt:
            self.logger.info("Application interrupted by user")
        except Exception as e:
            self.logger.error(f"Application error: {e}")
            messagebox.showerror("Error", f"Application error:\n{e}")
        finally:
            self.logger.info("Application closed")


def main():
    """Main entry point - Now simplified with modular components"""
    try:
        # Simple main function - complexity moved to modular components
        app = TikTokLiteApp()
        app.run()
        
    except Exception as e:
        print(f"Failed to start application: {e}")
        logging.error(f"Startup error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
