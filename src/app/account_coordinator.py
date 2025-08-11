"""
Account Coordinator for TikTok Live Lite Application
==================================================

Manages account selection, loading, and coordination with other components.
Extracted from main.py for better maintainability.
"""

import tkinter as tk
from tkinter import messagebox, simpledialog


class AccountCoordinator:
    """Coordinates account management and selection"""
    
    def __init__(self, account_combo, status_var, app_instance):
        """
        Initialize Account Coordinator
        
        Args:
            account_combo: Combobox widget for account selection
            status_var: StringVar for status updates
            app_instance: Reference to main application instance
        """
        self.account_combo = account_combo
        self.status_var = status_var
        self.app = app_instance
        self.logger = app_instance.logger
        self.accounts = []
        
        # Bind selection event
        self.account_combo.bind('<<ComboboxSelected>>', self.on_account_selected)
    
    def load_accounts(self):
        """Load accounts into dropdown from unified database"""
        try:
            # Load from unified database instead of JSON
            accounts = self.app.db_manager.get_all_accounts()
            
            # Update dropdown
            account_list = [f"@{acc['username']}" for acc in accounts]
            self.account_combo['values'] = account_list
            
            if account_list:
                # Auto-select first account
                self.account_combo.set(account_list[0])
                self.status_var.set(f"Loaded {len(account_list)} account(s) from database")
                
                # Trigger account selection automatically
                self.on_account_selected()
                
            else:
                self.account_combo.set("")
                self.status_var.set("No accounts - Click 'Manage Accounts' to add")
            
            self.accounts = accounts  # Store for reference
            self.logger.info(f"✅ Loaded {len(accounts)} accounts from unified database")
            
        except Exception as e:
            self.logger.error(f"Error loading accounts from database: {e}")
            self.accounts = []
    
    def on_account_selected(self, event=None):
        """Handle account selection from dropdown"""
        selected = self.account_combo.get()
        if selected and hasattr(self.app, 'tab_manager') and self.app.tab_manager.live_feed_tab:
            # Remove @ symbol
            username = selected.replace('@', '')
            
            # Update Live Feed tab with selected account
            live_feed = self.app.tab_manager.live_feed_tab
            live_feed.set_selected_account(username)
            
            # Update Arduino tab if available
            if hasattr(self.app, 'tab_coordinator'):
                self.app.tab_coordinator.connect_arduino_to_account(username)
            
            # Hook ke live feed tab untuk mendapatkan tracker reference
            if hasattr(self.app, 'tab_coordinator'):
                self.app.tab_coordinator.setup_arduino_tracker_connection(live_feed)
            
            self.status_var.set(f"Selected: {selected}")
            self.logger.info(f"Account selected: {selected}")
    
    def open_account_manager(self):
        """Open Account Manager popup dialog with unified database"""
        try:
            from src.gui.account_manager_dialog_unified import AccountManagerDialogUnified
            
            dialog = AccountManagerDialogUnified(self.app.root, self.app.db_manager)
            self.app.root.wait_window(dialog.dialog)
            
            # Reload accounts after dialog closes
            self.load_accounts()
            
        except Exception as e:
            self.logger.error(f"Error opening account manager: {e}")
            # Fallback: Create a simple add account dialog
            self._simple_add_account_dialog()
    
    def _simple_add_account_dialog(self):
        """Simple fallback dialog for adding accounts"""
        username = simpledialog.askstring("Add Account", 
                                         "Enter TikTok username (without @):")
        if username and username.strip():
            username = username.replace('@', '').strip()
            
            try:
                account_id = self.app.db_manager.create_account(username)
                self.load_accounts()  # Refresh dropdown
                self.status_var.set(f"✅ Added account @{username}")
                messagebox.showinfo("Success", f"Account @{username} added successfully!")
                
            except Exception as e:
                self.logger.error(f"Error adding account: {e}")
                messagebox.showerror("Error", f"Failed to add account:\n{e}")
    
    def get_selected_account(self):
        """Get currently selected account"""
        selected = self.account_combo.get()
        if selected:
            return selected.replace('@', '')
        return None
    
    def refresh_accounts(self):
        """Refresh account list"""
        self.load_accounts()
