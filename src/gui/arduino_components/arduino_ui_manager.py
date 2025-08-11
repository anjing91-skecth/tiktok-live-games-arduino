"""
Arduino UI Components
====================

Handles all UI setup and layout for Arduino tab.
        # Stage selection row dengan override button
        select_row = ttk.Frame(stages_frame)
        select_row.pack(fill='x', pady=(0, 15))
        
        # Current stage selection
        current_stage_frame = ttk.Frame(select_row)
        current_stage_frame.pack(side='left', fill='x', expand=True)
        
        ttk.Label(current_stage_frame, text="Current Stage:", font=('Arial', 9, 'bold')).pack(side='left')
        self.arduino_tab.current_stage_var = tk.StringVar(value='Stage 1')
        self.arduino_tab.current_stage_dropdown = ttk.Combobox(current_stage_frame, textvariable=self.arduino_tab.current_stage_var,
                                       values=['Stage 1', 'Stage 2', 'Stage 3'], 
                                       state='readonly', width=12)
        self.arduino_tab.current_stage_dropdown.bind('<<ComboboxSelected>>', self.arduino_tab.on_current_stage_selected)
        self.arduino_tab.current_stage_dropdown.pack(side='right', padx=(5, 0))
        
        # Override button
        override_frame = ttk.Frame(select_row)
        override_frame.pack(side='right', padx=(10, 0))
        
        self.arduino_tab.override_var = tk.StringVar(value='Manual Mode')
        self.arduino_tab.override_button = ttk.Button(override_frame, textvariable=self.arduino_tab.override_var,
                                                    command=self.arduino_tab.on_override_clicked, width=12)
        self.arduino_tab.override_button.pack(side='right')
        
        # Configuration selection
        config_select_row = ttk.Frame(stages_frame)
        config_select_row.pack(fill='x', pady=(0, 15))
        
        ttk.Label(config_select_row, text="Configure Stage:", font=('Arial', 10, 'bold')).pack(side='left')
        self.arduino_tab.stage_var = tk.StringVar(value='Stage 2')
        self.arduino_tab.stage_combo = ttk.Combobox(config_select_row, textvariable=self.arduino_tab.stage_var,
                                       values=['Stage 1', 'Stage 2', 'Stage 3'], 
                                       state='readonly', width=15)
        self.arduino_tab.stage_combo.bind('<<ComboboxSelected>>', self.arduino_tab.on_stage_selected)
        self.arduino_tab.stage_combo.pack(side='left', padx=(10, 0))I logic from business logic for better modularity.
"""

import tkinter as tk
from tkinter import ttk
import sys
import os

# Add paths for imports  
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

