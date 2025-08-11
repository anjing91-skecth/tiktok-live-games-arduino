"""
Arduino Rule Dialog Component
============================

Separated component for rule creation/editing dialog.
This maintains the exact same functionality while being modular.
"""

import tkinter as tk
from tkinter import ttk, messagebox

class StageRuleDialog:
    """Dialog untuk membuat/edit rule dengan advanced options"""
    
    def __init__(self, parent, rule_data=None):
        self.parent = parent
        self.rule_data = rule_data
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Create New Rule" if not rule_data else "Edit Rule")
        self.dialog.geometry("600x550")
        self.dialog.resizable(False, False)
        self.dialog.grab_set()
        
        self.setup_dialog()
        
    def setup_dialog(self):
        """Setup rule creation dialog with advanced options"""
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill='both', expand=True)
        
        # Rule name
        ttk.Label(main_frame, text="Rule Name:").grid(row=0, column=0, sticky='w', pady=(0, 10))
        self.name_var = tk.StringVar(value=self.rule_data.get('name', '') if self.rule_data else '')
        ttk.Entry(main_frame, textvariable=self.name_var, width=40).grid(row=0, column=1, columnspan=2, pady=(0, 10), sticky='w')
        
        # Event type
        ttk.Label(main_frame, text="Event Type:").grid(row=1, column=0, sticky='w', pady=(0, 10))
        self.event_var = tk.StringVar(value=self.rule_data.get('event_type', 'gift') if self.rule_data else 'gift')
        event_combo = ttk.Combobox(main_frame, textvariable=self.event_var, 
                                  values=['gift', 'comment', 'like', 'follow', 'share'])
        event_combo.grid(row=1, column=1, pady=(0, 10), sticky='w')
        event_combo.bind('<<ComboboxSelected>>', self.on_event_type_change)
        
        # Target pins
        ttk.Label(main_frame, text="Target Pins:").grid(row=2, column=0, sticky='w', pady=(0, 10))
        pins_frame = ttk.Frame(main_frame)
        pins_frame.grid(row=2, column=1, columnspan=2, pady=(0, 10), sticky='ew')
        
        pins_default = "6,7,8,9"
        if self.rule_data and 'pins' in self.rule_data:
            pins_default = ','.join(map(str, self.rule_data['pins']))
        self.pins_var = tk.StringVar(value=pins_default)
        ttk.Entry(pins_frame, textvariable=self.pins_var, width=20).grid(row=0, column=0, sticky='ew')
        
        # Mode
        ttk.Label(main_frame, text="Mode:").grid(row=3, column=0, sticky='w', pady=(0, 10))
        self.mode_var = tk.StringVar(value=self.rule_data.get('mode', 'simultaneous') if self.rule_data else 'simultaneous')
        ttk.Combobox(main_frame, textvariable=self.mode_var, values=['simultaneous', 'sequential', 'random'], state='readonly').grid(row=3, column=1, pady=(0, 10), sticky='w')
        
        # Duration
        ttk.Label(main_frame, text="Duration (ms):").grid(row=4, column=0, sticky='w', pady=(0, 10))
        self.duration_var = tk.StringVar(value=str(self.rule_data.get('duration', 20)) if self.rule_data else '20')
        ttk.Entry(main_frame, textvariable=self.duration_var, width=10).grid(row=4, column=1, pady=(0, 10), sticky='w')
        
        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=5, column=0, columnspan=3, pady=(20, 0))
        
        ttk.Button(btn_frame, text="Save Rule", command=self.save_rule).pack(side='left', padx=(0, 10))
        ttk.Button(btn_frame, text="Cancel", command=self.dialog.destroy).pack(side='left')
    
    def on_event_type_change(self, event=None):
        """Handle event type change"""
        pass
        
    def save_rule(self):
        """Save rule data with validation"""
        if not self.name_var.get().strip():
            messagebox.showerror("Error", "Please enter a rule name")
            return
            
        pins_text = self.pins_var.get().strip()
        try:
            selected_pins = [int(p.strip()) for p in pins_text.split(',') if p.strip()]
        except ValueError:
            messagebox.showerror("Error", "Invalid pin format")
            return
            
        rule_data = {
            'name': self.name_var.get().strip(),
            'event_type': self.event_var.get(),
            'pins': selected_pins,
            'mode': self.mode_var.get(),
            'duration': int(self.duration_var.get() or 20),
            'status': 'Active'
        }
        
        self.result = rule_data
        self.dialog.destroy()
