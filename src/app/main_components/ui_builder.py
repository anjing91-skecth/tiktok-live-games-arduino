"""
UI Builder Component
===================

Handles main UI construction and layout management.
Extracted from main.py for better maintainability.
"""

import tkinter as tk
from tkinter import ttk
import logging


class UIBuilder:
    """Handles main UI construction and layout"""
    
    def __init__(self, app_instance):
        """Initialize UI builder"""
        self.app = app_instance
        self.root = app_instance.root
        self.logger = logging.getLogger(__name__)
    
    def create_main_window(self):
        """Create and configure main window"""
        self.root.title("TikTok Live Lite + Arduino v4.0")
        self.root.geometry("1400x900")
        self.root.minsize(1000, 700)
        
        self.logger.info("✅ Main window configured")
    
    def create_menu_bar(self):
        """Create menu bar using MenuManager"""
        self.app.menu_manager = self.app.MenuManager(self.root, self.app)
        self.app.menu_manager.setup_menu_bar()
        
        self.logger.info("✅ Menu bar created")
    
    def create_main_container(self):
        """Create main container frame"""
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        return self.main_frame
    
    def create_toolbar(self, parent_frame):
        """Create top toolbar with account selection"""
        toolbar = ttk.Frame(parent_frame)
        toolbar.pack(fill=tk.X, pady=(0, 5))
        
        # Left side - App title
        left_toolbar = ttk.Frame(toolbar)
        left_toolbar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(left_toolbar, text="🎭 TikTok Live Lite", 
                 font=('Arial', 14, 'bold')).pack(side=tk.LEFT)
        
        # Center - Account selection
        center_toolbar = ttk.Frame(toolbar)
        center_toolbar.pack(side=tk.LEFT, padx=20)
        
        ttk.Label(center_toolbar, text="📱 Account:", 
                 font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=(0, 5))
        
        self.app.account_var = tk.StringVar()
        self.app.account_combo = ttk.Combobox(center_toolbar, textvariable=self.app.account_var, 
                                             state="readonly", width=25, font=('Arial', 10))
        self.app.account_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        self.app.manage_accounts_btn = ttk.Button(center_toolbar, text="⚙️ Manage Accounts")
        self.app.manage_accounts_btn.pack(side=tk.LEFT)
        
        # Right side - Status
        right_toolbar = ttk.Frame(toolbar)
        right_toolbar.pack(side=tk.RIGHT)
        
        self.app.status_var = tk.StringVar(value="Ready")
        ttk.Label(right_toolbar, textvariable=self.app.status_var, 
                 font=('Arial', 9)).pack(side=tk.RIGHT)
        
        self.logger.info("✅ Toolbar created")
        return toolbar
    
    def create_notebook(self, parent_frame):
        """Create notebook for tabs"""
        self.app.notebook = ttk.Notebook(parent_frame)
        self.app.notebook.pack(fill=tk.BOTH, expand=True)
        
        self.logger.info("✅ Notebook created")
        return self.app.notebook
    
    def create_arduino_status(self, parent_frame):
        """Create Arduino integration status bar"""
        arduino_status_frame = ttk.Frame(parent_frame)
        arduino_status_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 0))
        
        ttk.Label(arduino_status_frame, text="🎮 Arduino Integration:", 
                 font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
        
        status_text = "Phase 4 Ready" if self.app.arduino_available else "Not Available"
        status_color = 'green' if self.app.arduino_available else 'orange'
        
        self.app.arduino_status_label = ttk.Label(arduino_status_frame, text=status_text, 
                                                 font=('Arial', 9), foreground=status_color)
        self.app.arduino_status_label.pack(side=tk.LEFT, padx=(5, 0))
        
        self.app.arduino_center_btn = ttk.Button(arduino_status_frame, text="🚀 Launch Arduino Center")
        self.app.arduino_center_btn.pack(side=tk.RIGHT)
        
        self.logger.info("✅ Arduino status bar created")
        return arduino_status_frame
    
    def build_complete_ui(self):
        """Build complete UI structure"""
        # Create main window
        self.create_main_window()
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create main container
        main_frame = self.create_main_container()
        
        # Create toolbar
        self.create_toolbar(main_frame)
        
        # Create notebook
        self.create_notebook(main_frame)
        
        # Create Arduino status
        self.create_arduino_status(main_frame)
        
        self.logger.info("🎨 Complete UI structure built successfully")
        return True
