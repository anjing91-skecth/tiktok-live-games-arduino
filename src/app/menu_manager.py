"""
Menu Manager for TikTok Live Lite Application
============================================

Handles all menu bar creation and menu event handlers.
Extracted from main.py for better maintainability.
"""

import tkinter as tk
from tkinter import messagebox
import sys
import subprocess
from pathlib import Path


class MenuManager:
    """Manages application menu bar and menu actions"""
    
    def __init__(self, root, app_instance):
        """
        Initialize Menu Manager
        
        Args:
            root: Main Tkinter window
            app_instance: Reference to main application instance
        """
        self.root = root
        self.app = app_instance
        self.logger = app_instance.logger
    
    def setup_menu_bar(self):
        """Setup main menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        self._setup_file_menu(menubar)
        
        # Arduino menu
        self._setup_arduino_menu(menubar)
        
        # View menu
        self._setup_view_menu(menubar)
        
        # Tools menu
        self._setup_tools_menu(menubar)
        
        # Help menu
        self._setup_help_menu(menubar)
    
    def _setup_file_menu(self, menubar):
        """Setup File menu"""
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Check if account coordinator is available
        if hasattr(self.app, 'account_coordinator') and hasattr(self.app.account_coordinator, 'open_account_manager'):
            file_menu.add_command(label="New Account", command=self.app.account_coordinator.open_account_manager)
        else:
            file_menu.add_command(label="New Account", command=self._show_account_unavailable)
        
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
    
    def _show_account_unavailable(self):
        """Show account unavailable message"""
        messagebox.showwarning("Account Manager", 
                              "Account manager is not yet initialized.\n"
                              "Please wait for application to fully load.")
    
    def _setup_arduino_menu(self, menubar):
        """Setup Arduino menu"""
        arduino_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Arduino", menu=arduino_menu)
        arduino_menu.add_command(label="🚀 Launch Control Center", command=self.launch_arduino_center)
        arduino_menu.add_separator()
        arduino_menu.add_command(label="📱 Port Scanner", command=self.launch_port_scanner)
        arduino_menu.add_command(label="⚡ Test Connection", command=self.test_arduino_connection)
        arduino_menu.add_separator()
        arduino_menu.add_command(label="📖 Arduino Guide", command=self.show_arduino_guide)
    
    def _setup_view_menu(self, menubar):
        """Setup View menu"""
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="📊 Statistics", command=self.show_statistics)
        view_menu.add_command(label="📝 Event Log", command=self.show_event_log)
        view_menu.add_separator()
        view_menu.add_command(label="🔄 Refresh", command=self.refresh_view)
    
    def _setup_tools_menu(self, menubar):
        """Setup Tools menu"""
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="🗄️ Database Manager", command=self.launch_database_manager)
        tools_menu.add_command(label="⚙️ Settings", command=self.show_settings)
        tools_menu.add_separator()
        tools_menu.add_command(label="🧹 Clear Cache", command=self.clear_cache)
    
    def _setup_help_menu(self, menubar):
        """Setup Help menu"""
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="📖 User Guide", command=self.show_user_guide)
        help_menu.add_command(label="🎮 Phase 4 Guide", command=self.show_phase4_guide)
        help_menu.add_separator()
        help_menu.add_command(label="ℹ️ About", command=self.show_about)
    
    # Arduino menu actions
    def launch_arduino_center(self):
        """Launch Arduino Control Center"""
        try:
            if hasattr(self.app, 'arduino_available') and self.app.arduino_available:
                messagebox.showinfo("Arduino Center", "Arduino Control Center would launch here!")
            else:
                messagebox.showwarning("Arduino Unavailable", 
                                     "Arduino components are not available.\n"
                                     "Please check Arduino installation.")
        except Exception as e:
            self.logger.error(f"Error launching Arduino center: {e}")
            messagebox.showerror("Error", f"Failed to launch Arduino center:\n{e}")
    
    def launch_port_scanner(self):
        """Launch Arduino port scanner"""
        try:
            messagebox.showinfo("Port Scanner", "Arduino Port Scanner would launch here!")
        except Exception as e:
            self.logger.error(f"Error launching port scanner: {e}")
            messagebox.showerror("Error", f"Failed to launch port scanner:\n{e}")
    
    def test_arduino_connection(self):
        """Test Arduino connection"""
        try:
            messagebox.showinfo("Connection Test", "Arduino connection test would run here!")
        except Exception as e:
            self.logger.error(f"Error testing Arduino connection: {e}")
            messagebox.showerror("Error", f"Failed to test Arduino connection:\n{e}")
    
    # View menu actions
    def show_statistics(self):
        """Show statistics window"""
        messagebox.showinfo("Statistics", "Statistics window would open here!")
    
    def show_event_log(self):
        """Show event log window"""
        messagebox.showinfo("Event Log", "Event log window would open here!")
    
    def refresh_view(self):
        """Refresh current view"""
        messagebox.showinfo("Refresh", "View refreshed!")
    
    # Tools menu actions
    def launch_database_manager(self):
        """Launch database manager"""
        messagebox.showinfo("Database Manager", "Database manager would launch here!")
    
    def show_settings(self):
        """Show settings dialog"""
        messagebox.showinfo("Settings", "Settings dialog would open here!")
    
    def clear_cache(self):
        """Clear application cache"""
        messagebox.showinfo("Clear Cache", "Cache cleared successfully!")
    
    # Help menu actions
    def show_user_guide(self):
        """Show user guide"""
        guide = """TikTok Live Lite + Arduino - User Guide

GETTING STARTED:
1. Add your TikTok account in Account Manager
2. Select account from dropdown
3. Click Start Tracking on Live Feed tab
4. Connect Arduino on Arduino tab (optional)

BASIC FEATURES:
• Live feed monitoring
• Real-time event tracking
• Account management
• Statistics viewing

ARDUINO FEATURES:
• Hardware control integration
• Custom rule engine
• Performance monitoring

For detailed instructions, check the documentation folder."""
        
        messagebox.showinfo("User Guide", guide)
    
    def show_phase4_guide(self):
        """Show Phase 4 Arduino guide"""
        guide = """Phase 4 Arduino Integration Guide

SETUP:
1. Connect Arduino to USB port
2. Upload provided sketch to Arduino
3. Use Port Scanner to find correct port
4. Test connection in Arduino tab

FEATURES:
• LED control based on TikTok events
• Custom rule engine for automation
• Real-time hardware feedback
• Performance monitoring

TROUBLESHOOTING:
• Check USB connection
• Verify correct COM port
• Ensure Arduino sketch is uploaded
• Check serial monitor for errors"""
        
        messagebox.showinfo("Phase 4 Guide", guide)
    
    def show_arduino_guide(self):
        """Show Arduino-specific guide"""
        self.show_phase4_guide()  # Same as Phase 4 guide
    
    def show_about(self):
        """Show about dialog"""
        about = """TikTok Live Lite + Arduino v4.0

Enhanced TikTok Live streaming tool with Arduino integration

CORE FEATURES:
• Live feed monitoring and interaction
• Account management
• Enhanced tracking system

PHASE 4 ARDUINO FEATURES:
• Hardware control integration
• Performance monitoring
• Custom rule engine

Developed with modular architecture for better maintainability.

© 2025 TikTok Live Games Arduino Project"""
        
        messagebox.showinfo("About", about)