class ArduinoUIManager:
    """Manages UI setup and layout for Arduino tab"""
    
    def __init__(self, arduino_tab):
        self.arduino_tab = arduino_tab
        self.widgets = {}
    
    def setup_main_layout(self, parent):
        """Setup improved main layout structure with better proportions"""
        # Main container dengan proper padding
        main_container = ttk.Frame(parent, padding=10)
        main_container.pack(fill='both', expand=True)
        
        # Header section untuk title dan connection
        header_frame = ttk.Frame(main_container)
        header_frame.pack(fill='x', pady=(0, 15))
        
        # Content area dengan improved two-column layout
        content_frame = ttk.Frame(main_container)
        content_frame.pack(fill='both', expand=True)
        
        # Left column - Controls dan Management (60% width)
        left_column = ttk.Frame(content_frame)
        left_column.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        # Right column - Status dan Log (40% width)  
        right_column = ttk.Frame(content_frame)
        right_column.pack(side='right', fill='both', expand=True)
        
        return {
            'main': main_container,
            'header': header_frame,
            'content': content_frame,
            'left': left_column,
            'right': right_column
        }
    
    def setup_connection_section(self, parent):
        """Setup improved connection section with better layout"""
        conn_frame = ttk.LabelFrame(parent, text="🔌 Arduino Connection", padding=15)
        conn_frame.pack(fill='x', pady=(0, 15))
        
        # Status row - prominent display
        status_row = ttk.Frame(conn_frame)
        status_row.pack(fill='x', pady=(0, 10))
        
        # Status dengan better styling
        self.arduino_tab.connection_status = ttk.Label(status_row, text="🔴 Disconnected", 
                                     font=('Arial', 12, 'bold'))
        self.arduino_tab.connection_status.pack(side='left')
        
        # Port selection row dengan better spacing
        port_row = ttk.Frame(conn_frame)
        port_row.pack(fill='x', pady=(0, 10))
        
        ttk.Label(port_row, text="Port:", font=('Arial', 10)).pack(side='left')
        self.arduino_tab.port_var = tk.StringVar()
        self.arduino_tab.port_combo = ttk.Combobox(port_row, textvariable=self.arduino_tab.port_var, 
                                  values=[], state='readonly', width=20)
        self.arduino_tab.port_combo.pack(side='left', padx=(8, 15))
        
        # Check Ports button dengan improved styling
        ttk.Button(port_row, text="🔍 Scan Ports", 
                  command=self.arduino_tab.check_arduino_ports).pack(side='left')
        
        # Action buttons row dengan better spacing
        action_row = ttk.Frame(conn_frame)
        action_row.pack(fill='x')
        
        # Connect/Disconnect button
        self.arduino_tab.connect_btn = ttk.Button(action_row, text="🔌 Connect", 
                                     command=self.arduino_tab.toggle_connection, width=12)
        self.arduino_tab.connect_btn.pack(side='left', padx=(0, 10))
        
        # Test buttons dengan consistent styling
        ttk.Button(action_row, text="💡 Test LED", width=12,
                  command=self.arduino_tab.test_led).pack(side='left', padx=(0, 5))
        
        ttk.Button(action_row, text="📍 Test Pin", width=12,
                  command=self.arduino_tab.test_pin).pack(side='left')
    
    def setup_stages_section(self, parent):
        """Setup improved stages management section"""
        stages_frame = ttk.LabelFrame(parent, text="⚙️ Stages Management", padding=15)
        stages_frame.pack(fill='x', pady=(0, 15))
        
        # Stage selection row dengan better layout
        select_row = ttk.Frame(stages_frame)
        select_row.pack(fill='x', pady=(0, 15))
        
        ttk.Label(select_row, text="Configure Stage:", font=('Arial', 10, 'bold')).pack(side='left')
        self.arduino_tab.stage_var = tk.StringVar(value='Stage 2')
        self.arduino_tab.stage_combo = ttk.Combobox(select_row, textvariable=self.arduino_tab.stage_var,
                                       values=['Stage 1', 'Stage 2', 'Stage 3'], 
                                       state='readonly', width=15)
        self.arduino_tab.stage_combo.bind('<<ComboboxSelected>>', self.arduino_tab.on_stage_selected)
        self.arduino_tab.stage_combo.pack(side='left', padx=(10, 0))
        
        # Configuration area dengan improved grid layout
        config_frame = ttk.Frame(stages_frame)
        config_frame.pack(fill='x', pady=(0, 15))
        
        # Store the config frame reference so Arduino tab can access it
        self.arduino_tab.stage_settings_frame = config_frame
        
        # Left column - Basic settings
        left_config = ttk.Frame(config_frame)
        left_config.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        # Right column - Advanced settings
        right_config = ttk.Frame(config_frame)
        right_config.pack(side='left', fill='x', expand=True)
        
        self._setup_stage_config_left(left_config)
        self._setup_stage_config_right(right_config)
        
        # Save button dengan better styling
        save_row = ttk.Frame(stages_frame)
        save_row.pack(fill='x')
        
        ttk.Button(save_row, text="💾 Save Stage Settings", width=20,
                  command=self.arduino_tab.save_stage_settings).pack(side='left')
    
    def _setup_stage_config_left(self, parent):
        """Setup left side of stage configuration with improved layout"""
        # Enable/Disable stage dengan better spacing dan dependency logic
        enable_row = ttk.Frame(parent)
        enable_row.pack(fill='x', pady=(0, 8))
        
        self.arduino_tab.stage_enable_var = tk.BooleanVar()
        self.arduino_tab.stage_enable_check = ttk.Checkbutton(enable_row, text="Enable Stage", 
                                                 variable=self.arduino_tab.stage_enable_var,
                                                 command=self.arduino_tab.on_stage_enable_changed)
        self.arduino_tab.stage_enable_check.pack(anchor='w')
        
        # Viewer minimum dengan better layout
        viewer_row = ttk.Frame(parent)
        viewer_row.pack(fill='x', pady=(0, 8))
        
        ttk.Label(viewer_row, text="Min Viewers:", font=('Arial', 9)).pack(side='left')
        self.arduino_tab.viewer_min_var = tk.StringVar(value='0')
        self.arduino_tab.viewer_min_entry = ttk.Entry(viewer_row, textvariable=self.arduino_tab.viewer_min_var, width=10)
        self.arduino_tab.viewer_min_entry.pack(side='right')
    
    def _setup_stage_config_right(self, parent):
        """Setup right side of stage configuration with improved layout"""
        # Delay setting dengan better layout
        delay_row = ttk.Frame(parent)
        delay_row.pack(fill='x', pady=(0, 8))
        
        ttk.Label(delay_row, text="Delay (s):", font=('Arial', 9)).pack(side='left')
        self.arduino_tab.delay_var = tk.StringVar(value='0')
        self.arduino_tab.delay_entry = ttk.Entry(delay_row, textvariable=self.arduino_tab.delay_var, width=10)
        self.arduino_tab.delay_entry.pack(side='right')
        
        # Retention setting dengan better layout  
        retention_row = ttk.Frame(parent)
        retention_row.pack(fill='x', pady=(0, 8))
        
        ttk.Label(retention_row, text="Retention (s):", font=('Arial', 9)).pack(side='left')
        self.arduino_tab.retention_var = tk.StringVar(value='0')
        self.arduino_tab.retention_entry = ttk.Entry(retention_row, textvariable=self.arduino_tab.retention_var, width=10)
        self.arduino_tab.retention_entry.pack(side='right')
    
    def setup_live_status_section(self, parent):
        """Setup compact live status section with stage monitoring"""
        status_frame = ttk.LabelFrame(parent, text="🎯 Live Status & Stage Monitor", padding=10)
        status_frame.pack(fill='x', pady=(0, 10))
        
        # Row 1: Current stage, mode and override controls in single line
        stage_row = ttk.Frame(status_frame)
        stage_row.pack(fill='x', pady=(0, 8))
        
        ttk.Label(stage_row, text="Active Stage:", font=('Arial', 9, 'bold')).pack(side='left')
        self.arduino_tab.current_stage_label = ttk.Label(stage_row, text="Stage 1", 
                                           font=('Arial', 11, 'bold'), foreground='#2E7D32')
        self.arduino_tab.current_stage_label.pack(side='left', padx=(8, 0))
        
        self.arduino_tab.stage_mode_indicator = ttk.Label(stage_row, text="[AUTO]", 
                                             font=('Arial', 8), foreground='green')
        self.arduino_tab.stage_mode_indicator.pack(side='left', padx=(8, 0))
        
        # Override button - key missing component
        self.arduino_tab.override_mode_button = ttk.Button(stage_row, text="Manual Override", 
                                                  command=self.arduino_tab.toggle_override_mode,
                                                  width=15)
        self.arduino_tab.override_mode_button.pack(side='right', padx=(5, 0))
        
        # Progress bar - compact version
        self.arduino_tab.stage_progress = ttk.Progressbar(stage_row, length=120, mode='determinate')
        self.arduino_tab.stage_progress.pack(side='right', padx=(0, 5))
        
        self.arduino_tab.stage_progress_label = ttk.Label(stage_row, text="0%", font=('Arial', 8))
        self.arduino_tab.stage_progress_label.pack(side='right')
        
        # Row 2: Viewers and manual stage controls
        viewer_row = ttk.Frame(status_frame)
        viewer_row.pack(fill='x', pady=(0, 8))
        
        ttk.Label(viewer_row, text="👥", font=('Arial', 10)).pack(side='left')
        self.arduino_tab.viewer_count_label = ttk.Label(viewer_row, text="0", font=('Arial', 11, 'bold'), 
                                          foreground='#1976D2')
        self.arduino_tab.viewer_count_label.pack(side='left', padx=(5, 0))
        
        ttk.Label(viewer_row, text="viewers", font=('Arial', 9)).pack(side='left', padx=(3, 0))
        
        # Manual stage controls (initially hidden, shown during override mode)
        manual_controls = ttk.Frame(viewer_row)
        manual_controls.pack(side='right', padx=(10, 0))
        
        ttk.Label(manual_controls, text="Stage:", font=('Arial', 8)).pack(side='left')
        self.arduino_tab.manual_stage_var = tk.StringVar(value="1")
        self.arduino_tab.manual_stage_spinbox = ttk.Spinbox(manual_controls, 
                                                  from_=1, to=10, width=3,
                                                  textvariable=self.arduino_tab.manual_stage_var,
                                                  command=self.arduino_tab.on_manual_stage_change)
        self.arduino_tab.manual_stage_spinbox.pack(side='left', padx=(3, 5))
        
        self.arduino_tab.apply_stage_button = ttk.Button(manual_controls, text="Apply", 
                                               command=self.arduino_tab.apply_manual_stage,
                                               width=8, state='disabled')
        self.arduino_tab.apply_stage_button.pack(side='left')
        
        # Store manual controls frame for show/hide
        self.arduino_tab.manual_controls_frame = manual_controls
        
        self.arduino_tab.next_stage_label = ttk.Label(viewer_row, text="→ Stage 2: 50 viewers", 
                                        font=('Arial', 8), foreground='#666')
        self.arduino_tab.next_stage_label.pack(side='right')
        
        # Row 3: Stage details - compact
        detail_row = ttk.Frame(status_frame)
        detail_row.pack(fill='x', pady=(0, 8))
        
        ttk.Label(detail_row, text="⚙️", font=('Arial', 9)).pack(side='left')
        self.arduino_tab.stage_details_label = ttk.Label(detail_row, text="Min: 0 | Delay: 1000ms | Retention: 3000ms", 
                                           font=('Arial', 8), foreground='#333')
        self.arduino_tab.stage_details_label.pack(side='left', padx=(5, 0))
        
        # Row 4: Connection and statistics - single compact line
        status_row = ttk.Frame(status_frame)
        status_row.pack(fill='x')
        
        # Left side - Tracker status
        ttk.Label(status_row, text="🔗", font=('Arial', 9)).pack(side='left')
        self.arduino_tab.tracker_status_label = ttk.Label(status_row, text="Disconnected", 
                                            font=('Arial', 8), foreground='#F44336')
        self.arduino_tab.tracker_status_label.pack(side='left', padx=(3, 15))
        
        # Middle - Last update
        ttk.Label(status_row, text="⏰", font=('Arial', 9)).pack(side='left')
        self.arduino_tab.last_update_label = ttk.Label(status_row, text="--:--:--", 
                                         font=('Arial', 8), foreground='#666')
        self.arduino_tab.last_update_label.pack(side='left', padx=(3, 15))
        
        # Right side - Quick stats
        ttk.Label(status_row, text="📊", font=('Arial', 9)).pack(side='left')
        self.arduino_tab.events_label = ttk.Label(status_row, text="0", font=('Arial', 8, 'bold'))
        self.arduino_tab.events_label.pack(side='left', padx=(3, 5))
        
        ttk.Label(status_row, text="✅", font=('Arial', 9)).pack(side='left')
        self.arduino_tab.success_label = ttk.Label(status_row, text="100%", font=('Arial', 8, 'bold'), 
                                     foreground='#4CAF50')
        self.arduino_tab.success_label.pack(side='left', padx=(3, 5))
        
        ttk.Label(status_row, text="🎯", font=('Arial', 9)).pack(side='left')
        self.arduino_tab.triggers_label = ttk.Label(status_row, text="0", font=('Arial', 8, 'bold'))
        self.arduino_tab.triggers_label.pack(side='left', padx=(3, 0))
    
    def setup_rules_section(self, parent):
        """Setup compact rules management section"""
        rules_frame = ttk.LabelFrame(parent, text="⚙️ Arduino Rules", padding=10)
        rules_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        # Compact rules toolbar
        toolbar = ttk.Frame(rules_frame)
        toolbar.pack(fill='x', pady=(0, 8))
        
        ttk.Button(toolbar, text="➕ Add", width=8,
                  command=self.arduino_tab.add_new_rule).pack(side='left', padx=(0, 5))
        ttk.Button(toolbar, text="✏️ Edit", width=8,
                  command=self.arduino_tab.edit_selected_rule).pack(side='left', padx=(0, 5))
        ttk.Button(toolbar, text="🗑️ Delete", width=8,
                  command=self.arduino_tab.delete_selected_rule).pack(side='left')
        
        # Compact rules treeview
        self.arduino_tab.rules_tree = ttk.Treeview(rules_frame, columns=('event', 'pins', 'mode'), 
                                     show='tree headings', height=6)
        
        # Configure columns with better proportions
        self.arduino_tab.rules_tree.heading('#0', text='Rule Name')
        self.arduino_tab.rules_tree.heading('event', text='Event')
        self.arduino_tab.rules_tree.heading('pins', text='Pins')
        self.arduino_tab.rules_tree.heading('mode', text='Mode')
        
        self.arduino_tab.rules_tree.column('#0', width=120)
        self.arduino_tab.rules_tree.column('event', width=100)
        self.arduino_tab.rules_tree.column('pins', width=70)
        self.arduino_tab.rules_tree.column('mode', width=70)
        
        # Scrollbar for rules
        rules_scroll = ttk.Scrollbar(rules_frame, orient='vertical', 
                                    command=self.arduino_tab.rules_tree.yview)
        self.arduino_tab.rules_tree.configure(yscrollcommand=rules_scroll.set)
        
        self.arduino_tab.rules_tree.pack(side='left', fill='both', expand=True)
        rules_scroll.pack(side='right', fill='y')
    
    def setup_log_section(self, parent):
        """Setup compact log display section"""
        log_frame = ttk.LabelFrame(parent, text="📋 Arduino Log", padding=10)
        log_frame.pack(fill='both', expand=True)
        
        # Compact log text area
        self.arduino_tab.log_text = tk.Text(log_frame, height=8, font=('Consolas', 8))
        self.arduino_tab.log_text.pack(fill='both', expand=True, pady=(0, 8))
        
        # Compact log controls
        log_controls = ttk.Frame(log_frame)
        log_controls.pack(fill='x')
        
        ttk.Button(log_controls, text="🗑️ Clear", width=8,
                  command=self.arduino_tab.clear_log).pack(side='left')
        
        # Compact filter
        ttk.Label(log_controls, text="Filter:", font=('Arial', 8)).pack(side='right', padx=(10, 3))
        self.arduino_tab.log_filter_var = tk.StringVar(value='All')
        log_filter = ttk.Combobox(log_controls, textvariable=self.arduino_tab.log_filter_var,
                                 values=['All', 'Info', 'Warning', 'Error'], 
                                 state='readonly', width=6, font=('Arial', 8))
        log_filter.pack(side='right')
    
    def get_widget(self, name):
        """Get widget by name"""
        return self.widgets.get(name)
    
    def set_widget(self, name, widget):
        """Set widget by name"""
        self.widgets[name] = widget
