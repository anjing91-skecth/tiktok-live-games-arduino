"""
Arduino Control Tab - Modular Version
====================================

Refactored version using modular components while maintaining
exact same UI functionality and user experience.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sys
import os
import threading
import time
import json

# Import component modules
from .arduino_components.arduino_ui_manager import ArduinoUIManager
from .arduino_components.arduino_hardware import ArduinoHardware
from .arduino_components.arduino_database_manager import ArduinoDatabaseManager
from .arduino_components.arduino_testing import ArduinoTesting
from .arduino_components.arduino_stage_manager import ArduinoStageManager
from .arduino_components.arduino_rule_dialog import StageRuleDialog
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
        
        # Stage timer system initialization
        self.stage_timer_active = False
        self.stage_timer_target = None
        self.stage_timer_start_time = None
        self.stage_timer_duration = 0
        self.manual_stage_override = False
        
        self.setup_tab()
        self.scan_ports_simple()
        
        # Initial welcome message dengan default stages DISABLED
        self.log_message("🚀 Arduino Control Tab initialized - REAL DATA MODE")
        self.log_message("📊 Live Status akan menampilkan viewer count REAL dari TikTok")
        self.log_message("⚡ Hanya menggunakan callback dari TikTok WebSocket API")
        
        # DEFAULT: Stages 2 & 3 DISABLED (sesuai requirement)
        self.log_message("🔧 Default stage configuration (SINKRON validasi & runtime):")
        self.log_message("✅ Stage 1: Always active (default)")
        self.log_message("❌ Stage 2: Disabled (min: 30 viewers, retention: 5)")
        self.log_message("❌ Stage 3: Disabled (min: 80 viewers, retention: 10)")
        self.log_message("📋 Validation Rules (+10 Buffer):")
        self.log_message("   - Stage 2 min > Stage 1 (0) + retention (0) + 10 = >10 viewers")
        self.log_message("   - Stage 3 min > Stage 2 (30) + retention (5) + 10 = >45 viewers") 
        self.log_message("   - Runtime progression: NAIK saat viewers ≥ min, TURUN saat < min")
        self.log_message("   - Retention: INSTANT naik saat ≥ (min+retention), turun saat ≤ (min-retention)")
        self.log_message("   - Delay: NAIK pakai delay target stage, TURUN pakai delay current stage")
        self.log_message("   - Same values: delay UP = delay DOWN, retention UP = retention DOWN")
        
        # Refresh stage display
        self.on_stage_selected()
        
    def set_account(self, account_username: str):
        """Set current account and load all settings from database using modular manager"""
        account = self.arduino_db_manager.set_account(account_username, self.log_message)
        if account:
            self.current_account_id = account['id']
            self.current_account_username = account_username
            
            # Load stage settings from database and update stage manager
            loaded_stages = self.arduino_db_manager.load_stage_settings_from_db(
                self.stage_manager.stages_config, self.log_message
            )
            self.stage_manager.stages_config = loaded_stages
            
            # Load rules from database  
            self.rules_data = self.arduino_db_manager.load_rules_from_db(self.log_message)
            self.refresh_rules_display()
            
            # Load Arduino port if saved
            if account.get('arduino_port'):
                self.port_var.set(account['arduino_port'])
                self.log_message(f"✅ Loaded Arduino port: {account['arduino_port']}")
            
            # Refresh UI
            self.refresh_stage_ui()
            self.log_message(f"✅ All settings loaded for @{account_username}")
    
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
        
        # Right column - Status dan Log
        self.ui_manager.setup_live_status_section(frames['right'])
        self.ui_manager.setup_log_section(frames['right'])
        
        # Start monitoring and register callbacks
        self.start_monitoring()
        self.register_viewer_callback()
    
    def register_viewer_callback(self):
        """Register callback untuk mendapat viewer updates dari TikTokConnector"""
        try:
            import sys
            
            # Cari TikTokConnector di loaded modules
            for name, module in sys.modules.items():
                # Cek apakah ada TikTokConnector
                if hasattr(module, 'tiktok_connector') and module.tiktok_connector:
                    connector = module.tiktok_connector
                    if hasattr(connector, 'callbacks'):
                        # Register callback untuk viewer updates
                        connector.callbacks['arduino_viewer_update'] = self.on_viewer_count_update
                        self.log_message("✅ Registered viewer callback with TikTokConnector")
                        return
                
                # Cek via account_manager->connector
                if hasattr(module, 'account_manager') and module.account_manager:
                    am = module.account_manager
                    if hasattr(am, 'tiktok_connector') and am.tiktok_connector:
                        connector = am.tiktok_connector
                        if hasattr(connector, 'callbacks'):
                            connector.callbacks['arduino_viewer_update'] = self.on_viewer_count_update
                            self.log_message("✅ Registered viewer callback via AccountManager")
                            return
            
            # Fallback: Search dalam widget hierarchy
            root = self.parent
            while hasattr(root, 'master') and root.master:
                root = root.master
            
            def find_connector_recursive(widget, depth=0):
                if depth > 5:
                    return None
                    
                if hasattr(widget, 'tiktok_connector') and widget.tiktok_connector:
                    return widget.tiktok_connector
                
                if hasattr(widget, 'account_manager') and widget.account_manager:
                    am = widget.account_manager
                    if hasattr(am, 'tiktok_connector') and am.tiktok_connector:
                        return am.tiktok_connector
                
                # Search children
                try:
                    if hasattr(widget, 'winfo_children'):
                        for child in widget.winfo_children():
                            result = find_connector_recursive(child, depth + 1)
                            if result:
                                return result
                except:
                    pass
                
                return None
            
            connector = find_connector_recursive(root)
            if connector and hasattr(connector, 'callbacks'):
                connector.callbacks['arduino_viewer_update'] = self.on_viewer_count_update
                self.log_message("✅ Registered viewer callback via widget search")
                
        except Exception as e:
            self.log_message(f"⚠️ Could not register viewer callback: {e}")
    
    def on_viewer_count_update(self, viewer_count):
        """Callback function untuk menerima REAL viewer count dari TikTokConnector"""
        try:
            import time
            
            # Update instance variable dengan REAL viewer count dari TikTok
            self.current_viewer_count = viewer_count
            self.last_callback_time = time.time()
            
            # Update viewer count display dan stage progress
            self.update_viewer_display(viewer_count)
            
            # Update tracker status to connected when receiving data
            self.update_tracker_status(True)
            
            # Update last update time
            if hasattr(self, 'last_update_label'):
                current_time = time.strftime("%H:%M:%S")
                self.last_update_label.config(text=current_time)
            
            # Update statistics
            if hasattr(self, 'triggers_label'):
                self.triggers_label.config(text=str(self.stats.get('triggers_executed', 0)))
            
            # Check untuk stage progression (hanya dalam auto mode)
            if not self.manual_stage_override:
                self.check_stage_progression(viewer_count)
            
            # Update next stage info
            self.update_next_stage_info(viewer_count)
            
            # Log milestone viewers untuk tracking real data
            if not hasattr(self, '_last_logged_viewers'):
                self._last_logged_viewers = 0
            
            # Log setiap perubahan signifikan (5+ viewers atau milestone)
            if (abs(viewer_count - self._last_logged_viewers) >= 5 or 
                viewer_count in [10, 20, 50, 100, 200, 500]):
                self.log_message(f"👥 Real TikTok viewers: {viewer_count}")
                self._last_logged_viewers = viewer_count
            
            # Log stage milestones
            if viewer_count >= 50 and self._last_logged_viewers < 50:
                self.log_message(f"🎯 Stage 2 threshold reached: {viewer_count} viewers")
            elif viewer_count >= 200 and self._last_logged_viewers < 200:
                self.log_message(f"🎯 Stage 3 threshold reached: {viewer_count} viewers")
            
            # Log jika ini callback pertama
            if not hasattr(self, '_callback_success_logged'):
                self.log_message("✅ REAL viewer data from TikTok WebSocket connected!")
                self._callback_success_logged = True
                
        except Exception as e:
            self.log_message(f"❌ Error in real viewer callback: {e}")
    
    # UI callback methods (placeholder untuk UI manager)
    def add_new_rule(self):
        """Add new Arduino rule using proper dialog"""
        try:
            dialog = StageRuleDialog(self.parent)
            self.parent.wait_window(dialog.dialog)
            
            if dialog.result:
                # Add to memory
                self.rules_data.append(dialog.result)
                self.refresh_rules_display()
                
                # SAVE TO DATABASE using modular manager
                success = self.arduino_db_manager.save_rule_to_db(dialog.result, self.log_message)
                if success:
                    self.log_message(f"✅ Rule '{dialog.result['name']}' created and saved")
                else:
                    self.log_message(f"⚠️ Rule '{dialog.result['name']}' created but not saved to database")
        except Exception as e:
            self.log_message(f"❌ Error creating rule: {e}")
    
    def edit_selected_rule(self):
        """Edit selected rule using proper dialog"""
        try:
            selection = self.rules_tree.selection()
            if not selection:
                messagebox.showwarning("Warning", "Please select a rule to edit")
                return
                
            item = selection[0]
            rule_name = self.rules_tree.item(item, 'text')
            
            # Find rule data by name
            rule_data = None
            rule_index = None
            for i, rule in enumerate(self.rules_data):
                if rule['name'] == rule_name:
                    rule_data = rule
                    rule_index = i
                    break
                    
            if rule_data is None:
                messagebox.showerror("Error", "Could not find rule data")
                return
                
            dialog = StageRuleDialog(self.parent, rule_data)
            self.parent.wait_window(dialog.dialog)
            
            if dialog.result and rule_index is not None:
                self.rules_data[rule_index] = dialog.result
                self.refresh_rules_display()
                
                # UPDATE IN DATABASE using modular manager
                success = self.arduino_db_manager.save_rule_to_db(dialog.result, self.log_message)
                if success:
                    self.log_message(f"✅ Rule '{dialog.result['name']}' updated and saved")
                else:
                    self.log_message(f"⚠️ Rule '{dialog.result['name']}' updated but not saved to database")
        except Exception as e:
            self.log_message(f"❌ Error editing rule: {e}")
    
    def delete_selected_rule(self):
        """Delete selected rule with confirmation"""
        try:
            selection = self.rules_tree.selection()
            if not selection:
                messagebox.showwarning("Warning", "Please select a rule to delete")
                return
                
            item = selection[0]
            rule_name = self.rules_tree.item(item, 'text')
            
            if messagebox.askyesno("Confirm Delete", f"Delete rule '{rule_name}'?"):
                # Remove from memory
                for i, rule in enumerate(self.rules_data):
                    if rule['name'] == rule_name:
                        del self.rules_data[i]
                        break
                
                self.refresh_rules_display()
                
                # DELETE FROM DATABASE using modular manager
                success = self.arduino_db_manager.delete_rule_from_db(rule_name, self.log_message)
                if success:
                    self.log_message(f"✅ Rule '{rule_name}' deleted successfully")
                else:
                    self.log_message(f"⚠️ Rule '{rule_name}' deleted from memory but not from database")
        except Exception as e:
            self.log_message(f"❌ Error deleting rule: {e}")

    def check_arduino_ports(self):
        """Check dan scan port Arduino yang tersedia menggunakan hardware component"""
        try:
            self.log_message("🔍 Scanning for Arduino ports...")
            
            available_ports = self.arduino_hardware.scan_ports()
            arduino_ports = []
            
            for port_device in available_ports:
                try:
                    # Get port description
                    if serial:
                        ports = serial.tools.list_ports.comports()
                        port_desc = "Unknown"
                        for port in ports:
                            if port.device == port_device:
                                port_desc = port.description
                                break
                    else:
                        port_desc = "Serial library not available"
                    
                    # Check if port is likely Arduino
                    arduino_keywords = ['arduino', 'ch340', 'ch341', 'ftdi', 'usb serial']
                    is_arduino = any(keyword in port_desc.lower() for keyword in arduino_keywords)
                    
                    if is_arduino:
                        arduino_ports.append(f"{port_device} - {port_desc}")
                        self.log_message(f"🎯 Found Arduino port: {port_device} ({port_desc})")
                    else:
                        self.log_message(f"📍 Found port: {port_device} ({port_desc})")
                        
                except Exception:
                    arduino_ports.append(port_device)
            
            # Update dropdown
            if hasattr(self, 'port_combo'):
                self.port_combo['values'] = arduino_ports
                
                if arduino_ports:
                    self.port_combo.set(arduino_ports[0])  # Select first Arduino port
                    self.log_message(f"✅ Found {len(arduino_ports)} Arduino port(s)")
                else:
                    self.log_message("⚠️ No Arduino ports detected")
                
        except Exception as e:
            self.log_message(f"❌ Error scanning ports: {e}")
    
    def toggle_connection(self):
        """Toggle Arduino connection using hardware component"""
        if self.arduino_hardware.is_connected():
            self.disconnect_arduino()
        else:
            self.connect_arduino()
    
    def connect_arduino(self):
        """Connect to Arduino using hardware component"""
        try:
            selected_port = self.port_var.get()
            if not selected_port:
                messagebox.showerror("Error", "Please select a port first")
                return
                
            port = selected_port.split(' - ')[0]
            
            # Use hardware component to connect
            if self.arduino_hardware.connect(port):
                self.arduino_connected = True
                self.connection_status.config(text="✅ Connected", foreground='green')
                self.connect_btn.config(text="Disconnect")
                
                # Test LED
                self.arduino_hardware.send_command("LED_ON")
                
                # Save port to database
                if self.current_account_id:
                    self.arduino_db_manager.save_arduino_port(self.current_account_id, port, self.log_message)
                
                self.log_message("✅ Arduino connected successfully")
            else:
                messagebox.showerror("Connection Failed", "Could not connect to Arduino")
            
        except Exception as e:
            self.log_message(f"❌ Connection error: {e}")
            messagebox.showerror("Error", f"Connection failed:\n{e}")
    
    def disconnect_arduino(self):
        """Disconnect from Arduino using hardware component"""
        try:
            # Turn off LED indicator
            self.arduino_hardware.send_command("LED_OFF")
            
            # Disconnect using hardware component
            if self.arduino_hardware.disconnect():
                self.arduino_connected = False
                if hasattr(self, 'connection_status'):
                    self.connection_status.config(text="🔴 Disconnected", foreground='red')
                if hasattr(self, 'connect_btn'):
                    self.connect_btn.config(text="🔌 Connect")
                
                self.log_message("🔌 Disconnected from Arduino")
            else:
                self.log_message("⚠️ Disconnect failed")
                
        except Exception as e:
            self.log_message(f"❌ Error disconnecting: {e}")
    
    def test_led(self):
        """Test LED functionality using Arduino testing component"""
        try:
            selected_port = self.port_var.get()
            port = selected_port.split(' - ')[0] if selected_port else None
            
            # Use testing component
            self.arduino_testing.test_led_blink(count=3, port=port)
            
        except Exception as e:
            self.log_message(f"❌ LED test error: {e}")
            messagebox.showerror("Error", f"LED test failed:\n{e}")
    
    def test_pin(self):
        """Test individual pin functionality using Arduino testing component"""
        try:
            # Get parent window for dialog
            parent_window = self.parent if hasattr(self, 'parent') else None
            
            # Use testing component
            self.arduino_testing.show_pin_test_dialog(parent_window)
            
        except Exception as e:
            self.log_message(f"❌ Pin test error: {e}")
            messagebox.showerror("Error", f"Pin test failed:\n{e}")
    
    def scan_ports_simple(self):
        """Initial port scan saat startup"""
        self.check_arduino_ports()
    
    def on_stage_selected(self, event=None):
        """Handle stage selection change dengan Stage 1 Lock dan enhanced UI management"""
        stage_num = int(self.stage_var.get().split()[-1])
        config = self.stage_manager.stages_config.get(stage_num, {})
        
        # Update UI fields
        self.stage_enable_var.set(config.get('active', False))
        self.viewer_min_var.set(str(config.get('viewer_min', 0)))
        self.delay_var.set(str(config.get('delay', 0)))
        self.retention_var.set(str(config.get('retention', 0)))
        
        # Stage 1 restrictions - SEMUA SETTINGS LOCKED/DISABLED
        if stage_num == 1:
            # Disable stage enable checkbox (Stage 1 always enabled)
            if hasattr(self, 'stage_enable_check'):
                self.stage_enable_check.config(state='disabled')
            
            # Disable all input fields untuk Stage 1
            if hasattr(self, 'stage_settings_frame'):
                for widget in self.stage_settings_frame.winfo_children():
                    if isinstance(widget, ttk.Frame):
                        for child in widget.winfo_children():
                            if isinstance(child, ttk.Entry):
                                child.config(state='disabled')
                            elif isinstance(child, ttk.Button) and "Save" in str(child.cget('text')):
                                child.config(state='disabled')
            
            # Disable individual input widgets if they exist
            for attr_name in ['viewer_min_entry', 'delay_entry', 'retention_entry', 'bonus_entry']:
                if hasattr(self, attr_name):
                    getattr(self, attr_name).config(state='disabled')
                    
            # Show info message about Stage 1 being locked
            self.show_validation_warning("ℹ️ Stage 1 settings are locked (default base stage)")
            
        else:
            # Stage 2 & 3 - Enable all settings
            if hasattr(self, 'stage_enable_check'):
                self.stage_enable_check.config(state='normal')
            
            # Enable all input fields untuk Stage 2&3
            if hasattr(self, 'stage_settings_frame'):
                for widget in self.stage_settings_frame.winfo_children():
                    if isinstance(widget, ttk.Frame):
                        for child in widget.winfo_children():
                            if isinstance(child, ttk.Entry):
                                child.config(state='normal')
                            elif isinstance(child, ttk.Button) and "Save" in str(child.cget('text')):
                                child.config(state='normal')
            
            # Enable individual input widgets if they exist
            for attr_name in ['viewer_min_entry', 'delay_entry', 'retention_entry', 'bonus_entry']:
                if hasattr(self, attr_name):
                    getattr(self, attr_name).config(state='normal')
                    
            # Clear info message
            self.clear_validation_warning()
        
        # Update override button state based on new selection
        self.update_override_button_state()
    
    def on_current_stage_selected(self, event=None):
        """Handle current stage dropdown selection untuk manual stage switching"""
        if not hasattr(self, 'current_stage_var'):
            return
            
        selected_stage = self.current_stage_var.get()
        stage_num = int(selected_stage.split()[-1])
        
        # Check if stage is enabled/available
        if not self.stage_manager.stages_config[stage_num]['active']:
            self.log_message(f"❌ Stage {stage_num} is disabled and cannot be selected")
            # Reset dropdown to current stage
            if self.stage_manager.manual_stage_override:
                self.current_stage_var.set(f'Stage {self.stage_manager.manual_locked_stage}')
            else:
                self.current_stage_var.set(f'Stage {self.stage_manager.current_stage}')
            return
        
        # If in manual mode and same stage selected, no change needed
        if (self.stage_manager.manual_stage_override and 
            self.stage_manager.manual_locked_stage == stage_num):
            return
            
        # Switch to manual mode with selected stage
        success = self.stage_manager.set_manual_stage_override(stage_num)
        if success:
            self.log_message(f"🔒 Manual mode: Locked to Stage {stage_num}")
            # Update override button state
            self.update_override_button_state()
            # Update any visual indicators
            self.update_stage_display()
        else:
            # Reset dropdown if failed
            if self.stage_manager.manual_stage_override:
                self.current_stage_var.set(f'Stage {self.stage_manager.manual_locked_stage}')
            else:
                self.current_stage_var.set(f'Stage {self.stage_manager.current_stage}')
    
    def on_override_clicked(self):
        """Handle override button click untuk toggle manual/auto mode"""
        if not hasattr(self, 'current_stage_var'):
            return
            
        selected_stage = self.current_stage_var.get()
        stage_num = int(selected_stage.split()[-1])
        
        # Toggle override mode menggunakan stage manager
        result = self.stage_manager.toggle_override_mode(stage_num)
        
        if result['success']:
            self.log_message(result['message'])
            # Update button state
            self.update_override_button_state()
            # Update any visual indicators
            self.update_stage_display()
        else:
            self.log_message(f"❌ Failed to toggle override: {result.get('message', 'Unknown error')}")
    
    def update_override_button_state(self):
        """Update override button text based on current state"""
        if not hasattr(self, 'override_var') or not hasattr(self, 'current_stage_var'):
            return
            
        selected_stage = self.current_stage_var.get()
        stage_num = int(selected_stage.split()[-1])
        
        button_state = self.stage_manager.get_override_button_state(stage_num)
        self.override_var.set(button_state.get('text', 'Manual Mode'))
    
    def update_stage_display(self):
        """Update current stage display dan sync dropdown dengan stage manager state"""
        if not hasattr(self, 'current_stage_var'):
            return
            
        # Get current stage from stage manager
        current_stage = self.stage_manager.current_stage
        
        # Update dropdown to reflect current stage
        self.current_stage_var.set(f'Stage {current_stage}')
        
        # Update button text
        self.update_override_button_state()
        
        # Update any other visual indicators if they exist
        if hasattr(self, 'stage_mode_indicator'):
            if self.stage_manager.manual_stage_override:
                self.stage_mode_indicator.config(
                    text="[MANUAL]",
                    foreground='#F44336'
                )
            else:
                self.stage_mode_indicator.config(
                    text="[AUTO]",
                    foreground='#4CAF50'
                )
    
    def on_stage_enable_changed(self):
        """Handle stage enable checkbox changes dengan dependency validation dan auto fallback"""
        stage_num = int(self.stage_var.get().split()[-1])
        is_enabled = self.stage_enable_var.get()
        
        # Use stage manager untuk handle dependencies dan fallback
        result = self.stage_manager.update_stage_enable_with_dependencies(stage_num, is_enabled)
        
        if not result['success']:
            # Reset checkbox jika dependencies tidak terpenuhi
            old_value = self.stage_manager.stages_config[stage_num].get('active', False)
            self.stage_enable_var.set(old_value)
            
            # Show warning messages
            for warning in result['warnings']:
                self.log_message(warning)
        else:
            # Log all successful changes
            for change in result['changes']:
                self.log_message(f"✅ {change}")
        
        # Update current stage display to reflect any fallback
        self.update_stage_display()
        
        # Update override button state
        self.update_override_button_state()
    
    def on_stage_checkbox_change(self):
        """Handle stage checkbox changes dengan Stage Dependencies"""
        stage_num = int(self.stage_var.get().split()[-1])
        is_enabled = self.stage_enable_var.get()
        
        # STAGE DEPENDENCIES LOGIC
        if is_enabled:
            # Auto-enable lower stages if higher stage enabled
            if stage_num == 3 and not self.stage_manager.stages_config[2]['active']:
                self.stage_manager.stages_config[2]['active'] = True
                self.log_message("🔗 Auto-enabled Stage 2 (dependency for Stage 3)")
                
        else:
            # Auto-disable higher stages if lower stage disabled
            if stage_num == 2 and self.stage_manager.stages_config[3]['active']:
                self.stage_manager.stages_config[3]['active'] = False
                self.log_message("🔗 Auto-disabled Stage 3 (Stage 2 dependency removed)")
                
        # Update config
        self.stage_manager.stages_config[stage_num]['active'] = is_enabled
        
        # Check if current stage needs to change due to dependency
        current_stage = self.get_current_stage_number()
        if not is_enabled and current_stage == stage_num:
            # Current stage disabled - auto turun ke available stage
            self.auto_fallback_stage()
        
        self.update_override_button_state()
        
        stage_name = self.stage_var.get()
        self.log_message(f"{stage_name}: {'Enabled' if is_enabled else 'Disabled'}")
    
    def auto_fallback_stage(self):
        """Auto fallback ke stage yang tersedia jika current stage di-disable"""
        try:
            # Cari stage tertinggi yang aktif
            fallback_stage = 1  # Default ke Stage 1
            for stage_num in [3, 2]:
                if self.stage_manager.stages_config[stage_num]['active']:
                    fallback_stage = stage_num
                    break
            
            self.set_current_stage(fallback_stage)
            self.log_message(f"🔄 Auto-fallback to Stage {fallback_stage} (dependency cascade)")
            
        except Exception as e:
            self.log_message(f"❌ Error in auto-fallback: {e}")
    
    def clear_validation_warning(self):
        """Clear validation warning message"""
        if self.validation_warning_label:
            self.validation_warning_label.config(text="")
    
    def show_validation_warning(self, message):
        """Show validation warning message"""
        if self.validation_warning_label:
            self.validation_warning_label.config(text=message)
    
    def update_override_button_state(self):
        """Update override button state dengan Enhanced Logic - Bisa override ke stage lain"""
        try:
            stage_num = int(self.stage_var.get().split()[-1])
            is_enabled = self.stage_enable_var.get()
            current_stage = self.get_current_stage_number()
            
            if self.manual_stage_override:
                # Mode Manual: Override enabled untuk semua stage (termasuk Stage 1 sebagai fallback)
                if stage_num == current_stage:
                    # Current stage - tampilkan status tapi disable button
                    self.override_btn.config(state='disabled', text="🔒 Current Stage")
                else:
                    # Stage lain - cek apakah bisa override
                    if stage_num == 1:
                        # Stage 1 SELALU bisa di-override sebagai fallback dalam mode manual
                        self.override_btn.config(state='normal', text="🎯 Switch to Stage 1 (Fallback)")
                    elif is_enabled:
                        # Stage enabled - bisa override
                        self.override_btn.config(state='normal', text=f"🎯 Switch to Stage {stage_num}")
                    else:
                        # Stage disabled - tidak bisa override
                        self.override_btn.config(state='disabled', text="❌ Stage disabled")
                
                self.reset_auto_btn.config(state='normal')
                
            else:
                # Mode Auto: Stage 1 tidak bisa di-override dalam mode auto (untuk start manual mode)
                if stage_num == 1:
                    self.override_btn.config(state='disabled', text="❌ Stage 1 is default (auto mode)")
                elif is_enabled:
                    self.override_btn.config(state='normal')
                    # Update button text untuk clarity
                    if stage_num == current_stage:
                        self.override_btn.config(text="🔒 Lock Stage")  # Lock current stage
                    else:
                        self.override_btn.config(text=f"🎯 Override to Stage {stage_num}")  # Override to different stage
                else:
                    self.override_btn.config(state='disabled', text="❌ Stage disabled")
                        
                self.reset_auto_btn.config(state='disabled')
                
        except Exception as e:
            pass  # Silent fail
    
    def save_stage_settings(self):
        """Save stage settings dengan Validation dan Stage Dependencies - Stage 1 DISABLED"""
        try:
            stage_num = int(self.stage_var.get().split()[-1])
            
            # Stage 1 tidak bisa di-setting - BLOCK dengan pesan
            if stage_num == 1:
                self.show_validation_warning("⚠️ Stage 1 settings are locked (default stage)")
                messagebox.showwarning("Settings Locked", "Stage 1 is the default stage and cannot be modified.")
                return
                
            # Parse input values
            try:
                viewer_min = int(self.viewer_min_var.get() or 0)
                delay = int(self.delay_var.get() or 0)
                retention = int(self.retention_var.get() or 0)
                is_active = self.stage_enable_var.get()
            except ValueError:
                self.show_validation_warning("❌ Please enter valid numeric values")
                return
            
            # VALIDATION: Check minimum values against lower stages
            validation_error = self.validate_stage_settings(stage_num, viewer_min, retention)
            if validation_error:
                self.show_validation_warning(validation_error)
                return
                
            # Clear validation warning
            self.clear_validation_warning()
            
            # STAGE DEPENDENCIES: Handle enable/disable cascade
            if is_active:
                # Auto-enable lower stages
                if stage_num == 3 and not self.stage_manager.stages_config[2]['active']:
                    self.stage_manager.stages_config[2]['active'] = True
                    self.log_message("🔗 Auto-enabled Stage 2 (dependency for Stage 3)")
            
            # Save configuration to memory
            self.stage_manager.stages_config[stage_num] = {
                'viewer_min': viewer_min,
                'delay': delay,
                'retention': retention,
                'active': is_active,
                'bonus': self.stage_manager.stages_config[stage_num].get('bonus', 0)  # Preserve bonus
            }
            
            # SAVE TO DATABASE using modular manager
            success = self.arduino_db_manager.save_stage_settings(
                stage_num, viewer_min, delay, retention, is_active,
                self.stage_manager.stages_config[stage_num]['bonus'], self.log_message
            )
            
            self.log_message(f"📊 Stage {stage_num} config: Min:{viewer_min}, Delay:{delay}s, Retention:{retention}")
            
        except Exception as e:
            self.show_validation_warning(f"❌ Error saving settings: {e}")
    
    def validate_stage_settings(self, stage_num, viewer_min, retention):
        """Validate stage settings dengan +10 buffer requirement"""
        try:
            # Check against lower stages - DENGAN +10 BUFFER REQUIREMENT
            if stage_num == 2:
                # Stage 2 harus > Stage 1 + retention + 10 buffer
                stage1_min = self.stage_manager.stages_config[1]['viewer_min']  # Always 0
                stage1_retention = self.stage_manager.stages_config[1]['retention']  # Always 0
                min_required = stage1_min + stage1_retention + 10  # +10 buffer
                if viewer_min <= min_required:
                    return f"❌ Stage 2 min viewers harus > {min_required} (Stage 1 min + retention + 10 buffer)"
                    
            elif stage_num == 3:
                # Stage 3 harus > Stage 2 min + retention + 10 buffer
                stage2_min = self.stage_manager.stages_config[2]['viewer_min']
                stage2_retention = self.stage_manager.stages_config[2]['retention']
                min_required = stage2_min + stage2_retention + 10  # +10 buffer
                
                if viewer_min <= min_required:
                    return f"❌ Stage 3 min viewers harus > {min_required} (Stage 2: {stage2_min} + retention: {stage2_retention} + 10 buffer)"
            
            # Validasi retention tidak boleh > min_viewers (logis)
            if retention >= viewer_min and viewer_min > 0:
                return f"❌ Retention ({retention}) harus < Min viewers ({viewer_min})"
            
            return None  # No validation error
            
        except Exception:
            return "❌ Validation error occurred"
    
    def override_current_stage(self):
        """Override current stage"""
        try:
            selected_stage = self.stage_var.get()
            stage_num = int(selected_stage.split()[-1])
            
            self.manual_stage_override = True
            self.set_current_stage(stage_num)
            self.stage_mode_label.config(text="Manual", foreground='orange')
            self.update_stage_mode_indicator('manual')  # Update new indicator
            self.update_override_button_state()
            
            self.log_message(f"🎯 Manual stage override: Set to Stage {stage_num}")
            
        except Exception as e:
            self.log_message(f"Error in stage override: {e}")
    
    def reset_to_auto_mode(self):
        """Reset to automatic mode"""
        try:
            self.manual_stage_override = False
            self.stage_mode_label.config(text="Auto", foreground='green')
            self.update_stage_mode_indicator('auto')  # Update new indicator
            self.update_override_button_state()
            
            self.log_message("🔄 Stage management reset to automatic mode")
            
        except Exception as e:
            self.log_message(f"Error resetting to auto mode: {e}")
    
    def set_current_stage(self, stage_num):
        """Set current stage display dengan enhanced information"""
        try:
            # Update stage label
            self.current_stage_label.config(text=f"Stage {stage_num}")
            colors = {1: '#2E7D32', 2: '#F57C00', 3: '#D32F2F'}  # Green, Orange, Red
            self.current_stage_label.config(foreground=colors.get(stage_num, '#2E7D32'))
            
            # Update stage details
            if hasattr(self, 'stage_details_label'):
                stage_config = self.stage_manager.stages_config.get(stage_num, {})
                min_viewers = stage_config.get('viewer_min', 0)
                delay = stage_config.get('delay', 1000)
                retention = stage_config.get('retention', 3000)
                
                details_text = f"Min: {min_viewers} viewers | Delay: {delay}ms | Retention: {retention}ms"
                self.stage_details_label.config(text=details_text)
            
            # Update next stage info
            if hasattr(self, 'next_stage_label'):
                next_stage_num = stage_num + 1 if stage_num < 3 else None
                if next_stage_num:
                    next_config = self.stage_manager.stages_config.get(next_stage_num, {})
                    next_min = next_config.get('viewer_min', 0)
                    self.next_stage_label.config(text=f"Stage {next_stage_num}: {next_min} viewers")
                else:
                    self.next_stage_label.config(text="Final Stage Reached")
            
            # Update stage progress
            self.update_stage_progress()
            
            self.log_message(f"🎯 Current stage: Stage {stage_num}")
            
        except Exception as e:
            self.log_message(f"❌ Error updating stage display: {e}")
    
    def update_stage_progress(self):
        """Update stage progress bar based on current viewers"""
        try:
            if not hasattr(self, 'stage_progress'):
                return
                
            current_stage = self.get_current_stage_number()
            current_viewers = self.current_viewer_count
            
            # Get current stage config
            stage_config = self.stage_manager.stages_config.get(current_stage, {})
            min_viewers = stage_config.get('viewer_min', 0)
            
            # Get next stage config for target
            next_stage = current_stage + 1 if current_stage < 3 else None
            if next_stage:
                next_config = self.stage_manager.stages_config.get(next_stage, {})
                target_viewers = next_config.get('viewer_min', min_viewers + 50)
            else:
                target_viewers = min_viewers + 100  # Arbitrary target for final stage
            
            # Calculate progress percentage
            if target_viewers > min_viewers:
                progress = max(0, min(100, ((current_viewers - min_viewers) / (target_viewers - min_viewers)) * 100))
            else:
                progress = 100 if current_viewers >= min_viewers else 0
            
            # Update progress bar
            self.stage_progress['value'] = progress
            self.stage_progress_label.config(text=f"{progress:.0f}%")
            
        except Exception as e:
            self.log_message(f"❌ Error updating stage progress: {e}")
    
    def update_stage_mode_indicator(self, mode):
        """Update stage mode indicator (Auto/Manual)"""
        if hasattr(self, 'stage_mode_indicator'):
            if mode.lower() == 'auto':
                self.stage_mode_indicator.config(text="[AUTO]", foreground='#4CAF50')
            else:
                self.stage_mode_indicator.config(text="[MANUAL]", foreground='#FF9800')
    
    def refresh_rules_display(self):
        """Refresh the rules display"""
        for item in self.rules_tree.get_children():
            self.rules_tree.delete(item)
            
        for rule in self.rules_data:
            pins_str = ', '.join(map(str, rule['pins']))
            self.rules_tree.insert('', 'end', values=(
                rule['name'],
                rule['event_type'],
                pins_str,
                rule['mode'],
                rule['status']
            ))
    
    def set_tracker(self, tracker):
        """Set TikTok tracker menggunakan Event Bridge"""
        try:
            self.tracker = tracker
            
            # Gunakan Event Bridge untuk koneksi
            self.event_bridge.connect_tracker(tracker)
            
            if tracker:
                self.log_message("✅ Arduino tab connected to tracker via Event Bridge")
            else:
                self.log_message("❌ Tracker disconnected from Arduino tab")
                
        except Exception as e:
            self.log_message(f"❌ Error connecting to tracker: {e}")
    
    def get_current_viewers(self):
        """Get current viewer count - UNIFIED METHOD untuk Live Status dan Stages Management"""
        try:
            # Prioritas 1: Data dari TikTok tracker callback (REAL DATA)
            if hasattr(self, 'current_viewer_count') and self.current_viewer_count > 0:
                return self.current_viewer_count
            
            # Jika belum ada data dari callback, return 0 (NO FALLBACK as requested)
            return 0
                
        except Exception as e:
            return 0
    
    # ===========================================
    # EVENT ACTION HANDLERS untuk Event Bridge
    # ===========================================
    
    def trigger_gift_action(self, gift_name: str, gift_count: int, username: str):
        """Trigger Arduino action untuk gift received"""
        try:
            # Cek apakah ada rule untuk gift
            for rule in self.rules_data:
                if rule.get('event_type') == 'gift' and rule.get('status') == 'active':
                    # Trigger rule action
                    self._execute_rule_action(rule, {
                        'event_type': 'gift',
                        'gift_name': gift_name,
                        'gift_count': gift_count,
                        'username': username
                    })
        except Exception as e:
            self.log_message(f"❌ Error triggering gift action: {e}")
    
    def trigger_comment_action(self, comment: str, username: str):
        """Trigger Arduino action untuk comment received"""
        try:
            # Cek apakah ada rule untuk comment
            for rule in self.rules_data:
                if rule.get('event_type') == 'comment' and rule.get('status') == 'active':
                    # Trigger rule action
                    self._execute_rule_action(rule, {
                        'event_type': 'comment',
                        'comment': comment,
                        'username': username
                    })
        except Exception as e:
            self.log_message(f"❌ Error triggering comment action: {e}")
    
    def trigger_like_action(self, like_count: int, username: str):
        """Trigger Arduino action untuk like received"""
        try:
            # Cek apakah ada rule untuk like
            for rule in self.rules_data:
                if rule.get('event_type') == 'like' and rule.get('status') == 'active':
                    # Trigger rule action
                    self._execute_rule_action(rule, {
                        'event_type': 'like',
                        'like_count': like_count,
                        'username': username
                    })
        except Exception as e:
            self.log_message(f"❌ Error triggering like action: {e}")
    
    def trigger_follow_action(self, username: str):
        """Trigger Arduino action untuk follow received"""
        try:
            # Cek apakah ada rule untuk follow
            for rule in self.rules_data:
                if rule.get('event_type') == 'follow' and rule.get('status') == 'active':
                    # Trigger rule action
                    self._execute_rule_action(rule, {
                        'event_type': 'follow',
                        'username': username
                    })
        except Exception as e:
            self.log_message(f"❌ Error triggering follow action: {e}")
    
    def trigger_share_action(self, username: str):
        """Trigger Arduino action untuk share received"""
        try:
            # Cek apakah ada rule untuk share
            for rule in self.rules_data:
                if rule.get('event_type') == 'share' and rule.get('status') == 'active':
                    # Trigger rule action
                    self._execute_rule_action(rule, {
                        'event_type': 'share',
                        'username': username
                    })
        except Exception as e:
            self.log_message(f"❌ Error triggering share action: {e}")
    
    def _execute_rule_action(self, rule: dict, event_data: dict):
        """Execute Arduino action untuk rule"""
        try:
            if not self.arduino_connected:
                return
                
            pins = rule.get('pins', [])
            mode = rule.get('mode', 'blink')
            
            # Use controller if available
            if hasattr(self, 'arduino_controller') and self.arduino_controller and self.arduino_controller.is_connected:
                # Use controller methods
                for pin in pins:
                    if mode == 'blink':
                        # Use test_pin for blink functionality
                        self.arduino_controller.test_pin(pin, 500)
                    else:
                        # For on/off modes, use trigger_pins
                        self.arduino_controller.trigger_pins([pin], 500 if mode == 'on' else 0)
                        
                self.log_message(f"⚡ Executed {rule['name']} for {event_data['event_type']} via controller")
            else:
                self.log_message(f"⚠️ Arduino controller not available for rule execution")
                
        except Exception as e:
            self.log_message(f"❌ Error executing rule action: {e}")
    
    # ===========================================
    # EXISTING METHODS (unchanged)
    # ===========================================
    
    def start_monitoring(self):
        """Start monitoring thread - REAL DATA ONLY dari TikTok callback"""
        self.monitoring_active = True
        
        def monitor_loop():
            while self.monitoring_active:
                try:
                    # Gunakan method get_current_viewers yang sudah optimized
                    current_viewers = self.get_current_viewers()
                    
                    # Update display viewer count menggunakan helper method
                    self.update_viewer_display(current_viewers)
                    
                    # STAGES MANAGEMENT: Pastikan menggunakan viewer data yang sama dengan Live Status
                    if self.is_stage_auto_mode():
                        self.check_stage_progression(current_viewers)
                    
                    # Update next stage info dengan data yang sama
                    self.update_next_stage_info(current_viewers)
                    
                    # Update statistics
                    self.events_label.config(text=str(self.stats['events_processed']))
                    self.success_label.config(text=f"{self.stats['success_rate']:.1f}%")
                    
                    time.sleep(1)  # Update setiap detik
                    
                except Exception as e:
                    pass  # Silent fail untuk monitoring
                    
        thread = threading.Thread(target=monitor_loop, daemon=True)
        thread.start()
    
    def check_stage_progression(self, current_viewers):
        """ENHANCED Stage Progression dengan Delay + Retention System"""
        try:
            current_stage = self.get_current_stage_number()
            
            # 1. RETENTION CHECK (PRIORITAS UTAMA - bypass delay)
            retention_change = self.check_retention_triggers(current_viewers, current_stage)
            if retention_change:
                new_stage, reason = retention_change
                self.set_current_stage(new_stage)
                self.stop_stage_timer()  # Stop any running timer
                self.log_message(f"⚡ RETENTION: Stage {current_stage}→{new_stage} ({reason})")
                return
            
            # 2. DELAY SYSTEM CHECK (jika tidak ada retention trigger)
            delay_change = self.check_delay_progression(current_viewers, current_stage)
            if delay_change:
                target_stage, reason = delay_change
                
                # Start timer jika belum jalan atau target berbeda
                if not self.stage_timer_active or self.stage_timer_target != target_stage:
                    self.start_stage_timer(target_stage, current_viewers, reason)
                
            else:
                # Tidak ada perubahan stage yang diperlukan
                if self.stage_timer_active:
                    self.stop_stage_timer()
            
            # 3. CHECK TIMER COMPLETION (timer TIDAK reset saat viewer berubah)
            if self.stage_timer_active:
                self.check_stage_timer_completion(current_viewers)
                
        except Exception as e:
            pass  # Silent fail untuk stage checks
    
    def check_retention_triggers(self, current_viewers, current_stage):
        """Check retention boundaries untuk instant stage change - NAIK & TURUN pakai retention sama"""
        try:
            # Check untuk NAIK stage (retention threshold tercapai)
            for stage_num in [3, 2]:
                if (stage_num > current_stage and 
                    self.stage_manager.stages_config[stage_num]['active']):
                    
                    min_viewers = self.stage_manager.stages_config[stage_num]['viewer_min']
                    retention = self.stage_manager.stages_config[stage_num].get('retention', 0)
                    retention_threshold = min_viewers + retention
                    
                    if current_viewers >= retention_threshold:
                        return (stage_num, f"UP: Viewers {current_viewers} ≥ retention {retention_threshold}")
            
            # Check untuk TURUN stage (retention boundary crossed - PAKAI NILAI RETENTION SAMA)
            if current_stage > 1:
                current_config = self.stage_manager.stages_config[current_stage]
                min_viewers = current_config['viewer_min']
                retention_down = current_config.get('retention', 0)  # PAKAI retention yang sama
                retention_floor = min_viewers - retention_down
                
                if current_viewers <= retention_floor:
                    # Turun ke stage tertinggi yang masih valid
                    for stage_num in [2, 1]:
                        if stage_num < current_stage:
                            if stage_num == 1 or self.stage_manager.stages_config[stage_num]['active']:
                                return (stage_num, f"DOWN: Viewers {current_viewers} ≤ retention floor {retention_floor} (retention: {retention_down})")
            
            return None  # No retention trigger
            
        except Exception:
            return None
    
    def check_delay_progression(self, current_viewers, current_stage):
        """Check apakah perlu mulai delay countdown - NAIK & TURUN pakai delay sama"""
        try:
            # Check untuk NAIK stage
            for stage_num in [3, 2]:
                if (stage_num > current_stage and 
                    self.stage_manager.stages_config[stage_num]['active']):
                    
                    min_viewers = self.stage_manager.stages_config[stage_num]['viewer_min']
                    
                    if current_viewers >= min_viewers:
                        return (stage_num, f"UP: Viewers {current_viewers} ≥ min {min_viewers}")
            
            # Check untuk TURUN stage - PAKAI DELAY DARI CURRENT STAGE
            if current_stage > 1:
                current_config = self.stage_manager.stages_config[current_stage]
                min_viewers = current_config['viewer_min']
                
                if current_viewers < min_viewers:
                    # Turun ke stage tertinggi yang valid
                    for stage_num in [2, 1]:
                        if stage_num < current_stage:
                            if stage_num == 1 or self.stage_manager.stages_config[stage_num]['active']:
                                # GUNAKAN DELAY dari current stage yang akan ditinggalkan
                                delay_down = current_config.get('delay', 0)
                                return (stage_num, f"DOWN: Viewers {current_viewers} < current min {min_viewers} (delay: {delay_down}s)")
            
            return None  # No delay progression needed
            
        except Exception:
            return None
    
    def start_stage_timer(self, target_stage, viewers, reason):
        """Start delay timer untuk stage change - NAIK & TURUN pakai delay yang sesuai"""
        try:
            current_stage = self.get_current_stage_number()
            
            # Tentukan delay berdasarkan arah perubahan stage
            if target_stage > current_stage:
                # NAIK stage - pakai delay dari target stage
                delay_seconds = self.stage_manager.stages_config[target_stage].get('delay', 0)
                direction = "UP"
            else:
                # TURUN stage - pakai delay dari current stage yang akan ditinggalkan
                delay_seconds = self.stage_manager.stages_config[current_stage].get('delay', 0)
                direction = "DOWN"
            
            if delay_seconds <= 0:
                # No delay - change immediately
                self.set_current_stage(target_stage)
                self.log_message(f"🎯 INSTANT {direction}: Stage changed to {target_stage} ({reason})")
                return
            
            # Start countdown timer
            self.stage_timer_active = True
            self.stage_timer_target = target_stage
            self.stage_timer_start_time = time.time()
            self.stage_timer_duration = delay_seconds
            
            self.log_message(f"⏳ DELAY {direction}: Stage {target_stage} in {delay_seconds}s ({reason})")
            
        except Exception as e:
            self.log_message(f"❌ Error starting stage timer: {e}")
    
    def check_stage_timer_completion(self, current_viewers):
        """Check apakah timer sudah selesai dan viewer masih memenuhi syarat - NAIK & TURUN"""
        try:
            if not self.stage_timer_active or not self.stage_timer_start_time or not self.stage_timer_target:
                return
                
            elapsed = time.time() - self.stage_timer_start_time
            remaining = max(0, self.stage_timer_duration - elapsed)
            current_stage = self.get_current_stage_number()
            
            if elapsed >= self.stage_timer_duration:
                # Timer selesai - cek apakah viewer masih memenuhi syarat
                target_stage = self.stage_timer_target
                
                if target_stage > current_stage:
                    # NAIK stage - cek apakah masih >= min_viewers target
                    min_viewers = self.stage_manager.stages_config[target_stage]['viewer_min']
                    if current_viewers >= min_viewers:
                        self.set_current_stage(target_stage)
                        self.log_message(f"✅ DELAY UP COMPLETE: Stage changed to {target_stage} (Viewers: {current_viewers})")
                    else:
                        self.log_message(f"❌ DELAY UP FAILED: Viewers {current_viewers} < required {min_viewers}")
                        
                else:
                    # TURUN stage - cek apakah masih < min_viewers current stage
                    current_min_viewers = self.stage_manager.stages_config[current_stage]['viewer_min']
                    if current_viewers < current_min_viewers:
                        self.set_current_stage(target_stage)
                        self.log_message(f"✅ DELAY DOWN COMPLETE: Stage changed to {target_stage} (Viewers: {current_viewers})")
                    else:
                        self.log_message(f"❌ DELAY DOWN CANCELLED: Viewers {current_viewers} back to >= {current_min_viewers}")
                
                self.stop_stage_timer()
            
        except Exception as e:
            self.log_message(f"❌ Error checking stage timer: {e}")
    
    def stop_stage_timer(self):
        """Stop stage timer"""
        self.stage_timer_active = False
        self.stage_timer_target = None
        self.stage_timer_start_time = None
        self.stage_timer_duration = 0
    
    def get_current_stage_number(self):
        """Get current stage number from display"""
        try:
            stage_text = self.current_stage_label.cget("text")
            if "Stage" in stage_text:
                return int(stage_text.split()[-1])
            return 1
        except:
            return 1
    
    def update_next_stage_info(self, current_viewers):
        """Update next stage information - MENGGUNAKAN DATA YANG SAMA dengan Live Status viewer"""
        try:
            current_stage = self.get_current_stage_number()
            
            # Find next available stage (pastikan konsistensi dengan Live Status)
            next_stage = None
            for stage_num in [2, 3]:
                if (self.stage_manager.stages_config[stage_num]['active'] and 
                    stage_num > current_stage and
                    current_viewers < self.stage_manager.stages_config[stage_num]['viewer_min']):
                    next_stage = stage_num
                    break
                    
            if next_stage:
                min_viewers = self.stage_manager.stages_config[next_stage]['viewer_min']
                remaining = max(0, min_viewers - current_viewers)
                self.next_stage_label.config(text=f"Stage {next_stage}: {remaining} more viewers (REAL DATA)")
            else:
                if current_stage >= 3:
                    self.next_stage_label.config(text="Max stage reached")
                else:
                    self.next_stage_label.config(text="No higher stages enabled")
                    
        except Exception:
            self.next_stage_label.config(text="Stage info unavailable")
    
    def log_message(self, message):
        """Add message to Arduino log - UNIFIED logging untuk semua components"""
        try:
            # Check if log_text widget exists
            if not hasattr(self, 'log_text') or self.log_text is None:
                # If UI not ready, just print to console
                print(f"Arduino Log: {message}")
                return
                
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] {message}\n"
            
            self.log_text.insert('end', log_entry)
            self.log_text.see('end')
            
            # Keep log manageable (500 lines max)
            lines = self.log_text.get('1.0', 'end').split('\n')
            if len(lines) > 500:
                self.log_text.delete('1.0', '100.0')
        except Exception as e:
            # Fallback to console if anything goes wrong
            print(f"Arduino Log Error: {e}")
            print(f"Arduino Log: {message}")
    
    def clear_log(self):
        """Clear Arduino log"""
        self.log_text.delete('1.0', 'end')
        self.log_message("📝 Log cleared")
    
    # Helper methods untuk mengurangi duplikasi kode
    def update_viewer_display(self, viewer_count):
        """Helper: Update viewer count display - UNIFIED untuk Live Status dan Stages"""
        self.viewer_count_label.config(text=str(viewer_count))
        
        # Update stage progress when viewer count changes
        self.update_stage_progress()
        
    def update_tracker_status(self, connected):
        """Update tracker connection status display"""
        if hasattr(self, 'tracker_status_label'):
            if connected:
                self.tracker_status_label.config(
                    text="🟢 Tracker: Connected", 
                    foreground='#4CAF50'
                )
            else:
                self.tracker_status_label.config(
                    text="🔴 Tracker: Disconnected", 
                    foreground='#F44336'
                )
        
    def is_stage_auto_mode(self):
        """Helper: Check if stage is in auto mode"""
        return not self.manual_stage_override
        
    def get_stage_min_viewers(self, stage_number):
        """Helper: Get minimum viewers for stage"""
        return self.stage_manager.stages_config.get(stage_number, {}).get('viewer_min', 0)
        
    def is_stage_active(self, stage_number):
        """Helper: Check if stage is active"""
        return self.stage_manager.stages_config.get(stage_number, {}).get('active', False)
    
    # ========== ARDUINO OVERRIDE SYSTEM METHODS ==========
    
    def toggle_override_mode(self):
        """Toggle between AUTO and MANUAL stage mode"""
        try:
            current_mode = getattr(self, 'manual_stage_override', False)
            new_mode = not current_mode
            
            # Update override state
            self.manual_stage_override = new_mode
            
            # Update UI components
            self.update_override_button_state()
            self.toggle_manual_controls(new_mode)
            
            # Log mode change
            mode_text = "MANUAL" if new_mode else "AUTO"
            self.log_message(f"Stage mode changed to: {mode_text}")
            
            # If switching to auto, resume automatic stage progression
            if not new_mode:
                self.stage_manager.resume_auto_progression()
            else:
                self.stage_manager.pause_auto_progression()
                
        except Exception as e:
            self.log_message(f"Error toggling override mode: {e}")
    
    def update_override_button_state(self):
        """Update override button text and appearance based on current mode"""
        try:
            if hasattr(self, 'override_mode_button'):
                if getattr(self, 'manual_stage_override', False):
                    self.override_mode_button.config(
                        text="🔴 Manual Mode",
                        style="Warning.TButton"
                    )
                    self.stage_mode_indicator.config(
                        text="[MANUAL]",
                        foreground='#F44336'
                    )
                else:
                    self.override_mode_button.config(
                        text="🟢 Auto Mode", 
                        style="TButton"
                    )
                    self.stage_mode_indicator.config(
                        text="[AUTO]",
                        foreground='#4CAF50'
                    )
        except Exception as e:
            self.log_message(f"Error updating override button: {e}")
    
    def toggle_manual_controls(self, show):
        """Show/hide manual stage controls based on override mode"""
        try:
            if hasattr(self, 'manual_controls_frame'):
                if show:
                    self.manual_controls_frame.pack(side='right', padx=(10, 0))
                    self.apply_stage_button.config(state='normal')
                    self.next_stage_label.pack_forget()  # Hide auto progress info
                else:
                    self.manual_controls_frame.pack_forget()
                    self.apply_stage_button.config(state='disabled')
                    self.next_stage_label.pack(side='right')  # Show auto progress info
        except Exception as e:
            self.log_message(f"Error toggling manual controls: {e}")
    
    def on_manual_stage_change(self):
        """Handle manual stage spinbox change"""
        try:
            selected_stage = int(self.manual_stage_var.get())
            current_stage = getattr(self, 'current_stage', 1)
            
            # Enable apply button only if stage is different and valid
            if selected_stage != current_stage and self.is_stage_available(selected_stage):
                self.apply_stage_button.config(state='normal', style="Accent.TButton")
            else:
                self.apply_stage_button.config(state='disabled', style="TButton")
                
        except Exception as e:
            self.log_message(f"Error in manual stage change: {e}")
    
    def apply_manual_stage(self):
        """Apply manually selected stage"""
        try:
            target_stage = int(self.manual_stage_var.get())
            
            if not self.is_stage_available(target_stage):
                self.log_message(f"Stage {target_stage} is not available or disabled")
                return
            
            # Apply stage through stage manager
            success = self.stage_manager.set_manual_stage_override(target_stage)
            
            if success:
                self.current_stage = target_stage
                self.update_current_stage_display()
                self.log_message(f"Manual stage applied: Stage {target_stage}")
                
                # Reset apply button
                self.apply_stage_button.config(state='disabled', style="TButton")
            else:
                self.log_message(f"Failed to apply Stage {target_stage}")
                
        except Exception as e:
            self.log_message(f"Error applying manual stage: {e}")
    
    def is_stage_available(self, stage_number):
        """Check if stage is available for manual override"""
        try:
            # Check if stage exists in configuration
            if stage_number not in self.stage_manager.stages_config:
                return False
            
            # Check if stage is enabled
            stage_config = self.stage_manager.stages_config[stage_number]
            if not stage_config.get('active', False):
                return False
            
            # Check stage dependencies (if any)
            dependencies = stage_config.get('dependencies', [])
            for dep_stage in dependencies:
                if not self.is_stage_completed(dep_stage):
                    return False
            
            return True
            
        except Exception as e:
            self.log_message(f"Error checking stage availability: {e}")
            return False
    
    def is_stage_completed(self, stage_number):
        """Check if a stage has been completed (for dependency checking)"""
        # Implementation depends on how stage completion is tracked
        # For now, assume stages are completed if they have been reached
        return stage_number <= getattr(self, 'highest_stage_reached', 1)
    
    def update_current_stage_display(self):
        """Update all stage-related displays"""
        try:
            stage_num = getattr(self, 'current_stage', 1)
            self.current_stage_label.config(text=f"Stage {stage_num}")
            
            # Update manual stage spinbox to match current stage
            if hasattr(self, 'manual_stage_var'):
                self.manual_stage_var.set(str(stage_num))
            
            # Update stage details
            if hasattr(self, 'stage_details_label'):
                stage_config = self.stage_manager.stages_config.get(stage_num, {})
                min_viewers = stage_config.get('viewer_min', 0)
                delay = stage_config.get('delay', 0)
                retention = stage_config.get('retention', 0)
                
                details_text = f"Min: {min_viewers} | Delay: {delay}ms | Retention: {retention}ms"
                self.stage_details_label.config(text=details_text)
            
        except Exception as e:
            self.log_message(f"Error updating current stage display: {e}")
    
    # ========== ENHANCED STAGE PROGRESSION METHODS ==========
    
    def update_stage_progression_with_fallback(self, viewer_count):
        """Update stage progression dengan auto fallback support"""
        try:
            # Check if stage should progress using stage manager
            new_stage = self.stage_manager.check_stage_progression(viewer_count)
            
            if new_stage is not None and new_stage != self.stage_manager.current_stage:
                old_stage = self.stage_manager.current_stage
                self.stage_manager.set_current_stage(new_stage)
                
                # Log the progression or fallback
                if new_stage > old_stage:
                    self.log_message(f"🔼 Stage progression: Stage {old_stage} → Stage {new_stage} ({viewer_count} viewers)")
                elif new_stage < old_stage:
                    self.log_message(f"🔽 Stage fallback: Stage {old_stage} → Stage {new_stage} ({viewer_count} viewers)")
                
                # Update display
                self.update_stage_display()
                
        except Exception as e:
            self.log_message(f"❌ Error in stage progression: {e}")
            
    def update_automatic_stage_check_enhanced(self, viewer_count):
        """Enhanced automatic stage checking dengan fallback"""
        try:
            if not self.stage_manager.manual_stage_override:
                # Check for normal progression and fallback
                self.update_stage_progression_with_fallback(viewer_count)
            
            # Check retention triggers regardless of mode (for logging)
            current_stage = self.stage_manager.current_stage
            retention_result = self.stage_manager.check_retention_triggers(viewer_count, current_stage)
            
            if retention_result['trigger']:
                self.log_message(f"🎯 Retention trigger: {retention_result['action']} at {viewer_count} viewers")
                
        except Exception as e:
            self.log_message(f"❌ Error in automatic stage check: {e}")
    
    def force_stage_update_from_manager(self):
        """Force update display dari stage manager state - untuk debugging"""
        try:
            current_stage = self.stage_manager.current_stage
            mode = "MANUAL" if self.stage_manager.manual_stage_override else "AUTO"
            locked_stage = self.stage_manager.manual_locked_stage
            
            self.log_message(f"🔍 Stage Status: Current={current_stage}, Mode={mode}, Locked={locked_stage}")
            self.update_stage_display()
            
        except Exception as e:
            self.log_message(f"❌ Error forcing stage update: {e}")
            
        except Exception as e:
            self.log_message(f"Error updating stage display: {e}", "error")
