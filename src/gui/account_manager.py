"""
Account Manager GUI untuk TikTok Live Games Desktop Application
Dialog untuk add, edit, dan manage TikTok accounts
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, scrolledtext
import sys
import os
import threading
import time

# Add path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from core.database_manager import DatabaseManager

class AccountManagerDialog:
    """Dialog untuk mengelola TikTok accounts"""
    
    def __init__(self, parent, db_manager):
        self.parent = parent
        self.db_manager = db_manager
        self.dialog = None
        self.accounts_tree = None
        self.refresh_callback = None
        
    def show(self, refresh_callback=None):
        """Show account manager dialog"""
        self.refresh_callback = refresh_callback
        
        # Create dialog window
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("🎭 Account Manager")
        self.dialog.geometry("800x600")
        self.dialog.resizable(True, True)
        
        # Make dialog modal
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        self.setup_ui()
        self.load_accounts()
        
        # Center dialog
        self.center_dialog()
        
    def setup_ui(self):
        """Setup dialog UI components"""
        # Main frame
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(
            main_frame, 
            text="🎭 TikTok Account Management", 
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Toolbar
        self.create_toolbar(main_frame)
        
        # Accounts list
        self.create_accounts_list(main_frame)
        
        # Account details
        self.create_account_details(main_frame)
        
        # Buttons
        self.create_buttons(main_frame)
        
    def create_toolbar(self, parent):
        """Create toolbar with account actions"""
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(
            toolbar, text="➕ Add Account", 
            command=self.add_account
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            toolbar, text="✏️ Edit Account", 
            command=self.edit_account
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            toolbar, text="🗑️ Delete Account", 
            command=self.delete_account
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(
            side=tk.LEFT, fill=tk.Y, padx=10
        )
        
        ttk.Button(
            toolbar, text="🔄 Refresh", 
            command=self.load_accounts
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            toolbar, text="🧪 Test Connection", 
            command=self.test_account_connection
        ).pack(side=tk.LEFT, padx=(0, 5))
        
    def create_accounts_list(self, parent):
        """Create accounts list with treeview"""
        # Frame for list
        list_frame = ttk.LabelFrame(parent, text="📋 TikTok Accounts")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Treeview with scrollbar
        tree_frame = ttk.Frame(list_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        
        # Treeview
        self.accounts_tree = ttk.Treeview(
            tree_frame,
            columns=("id", "username", "display_name", "arduino_port", "status", "created_at"),
            show="headings",
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set
        )
        
        # Configure scrollbars
        v_scrollbar.config(command=self.accounts_tree.yview)
        h_scrollbar.config(command=self.accounts_tree.xview)
        
        # Grid layout
        self.accounts_tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Configure columns
        self.accounts_tree.heading("id", text="ID")
        self.accounts_tree.heading("username", text="Username")
        self.accounts_tree.heading("display_name", text="Display Name")
        self.accounts_tree.heading("arduino_port", text="Arduino Port")
        self.accounts_tree.heading("status", text="Status")
        self.accounts_tree.heading("created_at", text="Created")
        
        # Column widths
        self.accounts_tree.column("id", width=50)
        self.accounts_tree.column("username", width=150)
        self.accounts_tree.column("display_name", width=200)
        self.accounts_tree.column("arduino_port", width=100)
        self.accounts_tree.column("status", width=80)
        self.accounts_tree.column("created_at", width=150)
        
        # Bind selection event
        self.accounts_tree.bind("<<TreeviewSelect>>", self.on_account_select)
        
    def create_account_details(self, parent):
        """Create account details panel"""
        details_frame = ttk.LabelFrame(parent, text="📝 Account Details")
        details_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Details grid
        details_grid = ttk.Frame(details_frame)
        details_grid.pack(fill=tk.X, padx=10, pady=10)
        
        # Account info labels
        self.detail_labels = {}
        
        details = [
            ("ID:", "id"),
            ("Username:", "username"),
            ("Display Name:", "display_name"),
            ("Arduino Port:", "arduino_port"),
            ("Status:", "status"),
            ("Created:", "created_at")
        ]
        
        for i, (label_text, key) in enumerate(details):
            row = i // 2
            col = (i % 2) * 2
            
            ttk.Label(details_grid, text=label_text).grid(
                row=row, column=col, sticky="w", padx=(0, 5), pady=2
            )
            
            self.detail_labels[key] = ttk.Label(
                details_grid, text="-", font=("Arial", 9, "bold")
            )
            self.detail_labels[key].grid(
                row=row, column=col+1, sticky="w", padx=(0, 20), pady=2
            )
            
    def create_buttons(self, parent):
        """Create dialog buttons"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(
            button_frame, text="✅ Close", 
            command=self.close_dialog
        ).pack(side=tk.RIGHT, padx=(5, 0))
        
        ttk.Button(
            button_frame, text="📊 Export Data", 
            command=self.export_accounts
        ).pack(side=tk.RIGHT, padx=(5, 0))
        
    def load_accounts(self):
        """Load accounts from database"""
        try:
            # Clear existing items
            for item in self.accounts_tree.get_children():
                self.accounts_tree.delete(item)
                
            # Load accounts
            accounts = self.db_manager.get_all_accounts()
            
            for account in accounts:
                # Format created date
                created_at = account.get('created_at', 'Unknown')
                if isinstance(created_at, str) and len(created_at) > 16:
                    created_at = created_at[:16]  # Truncate timestamp
                
                self.accounts_tree.insert("", "end", values=(
                    account['id'],
                    account['username'],
                    account['display_name'],
                    account['arduino_port'],
                    account['status'],
                    created_at
                ))
                
            # Update status
            count = len(accounts)
            self.dialog.title(f"🎭 Account Manager ({count} accounts)")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load accounts: {e}")
            
    def on_account_select(self, event):
        """Handle account selection"""
        try:
            selection = self.accounts_tree.selection()
            if not selection:
                # Clear details
                for label in self.detail_labels.values():
                    label.config(text="-")
                return
                
            # Get selected account
            item = self.accounts_tree.item(selection[0])
            values = item['values']
            
            if len(values) >= 6:
                # Update detail labels
                details = ["id", "username", "display_name", "arduino_port", "status", "created_at"]
                for i, key in enumerate(details):
                    self.detail_labels[key].config(text=str(values[i]))
                    
        except Exception as e:
            print(f"Selection error: {e}")
            
    def add_account(self):
        """Add new account"""
        dialog = AddEditAccountDialog(self.dialog, self.db_manager)
        result = dialog.show()
        
        if result:
            self.load_accounts()
            if self.refresh_callback:
                self.refresh_callback()
                
    def edit_account(self):
        """Edit selected account"""
        try:
            selection = self.accounts_tree.selection()
            if not selection:
                messagebox.showwarning("Warning", "Please select an account to edit")
                return
                
            # Get selected account ID
            item = self.accounts_tree.item(selection[0])
            account_id = item['values'][0]
            
            # Get account details
            accounts = self.db_manager.get_all_accounts()
            account = next((acc for acc in accounts if acc['id'] == account_id), None)
            
            if not account:
                messagebox.showerror("Error", "Account not found")
                return
                
            # Show edit dialog
            dialog = AddEditAccountDialog(self.dialog, self.db_manager, account)
            result = dialog.show()
            
            if result:
                self.load_accounts()
                if self.refresh_callback:
                    self.refresh_callback()
                    
        except Exception as e:
            messagebox.showerror("Error", f"Failed to edit account: {e}")
            
    def delete_account(self):
        """Delete selected account"""
        try:
            selection = self.accounts_tree.selection()
            if not selection:
                messagebox.showwarning("Warning", "Please select an account to delete")
                return
                
            # Get selected account
            item = self.accounts_tree.item(selection[0])
            account_id = item['values'][0]
            username = item['values'][1]
            
            # Confirm deletion
            if not messagebox.askyesno(
                "Confirm Delete", 
                f"Are you sure you want to delete account '@{username}'?\n\n"
                "This will also delete all associated sessions and data."
            ):
                return
                
            # Delete account
            self.db_manager.delete_account(account_id)
            
            # Refresh
            self.load_accounts()
            if self.refresh_callback:
                self.refresh_callback()
                
            messagebox.showinfo("Success", f"Account '@{username}' deleted successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete account: {e}")
            
    def test_account_connection(self):
        """Test TikTok connection for selected account"""
        try:
            selection = self.accounts_tree.selection()
            if not selection:
                messagebox.showwarning("Warning", "Please select an account to test")
                return
                
            # Get selected account
            item = self.accounts_tree.item(selection[0])
            account_id = item['values'][0]
            username = item['values'][1]
            
            # Create test dialog
            self.show_connection_test_dialog(account_id, username)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to test connection: {e}")
    
    def show_connection_test_dialog(self, account_id, username):
        """Show connection test dialog with real-time results"""
        
        # Create test dialog
        test_dialog = tk.Toplevel(self.parent)
        test_dialog.title(f"Testing Connection - @{username}")
        test_dialog.geometry("500x400")
        test_dialog.resizable(True, True)
        
        # Make dialog modal
        test_dialog.transient(self.parent)
        test_dialog.grab_set()
        
        # Center dialog
        test_dialog.geometry("+%d+%d" % (
            self.parent.winfo_rootx() + 50,
            self.parent.winfo_rooty() + 50
        ))
        
        # Header
        header_frame = tk.Frame(test_dialog)
        header_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(
            header_frame, 
            text=f"🔍 Testing TikTok Connection",
            font=("Arial", 12, "bold")
        ).pack(side="left")
        
        # Status label
        self.test_status_label = tk.Label(
            header_frame, 
            text="🔄 Initializing...",
            fg="blue"
        )
        self.test_status_label.pack(side="right")
        
        # Progress bar
        progress_frame = tk.Frame(test_dialog)
        progress_frame.pack(fill="x", padx=10, pady=5)
        
        self.test_progress = ttk.Progressbar(
            progress_frame, 
            mode='indeterminate'
        )
        self.test_progress.pack(fill="x")
        
        # Results area
        results_frame = tk.LabelFrame(test_dialog, text="Test Results", padx=5, pady=5)
        results_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.test_results = scrolledtext.ScrolledText(
            results_frame,
            height=15,
            font=("Consolas", 9)
        )
        self.test_results.pack(fill="both", expand=True)
        
        # Buttons
        button_frame = tk.Frame(test_dialog)
        button_frame.pack(fill="x", padx=10, pady=5)
        
        self.test_stop_btn = tk.Button(
            button_frame,
            text="⏹ Stop Test",
            command=lambda: self.stop_connection_test(),
            state="normal"
        )
        self.test_stop_btn.pack(side="left")
        
        self.test_close_btn = tk.Button(
            button_frame,
            text="✕ Close",
            command=test_dialog.destroy,
            state="disabled"
        )
        self.test_close_btn.pack(side="right")
        
        # Start test
        self.test_running = True
        self.test_progress.start()
        
        def run_test():
            self.run_connection_test(account_id, username, test_dialog)
        
        test_thread = threading.Thread(target=run_test, daemon=True)
        test_thread.start()
        
    def run_connection_test(self, account_id, username, dialog):
        """Run the actual connection test"""
        try:
            self.log_test_result(f"🚀 Starting connection test for @{username}")
            self.log_test_result(f"Account ID: {account_id}")
            self.log_test_result("=" * 50)
            
            # Test 1: Database connection
            self.update_test_status("📊 Testing database connection...")
            account = self.db_manager.get_account(account_id)
            if account:
                self.log_test_result("✅ Database connection: OK")
                self.log_test_result(f"   - Display Name: {account['display_name']}")
                self.log_test_result(f"   - Arduino Port: {account['arduino_port']}")
                self.log_test_result(f"   - Status: {account['status']}")
            else:
                self.log_test_result("❌ Database connection: FAILED")
                return
            
            if not self.test_running:
                return
                
            # Test 2: TikTok API connection
            self.update_test_status("🎵 Testing TikTok Live API...")
            self.log_test_result("\n🎵 TikTok Live API Test:")
            
            try:
                from core.tiktok_connector import TikTokConnector
                
                # Create test connector
                connector = TikTokConnector(username)
                self.log_test_result("✅ TikTokConnector initialized")
                
                # Test finding live stream
                self.log_test_result("🔍 Searching for live stream...")
                
                # Simulate connection test (dalam implementasi real, ini akan mencoba connect ke live stream)
                import time
                time.sleep(2)  # Simulate search time
                
                if not self.test_running:
                    return
                    
                self.log_test_result("⚠️  Live stream test: SIMULATED")
                self.log_test_result("   Note: Real live stream detection requires active stream")
                
            except ImportError as e:
                self.log_test_result(f"❌ TikTok API: Import error - {e}")
            except Exception as e:
                self.log_test_result(f"❌ TikTok API: {e}")
            
            if not self.test_running:
                return
                
            # Test 3: Arduino connection
            self.update_test_status("🔌 Testing Arduino connection...")
            self.log_test_result("\n🔌 Arduino Connection Test:")
            
            if account['arduino_port']:
                try:
                    from core.arduino_controller import ArduinoController
                    
                    arduino = ArduinoController()
                    self.log_test_result(f"✅ Arduino controller initialized")
                    self.log_test_result(f"   - Target port: {account['arduino_port']}")
                    
                    # Test connection (simulate)
                    time.sleep(1)
                    self.log_test_result("⚠️  Arduino connection: SIMULATED")
                    self.log_test_result("   Note: Real test requires physical Arduino device")
                    
                except ImportError as e:
                    self.log_test_result(f"❌ Arduino: Import error - {e}")
                except Exception as e:
                    self.log_test_result(f"❌ Arduino: {e}")
            else:
                self.log_test_result("⚠️  No Arduino port configured")
            
            # Test complete
            self.log_test_result("\n" + "=" * 50)
            self.log_test_result("✅ Connection test completed!")
            self.update_test_status("✅ Test completed")
            
        except Exception as e:
            self.log_test_result(f"\n❌ Test failed: {e}")
            self.update_test_status("❌ Test failed")
        finally:
            # Stop progress and enable close button
            self.test_progress.stop()
            self.test_stop_btn.config(state="disabled")
            self.test_close_btn.config(state="normal")
            self.test_running = False
    
    def log_test_result(self, message):
        """Add message to test results"""
        if hasattr(self, 'test_results'):
            self.test_results.insert(tk.END, message + "\n")
            self.test_results.see(tk.END)
            self.test_results.update()
    
    def update_test_status(self, status):
        """Update test status label"""
        if hasattr(self, 'test_status_label'):
            self.test_status_label.config(text=status)
    
    def stop_connection_test(self):
        """Stop the running connection test"""
        self.test_running = False
        self.log_test_result("\n⏹ Test stopped by user")
        self.update_test_status("⏹ Test stopped")
            
    def export_accounts(self):
        """Export accounts data"""
        try:
            accounts = self.db_manager.get_all_accounts()
            
            # Create export text
            export_text = "TikTok Accounts Export\n"
            export_text += "=" * 50 + "\n\n"
            
            for acc in accounts:
                export_text += f"ID: {acc['id']}\n"
                export_text += f"Username: {acc['username']}\n"
                export_text += f"Display Name: {acc['display_name']}\n"
                export_text += f"Arduino Port: {acc['arduino_port']}\n"
                export_text += f"Status: {acc['status']}\n"
                export_text += f"Created: {acc['created_at']}\n"
                export_text += "-" * 30 + "\n\n"
                
            # Show in dialog
            export_dialog = tk.Toplevel(self.dialog)
            export_dialog.title("📊 Export Data")
            export_dialog.geometry("600x400")
            
            text_widget = tk.Text(export_dialog, wrap=tk.WORD)
            text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            text_widget.insert(tk.END, export_text)
            text_widget.config(state=tk.DISABLED)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export data: {e}")
            
    def center_dialog(self):
        """Center dialog on parent"""
        self.dialog.update_idletasks()
        
        # Get parent window position and size
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        # Get dialog size
        dialog_width = self.dialog.winfo_reqwidth()
        dialog_height = self.dialog.winfo_reqheight()
        
        # Calculate center position
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        
    def close_dialog(self):
        """Close dialog"""
        if self.refresh_callback:
            self.refresh_callback()
        self.dialog.destroy()


