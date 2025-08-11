"""
Account Manager Dialog - Unified Database Version
================================================

Enhanced popup dialog using unified SQLite database instead of JSON:
- Add/Edit/Delete TikTok accounts  
- Account list with complete info (ID, Username, Status)
- Account validation and testing
- SQLite-based data storage (unified with Arduino components)
- Modal popup dialog

Integration with tiktok_live_lite.db database
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from core.database_manager import DatabaseManager


class AccountManagerDialogUnified:
    """Account Manager as popup dialog with unified database"""
    
    def __init__(self, parent, db_manager: DatabaseManager):
        self.parent = parent
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.setup_dialog()
        
        # Widgets dictionary for easy access
        self.widgets = {}
        
        # Create UI
        self._create_widgets()
        
        # Load accounts from database
        self.load_accounts()
        
        # Current editing account ID
        self.editing_account_id = None
    
    def setup_dialog(self):
        """Setup dialog window properties"""
        self.dialog.title("🔧 Account Manager - Unified Database")
        self.dialog.geometry("700x500")
        self.dialog.minsize(600, 400)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Center dialog on parent
        self.center_dialog()
        
        self.logger.info("Account Manager Dialog (Unified) opened")
    
    def center_dialog(self):
        """Center dialog on parent window"""
        self.dialog.update_idletasks()
        
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        dialog_width = self.dialog.winfo_width()
        dialog_height = self.dialog.winfo_height()
        
        x = parent_x + (parent_width // 2) - (dialog_width // 2)
        y = parent_y + (parent_height // 2) - (dialog_height // 2)
        
        self.dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
    
    def _create_widgets(self):
        """Create dialog widgets"""
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(title_frame, text="🎭 TikTok Account Manager", 
                 font=('Arial', 14, 'bold')).pack(side=tk.LEFT)
        
        ttk.Label(title_frame, text="📊 Unified Database", 
                 font=('Arial', 10), foreground='blue').pack(side=tk.RIGHT)
        
        # Account list frame
        list_frame = ttk.LabelFrame(main_frame, text="📋 Accounts", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Account treeview
        columns = ('ID', 'Username', 'Created', 'Status')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=10)
        
        # Configure columns
        self.tree.heading('ID', text='ID')
        self.tree.heading('Username', text='Username')
        self.tree.heading('Created', text='Created')
        self.tree.heading('Status', text='Status')
        
        self.tree.column('ID', width=50, minwidth=50)
        self.tree.column('Username', width=150, minwidth=100)
        self.tree.column('Created', width=120, minwidth=100)
        self.tree.column('Status', width=100, minwidth=80)
        
        # Scrollbar for treeview
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Account management frame
        mgmt_frame = ttk.LabelFrame(main_frame, text="⚙️ Account Management", padding=10)
        mgmt_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Input frame
        input_frame = ttk.Frame(mgmt_frame)
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(input_frame, text="Username:").pack(side=tk.LEFT)
        
        self.username_var = tk.StringVar()
        self.username_entry = ttk.Entry(input_frame, textvariable=self.username_var, 
                                       width=30, font=('Arial', 10))
        self.username_entry.pack(side=tk.LEFT, padx=(5, 10))
        
        # Buttons frame
        btn_frame = ttk.Frame(mgmt_frame)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="➕ Add Account", 
                  command=self.add_account).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(btn_frame, text="✏️ Edit Selected", 
                  command=self.edit_selected_account).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(btn_frame, text="🗑️ Delete Selected", 
                  command=self.delete_selected_account).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(btn_frame, text="🔄 Refresh", 
                  command=self.load_accounts).pack(side=tk.LEFT, padx=(0, 5))
        
        # Bottom frame (Close button)
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X)
        
        ttk.Button(bottom_frame, text="✅ Close", 
                  command=self.dialog.destroy).pack(side=tk.RIGHT)
        
        # Status label
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(bottom_frame, textvariable=self.status_var, 
                 font=('Arial', 9)).pack(side=tk.LEFT)
        
        # Bind events
        self.tree.bind('<Double-1>', self.on_item_double_click)
        self.username_entry.bind('<Return>', lambda e: self.add_account())
        
        self.logger.info("Account Manager Dialog widgets created")
    
    def load_accounts(self):
        """Load accounts from unified database"""
        try:
            # Clear existing items
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Get accounts from database
            accounts = self.db_manager.get_all_accounts()
            
            # Populate treeview
            for account in accounts:
                # Format created date
                created_str = account.get('created_at', 'Unknown')
                if created_str and created_str != 'Unknown':
                    try:
                        # Convert to readable format
                        created_date = datetime.fromisoformat(created_str.replace('Z', '+00:00'))
                        created_str = created_date.strftime('%Y-%m-%d %H:%M')
                    except:
                        pass
                
                self.tree.insert('', 'end', values=(
                    account['id'],
                    f"@{account['username']}",
                    created_str,
                    'Active'
                ))
            
            self.status_var.set(f"✅ Loaded {len(accounts)} accounts from database")
            self.logger.info(f"Loaded {len(accounts)} accounts from unified database")
            
        except Exception as e:
            self.logger.error(f"Error loading accounts: {e}")
            self.status_var.set("❌ Error loading accounts")
            messagebox.showerror("Error", f"Failed to load accounts:\n{e}")
    
    def add_account(self):
        """Add new account to database"""
        username = self.username_var.get().strip()
        if not username:
            messagebox.showwarning("Warning", "Please enter a username")
            self.username_entry.focus()
            return
        
        # Remove @ if present
        username = username.replace('@', '')
        
        try:
            # Add account using database manager
            account_id = self.db_manager.add_account(username)
            
            self.username_var.set("")  # Clear input
            self.load_accounts()  # Refresh list
            
            self.status_var.set(f"✅ Added account @{username} (ID: {account_id})")
            self.logger.info(f"Added account: @{username} (ID: {account_id})")
            
            messagebox.showinfo("Success", f"Account @{username} added successfully!")
            
        except Exception as e:
            self.logger.error(f"Error adding account: {e}")
            self.status_var.set("❌ Error adding account")
            messagebox.showerror("Error", f"Failed to add account:\n{e}")
    
    def edit_selected_account(self):
        """Edit selected account"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an account to edit")
            return
        
        item = self.tree.item(selection[0])
        account_id = item['values'][0]
        current_username = item['values'][1].replace('@', '')
        
        # Simple edit dialog
        new_username = simpledialog.askstring(
            "Edit Account",
            f"Edit username for account ID {account_id}:",
            initialvalue=current_username
        )
        
        if new_username and new_username.strip():
            new_username = new_username.replace('@', '').strip()
            
            try:
                # Update using database (if method exists)
                # For now, show not implemented message
                messagebox.showinfo("Info", "Account editing will be implemented in next version")
                
            except Exception as e:
                self.logger.error(f"Error editing account: {e}")
                messagebox.showerror("Error", f"Failed to edit account:\n{e}")
    
    def delete_selected_account(self):
        """Delete selected account"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an account to delete")
            return
        
        item = self.tree.item(selection[0])
        account_id = item['values'][0]
        username = item['values'][1]
        
        # Confirm deletion
        if messagebox.askyesno("Confirm Delete", 
                              f"Are you sure you want to delete account {username}?\n\n"
                              f"This will also delete all related Arduino settings and rules."):
            try:
                success = self.db_manager.delete_account(int(account_id))
                
                if success:
                    self.load_accounts()  # Refresh list
                    self.status_var.set(f"✅ Deleted account {username}")
                    self.logger.info(f"Deleted account: {username} (ID: {account_id})")
                    messagebox.showinfo("Success", f"Account {username} deleted successfully!")
                else:
                    self.status_var.set("❌ Error deleting account")
                    messagebox.showerror("Error", "Failed to delete account")
                
            except Exception as e:
                self.logger.error(f"Error deleting account: {e}")
                self.status_var.set("❌ Error deleting account")
                messagebox.showerror("Error", f"Failed to delete account:\n{e}")
    
    def on_item_double_click(self, event):
        """Handle double-click on account item"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            username = item['values'][1]
            messagebox.showinfo("Account Info", 
                              f"Account: {username}\n"
                              f"ID: {item['values'][0]}\n"
                              f"Created: {item['values'][2]}\n"
                              f"Status: {item['values'][3]}")
