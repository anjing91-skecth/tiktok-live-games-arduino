"""
Arduino Control Tab - Clean Business Logic Only
==============================================

File ini berisi business logic untuk Arduino tab tanpa duplikasi UI setup.
Semua UI setup sudah dipindahkan ke ArduinoUIManager.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sys
import os
import threading
import time
import json
from datetime import datetime

# Add paths for imports  
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'tiktok_live_lite'))

# Import database manager dengan struktur modular
try:
    from src.core.database_manager import DatabaseManager
except ImportError:
    try:
        from core.database_manager import DatabaseManager
    except ImportError:
        print("Warning: DatabaseManager not available")
        DatabaseManager = None

# Import serial for port scanning
try:
    import serial
    import serial.tools.list_ports
    SerialException = serial.SerialException
except ImportError:
    print("Warning: pyserial not available")
    serial = None
    SerialException = Exception

try:
    from arduino.controller import ArduinoController
except ImportError:
    print("Warning: ArduinoController not available")
    ArduinoController = None

# Import modular components
from .arduino_components import (StageRuleDialog, ArduinoDatabaseManager, ArduinoHardware, 
                                ArduinoStageManager, ArduinoTesting, ArduinoUIManager)
from .arduino_event_bridge import ArduinoEventBridge

class ArduinoControlTab:
    """Arduino control and monitoring tab with enhanced stages management"""
    
    def __init__(self, parent):
        self.parent = parent
        self.arduino_controller = None
        self.monitoring_active = False
        
        # DATABASE INTEGRATION - Shared database with Account Manager
        try:
            if DatabaseManager:
                self.db_manager = DatabaseManager("data/tiktok_live_lite.db")
            else:
                self.db_manager = None
        except Exception as e:
            print(f"Warning: Could not initialize database manager: {e}")
            self.db_manager = None
        
        # Initialize modular components
        self.arduino_db_manager = ArduinoDatabaseManager(self.db_manager)
        self.arduino_hardware = ArduinoHardware(self.log_message)
        self.stage_manager = ArduinoStageManager(self.log_message)
        self.arduino_testing = ArduinoTesting(self.log_message, self.arduino_hardware, self)  # Pass self reference
        self.ui_manager = ArduinoUIManager(self)
        
        # CURRENT ACCOUNT CONTEXT
        self.current_account_id = None
        self.current_account_username = None
        
        # Event Bridge untuk koneksi dengan Live Feed tracker
        self.event_bridge = ArduinoEventBridge(self)
        
        # Validation warnings
        self.validation_warning_label = None
        
        self.rules_data = []
        self.arduino_log = []
        self.stats = {
            'events_processed': 0,
            'triggers_executed': 0,
            'success_rate': 100.0,
            'last_trigger': 'None'
        }
        
        # Real-time viewer count dari TikTok callback (REAL DATA ONLY)
        self.current_viewer_count = 0
        self.last_callback_time = 0
        
        # Initialize tab UI
        self.setup_tab()
        
        # Load account-specific data
        self.load_account_arduino_data()
        
        # Load initial stage configuration
        self.load_stages_from_database()
        
        # Refresh UI setelah loading
        self.refresh_stage_ui()
    
    def load_account_arduino_data(self):
        """Load Arduino port setting untuk current account"""
        try:
            if hasattr(self, 'current_account_username') and self.current_account_username:
                account = self.arduino_db_manager.get_account_data(self.current_account_username)
                if account and 'arduino_port' in account:
                    self.port_var.set(account['arduino_port'])
                    self.log_message(f"✅ Loaded Arduino port for {self.current_account_username}: {account['arduino_port']}")
        except Exception as e:
            self.log_message(f"⚠️ Could not load account Arduino data: {e}")
    
    def refresh_stage_ui(self):
        """Refresh stage UI after loading from database"""
        # Refresh current stage selection to show loaded values
        self.on_stage_selected()
        
    def setup_tab(self):
        """Setup Arduino control tab dengan improved compact UI layout"""
        
        # Setup improved main layout using UI manager
        frames = self.ui_manager.setup_main_layout(self.parent)
        
        # Header section - Title dan Connection
        title_label = ttk.Label(frames['header'], text="🔌 Arduino Hardware Control", 
                               font=('Arial', 14, 'bold'), foreground='#1976D2')
        title_label.pack(pady=(0, 8))
        
        # Connection section di header
        self.ui_manager.setup_connection_section(frames['header'])
        
        # Left column - Management dan Controls  
        self.ui_manager.setup_stages_section(frames['left'])
        self.ui_manager.setup_rules_section(frames['left'])
        
        # Right column - Status, Stats, dan Log
        self.ui_manager.setup_status_section(frames['right'])
        self.ui_manager.setup_arduino_log_section(frames['right'])
        self.ui_manager.setup_testing_section(frames['right'])
        
        # Initialize real-time viewer count update thread
        self.initialize_viewer_count_tracker()
        
        # Initial port scan
        self.initial_port_scan()
    
    def initial_port_scan(self):
        """Initial port scan saat startup"""
        self.check_arduino_ports()
    
    def on_stage_selected(self, event=None):
        """Handle stage selection change dengan Retention System"""
        stage_num = int(self.stage_var.get().split()[-1])
        config = self.stage_manager.stages_config.get(stage_num, {})
        
        # Update UI fields
        self.stage_enable_var.set(config.get('active', False))
        self.viewer_min_var.set(str(config.get('viewer_min', 0)))
        self.delay_var.set(str(config.get('delay', 0)))
        self.retention_var.set(str(config.get('retention', 0)))
        
        # Stage 1 restrictions (read-only semua setting)
        if stage_num == 1:
            self.stage_enable_check.config(state='disabled')
            # Disable all input fields untuk Stage 1
            for widget in self.stage_settings_frame.winfo_children():
                if isinstance(widget, ttk.Frame):
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.Entry):
                            child.config(state='disabled')
            
            # Disable save button untuk Stage 1
            for widget in self.stage_settings_frame.winfo_children():
                if isinstance(widget, ttk.Frame):
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.Button) and "Save" in child.cget('text'):
                            child.config(state='disabled')
        else:
            self.stage_enable_check.config(state='normal')
            # Enable all input fields untuk Stage 2&3
            for widget in self.stage_settings_frame.winfo_children():
                if isinstance(widget, ttk.Frame):
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.Entry):
                            child.config(state='normal')
            
            # Enable save button untuk Stage 2&3
            for widget in self.stage_settings_frame.winfo_children():
                if isinstance(widget, ttk.Frame):
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.Button) and "Save" in child.cget('text'):
                            child.config(state='normal')
        
        # Clear any validation warnings when switching stages
        self.clear_validation_warning()
        
        self.update_override_button_state()
    
    def on_current_stage_selected(self, event=None):
        """Handle current stage dropdown selection untuk manual stage switching"""
        if not hasattr(self, 'current_stage_var'):
            return
            
        selected_stage = self.current_stage_var.get()
        stage_num = int(selected_stage.split()[-1])
        
        # Get current manual locked stage if any
        current_locked = self.stage_manager.manual_locked_stage
        
        if current_locked is not None and stage_num == current_locked:
            # Same stage selected - toggle back to auto mode
            self.stage_manager.toggle_override_mode(stage_num)
        else:
            # Different stage selected - switch to manual mode with this stage
            self.stage_manager.set_manual_stage_override(stage_num)
        
        # Update override button state
        self.update_override_button_state()
        
        # Update any visual indicators
        self.update_stage_display()
    
    def on_override_clicked(self):
        """Handle override button click untuk toggle manual/auto mode"""
        if not hasattr(self, 'current_stage_var'):
            return
            
        selected_stage = self.current_stage_var.get()
        stage_num = int(selected_stage.split()[-1])
        
        # Toggle override mode
        self.stage_manager.toggle_override_mode(stage_num)
        
        # Update button state
        self.update_override_button_state()
        
        # Update any visual indicators
        self.update_stage_display()
    
    def update_override_button_state(self):
        """Update override button text based on current state"""
        if not hasattr(self, 'override_var') or not hasattr(self, 'current_stage_var'):
            return
            
        selected_stage = self.current_stage_var.get()
        stage_num = int(selected_stage.split()[-1])
        
        button_state = self.stage_manager.get_override_button_state(stage_num)
        self.override_var.set(button_state.get('text', 'Manual Mode'))
    
    def update_stage_display(self):
        """Update current stage display berdasarkan stage manager state"""
        if not hasattr(self, 'current_stage_var'):
            return
            
        # Get current stage from manual lock or auto mode
        if self.stage_manager.manual_locked_stage is not None:
            current_stage = self.stage_manager.manual_locked_stage
        else:
            # In auto mode, get stage based on current viewer count
            current_stage = 1  # Default to stage 1, should be calculated from viewer thresholds
            
        self.current_stage_var.set(f'Stage {current_stage}')
    
    def on_stage_enable_changed(self):
        """Handle stage enable checkbox changes dengan dependency validation"""
        stage_num = int(self.stage_var.get().split()[-1])
        is_enabled = self.stage_enable_var.get()
        
        # Use stage manager untuk handle dependencies
        success = self.stage_manager.update_stage_enable_with_dependencies(stage_num, is_enabled)
        
        if not success:
            # Reset checkbox jika dependencies tidak terpenuhi
            old_value = self.stage_manager.stages_config[stage_num].get('active', False)
            self.stage_enable_var.set(old_value)
            
            # Show warning message
            if not is_enabled and stage_num == 2:
                messagebox.showwarning("Dependency Error", 
                                     "Cannot disable Stage 2 while Stage 3 is enabled!\nDisable Stage 3 first.")
            elif is_enabled and stage_num == 3:
                messagebox.showwarning("Dependency Error", 
                                     "Cannot enable Stage 3 while Stage 2 is disabled!\nEnable Stage 2 first.")
        
        # Update any visual indicators
        self.update_stage_display()