class AddEditAccountDialog:
    """Dialog untuk add/edit account"""
    
    def __init__(self, parent, db_manager, account=None):
        self.parent = parent
        self.db_manager = db_manager
        self.account = account  # None for add, account dict for edit
        self.dialog = None
        self.result = False
        
        # Form fields
        self.username_var = tk.StringVar()
        self.display_name_var = tk.StringVar()
        self.arduino_port_var = tk.StringVar()
        self.status_var = tk.StringVar(value="active")
        
    def show(self):
        """Show add/edit dialog"""
        # Create dialog
        self.dialog = tk.Toplevel(self.parent)
        title = "✏️ Edit Account" if self.account else "➕ Add Account"
        self.dialog.title(title)
        self.dialog.geometry("500x400")
        self.dialog.resizable(False, False)
        
        # Make modal
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        self.setup_ui()
        
        if self.account:
            self.load_account_data()
            
        self.center_dialog()
        
        # Wait for dialog to close
        self.dialog.wait_window()
        
        return self.result
        
    def setup_ui(self):
        """Setup dialog UI"""
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_text = "Edit TikTok Account" if self.account else "Add New TikTok Account"
        title_label = ttk.Label(
            main_frame, text=title_text, 
            font=("Arial", 14, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Form fields
        self.create_form_fields(main_frame)
        
        # Buttons
        self.create_buttons(main_frame)
        
    def create_form_fields(self, parent):
        """Create form input fields"""
        form_frame = ttk.LabelFrame(parent, text="Account Information")
        form_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Username
        ttk.Label(form_frame, text="Username:").grid(
            row=0, column=0, sticky="w", padx=10, pady=10
        )
        username_entry = ttk.Entry(
            form_frame, textvariable=self.username_var, width=30
        )
        username_entry.grid(row=0, column=1, sticky="ew", padx=10, pady=10)
        
        # Display Name
        ttk.Label(form_frame, text="Display Name:").grid(
            row=1, column=0, sticky="w", padx=10, pady=10
        )
        ttk.Entry(
            form_frame, textvariable=self.display_name_var, width=30
        ).grid(row=1, column=1, sticky="ew", padx=10, pady=10)
        
        # Arduino Port
        ttk.Label(form_frame, text="Arduino Port:").grid(
            row=2, column=0, sticky="w", padx=10, pady=10
        )
        port_combo = ttk.Combobox(
            form_frame, textvariable=self.arduino_port_var, width=28
        )
        port_combo['values'] = ("COM3", "COM4", "COM5", "COM6", "COM7", "COM8")
        port_combo.grid(row=2, column=1, sticky="ew", padx=10, pady=10)
        
        # Status
        ttk.Label(form_frame, text="Status:").grid(
            row=3, column=0, sticky="w", padx=10, pady=10
        )
        status_combo = ttk.Combobox(
            form_frame, textvariable=self.status_var, width=28, state="readonly"
        )
        status_combo['values'] = ("active", "inactive")
        status_combo.grid(row=3, column=1, sticky="ew", padx=10, pady=10)
        
        # Configure grid weights
        form_frame.grid_columnconfigure(1, weight=1)
        
        # Focus on username field
        username_entry.focus()
        
    def create_buttons(self, parent):
        """Create dialog buttons"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(
            button_frame, text="❌ Cancel", 
            command=self.cancel
        ).pack(side=tk.RIGHT, padx=(5, 0))
        
        save_text = "💾 Update" if self.account else "➕ Add"
        ttk.Button(
            button_frame, text=save_text, 
            command=self.save
        ).pack(side=tk.RIGHT, padx=(5, 0))
        
    def load_account_data(self):
        """Load existing account data for editing"""
        if self.account:
            self.username_var.set(self.account.get('username', ''))
            self.display_name_var.set(self.account.get('display_name', ''))
            self.arduino_port_var.set(self.account.get('arduino_port', ''))
            self.status_var.set(self.account.get('status', 'active'))
            
    def save(self):
        """Save account data"""
        try:
            # Validate input
            username = self.username_var.get().strip()
            display_name = self.display_name_var.get().strip()
            arduino_port = self.arduino_port_var.get().strip()
            status = self.status_var.get()
            
            if not username:
                messagebox.showerror("Error", "Username is required")
                return
                
            if not display_name:
                messagebox.showerror("Error", "Display name is required")
                return
                
            # Save to database
            if self.account:
                # Update existing account
                self.db_manager.update_account(
                    self.account['id'],
                    username,
                    display_name,
                    arduino_port,
                    status
                )
                messagebox.showinfo("Success", f"Account '@{username}' updated successfully!")
            else:
                # Add new account
                account_id = self.db_manager.create_account(
                    username, display_name, arduino_port
                )
                messagebox.showinfo("Success", f"Account '@{username}' added successfully! (ID: {account_id})")
            
            self.result = True
            self.dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save account: {e}")
            
    def cancel(self):
        """Cancel dialog"""
        self.result = False
        self.dialog.destroy()
        
    def center_dialog(self):
        """Center dialog on parent"""
        self.dialog.update_idletasks()
        
        # Get parent position and size
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        # Calculate center position
        x = parent_x + (parent_width - self.dialog.winfo_reqwidth()) // 2
        y = parent_y + (parent_height - self.dialog.winfo_reqheight()) // 2
        
        self.dialog.geometry(f"+{x}+{y}")
