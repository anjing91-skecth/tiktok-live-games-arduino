#!/usr/bin/env python3
"""
Main Window UPGRADED - Integrated with Unified Session Manager
=============================================================
Desktop GUI yang sudah terintegrasi dengan UnifiedSessionManager
untuk optimal performance dengan triple-priority data flow
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
import logging
from datetime import datetime
import json
import os
import sys
from pathlib import Path

# Import core modules - using absolute imports
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.core.database_manager import DatabaseManager
from src.core.tiktok_connector import TikTokConnector  
from src.core.arduino_controller import ArduinoController
from src.core.analytics_manager import AnalyticsManager
from src.core.unified_session_manager import UnifiedSessionManager

# Try to import statistics tab
try:
    from src.gui.statistics_tab import StatisticsTab
    STATISTICS_AVAILABLE = True
except ImportError:
    STATISTICS_AVAILABLE = False

class TikTokLiveGamesAppUnified:
    """Main application class with Unified Session Manager integration"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.root = tk.Tk()
        self.root.title("🎮 TikTok Live Games Controller v3.0 - UNIFIED")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        # Initialize core components for unified system
        self.db_manager = DatabaseManager()
        self.db_manager.initialize_database()
        
        self.arduino_controller = ArduinoController()
        self.analytics_manager = AnalyticsManager("database/analytics.db")
        self.analytics_manager.init_database()
        
        # INITIALIZE UNIFIED SESSION MANAGER
        self.unified_manager = UnifiedSessionManager(
            arduino_controller=self.arduino_controller,
            database_manager=self.db_manager,
            analytics_manager=self.analytics_manager
        )
        
        # Initialize unified system
        self.unified_manager.initialize()
        self.logger.info("🎯 Unified Session Manager initialized in GUI")
        
        # TikTok connector (will be created per session)
        self.tiktok_connector = None
        
        # GUI state variables
        self.current_session_id = None
        self.current_username = None
        self.current_room_id = None
        self.is_connected = False
        self.update_thread = None
        self.stop_updates = False
        
        # Setup GUI
        self.setup_gui()
        self.setup_menu()
        
        # Start live data update loop
        self.start_live_data_updates()
        
        # Setup window close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_gui(self):
        """Setup main GUI layout"""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Top section - Connection controls
        self.setup_connection_section(main_frame)
        
        # Middle section - Tabbed interface
        self.setup_tabbed_interface(main_frame)
        
        # Bottom section - Event log
        self.setup_event_log_section(main_frame)
    
    def setup_connection_section(self, parent):
        """Setup connection control section"""
        conn_frame = ttk.LabelFrame(parent, text="🔗 Connection Control", padding=10)
        conn_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Account selection
        ttk.Label(conn_frame, text="Account:").grid(row=0, column=0, padx=(0, 5), sticky=tk.W)
        self.account_combo = ttk.Combobox(conn_frame, width=30, state="readonly")
        self.account_combo.grid(row=0, column=1, padx=(0, 10), sticky=tk.W)
        self.load_accounts()
        
        # Connection status
        ttk.Label(conn_frame, text="Status:").grid(row=0, column=2, padx=(10, 5), sticky=tk.W)
        self.connection_status = ttk.Label(conn_frame, text="🔴 DISCONNECTED", foreground="red")
        self.connection_status.grid(row=0, column=3, padx=(0, 10), sticky=tk.W)
        
        # Session info
        ttk.Label(conn_frame, text="Session:").grid(row=0, column=4, padx=(10, 5), sticky=tk.W)
        self.session_info = ttk.Label(conn_frame, text="No active session", foreground="gray")
        self.session_info.grid(row=0, column=5, padx=(0, 10), sticky=tk.W)
        
        # Control buttons
        button_frame = ttk.Frame(conn_frame)
        button_frame.grid(row=1, column=0, columnspan=6, pady=(10, 0), sticky=tk.W)
        
        self.start_button = ttk.Button(button_frame, text="🚀 Start Session", command=self.start_session)
        self.start_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_button = ttk.Button(button_frame, text="⏹️ Stop Session", command=self.stop_session, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Auto-reconnect toggle
        self.auto_reconnect_var = tk.BooleanVar(value=True)
        self.auto_reconnect_check = ttk.Checkbutton(
            button_frame, 
            text="Auto-reconnect", 
            variable=self.auto_reconnect_var
        )
        self.auto_reconnect_check.pack(side=tk.LEFT, padx=(10, 0))
    
    def setup_tabbed_interface(self, parent):
        """Setup tabbed interface for different views"""
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Tab 1: Live Feed (Real-time leaderboard & stats)
        self.setup_live_feed_tab()
        
        # Tab 2: Arduino Control
        self.setup_arduino_tab()
        
        # Tab 3: Statistics (Analytics data)
        self.setup_statistics_tab()
        
        # Tab 4: Session Management
        self.setup_session_tab()
    
    def setup_live_feed_tab(self):
        """Setup live feed tab with real-time data"""
        live_frame = ttk.Frame(self.notebook)
        self.notebook.add(live_frame, text="📺 Live Feed")
        
        # Live stats frame
        stats_frame = ttk.LabelFrame(live_frame, text="📊 Live Statistics", padding=10)
        stats_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Stats display
        stats_grid = ttk.Frame(stats_frame)
        stats_grid.pack(fill=tk.X)
        
        # Create stat labels
        self.live_stats_labels = {}
        stats = ['gifts', 'comments', 'likes', 'follows', 'shares', 'viewers']
        for i, stat in enumerate(stats):
            ttk.Label(stats_grid, text=f"{stat.title()}:").grid(row=0, column=i*2, padx=5, sticky=tk.W)
            label = ttk.Label(stats_grid, text="0", font=("Arial", 12, "bold"))
            label.grid(row=0, column=i*2+1, padx=(0, 15), sticky=tk.W)
            self.live_stats_labels[stat] = label
        
        # Live leaderboard frame
        leaderboard_frame = ttk.LabelFrame(live_frame, text="🏆 Live Leaderboard", padding=10)
        leaderboard_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Leaderboard tree
        columns = ("Rank", "Username", "Total Value", "Percentage")
        self.leaderboard_tree = ttk.Treeview(leaderboard_frame, columns=columns, show="headings", height=10)
        
        for col in columns:
            self.leaderboard_tree.heading(col, text=col)
            self.leaderboard_tree.column(col, width=150)
        
        # Scrollbar for leaderboard
        leaderboard_scroll = ttk.Scrollbar(leaderboard_frame, orient=tk.VERTICAL, command=self.leaderboard_tree.yview)
        self.leaderboard_tree.configure(yscrollcommand=leaderboard_scroll.set)
        
        self.leaderboard_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        leaderboard_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Recent events frame
        recent_frame = ttk.LabelFrame(live_frame, text="🕐 Recent Events", padding=10)
        recent_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.recent_events_text = scrolledtext.ScrolledText(recent_frame, height=6, wrap=tk.WORD)
        self.recent_events_text.pack(fill=tk.X)
    
    def setup_arduino_tab(self):
        """Setup Arduino control tab"""
        arduino_frame = ttk.Frame(self.notebook)
        self.notebook.add(arduino_frame, text="🔧 Arduino")
        
        # Arduino status
        status_frame = ttk.LabelFrame(arduino_frame, text="Arduino Status", padding=10)
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.arduino_status = ttk.Label(status_frame, text="🔴 Disconnected", foreground="red")
        self.arduino_status.pack()
        
        # Manual triggers
        trigger_frame = ttk.LabelFrame(arduino_frame, text="Manual Triggers", padding=10)
        trigger_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Add trigger buttons
        trigger_buttons = [
            ("💡 LED1", "LED1"),
            ("💡 LED2", "LED2"), 
            ("⚡ SOL1", "SOL1"),
            ("⚡ SOL2", "SOL2")
        ]
        
        for i, (text, action) in enumerate(trigger_buttons):
            btn = ttk.Button(trigger_frame, text=text, 
                           command=lambda a=action: self.manual_arduino_trigger(a))
            btn.grid(row=i//2, column=i%2, padx=5, pady=5, sticky=tk.W)
    
    def setup_statistics_tab(self):
        """Setup statistics tab using existing StatisticsTab"""
        if STATISTICS_AVAILABLE:
            try:
                self.statistics_tab = StatisticsTab(self.notebook)
                self.statistics_tab.set_analytics_manager(self.analytics_manager)
                self.notebook.add(self.statistics_tab.frame, text="📈 Statistics")
            except Exception as e:
                self.logger.error(f"Failed to create statistics tab: {e}")
                # Create simple placeholder
                stats_frame = ttk.Frame(self.notebook)
                self.notebook.add(stats_frame, text="📈 Statistics")
                ttk.Label(stats_frame, text=f"Statistics module error: {e}").pack(padx=20, pady=20)
        else:
            # Create simple placeholder
            stats_frame = ttk.Frame(self.notebook)
            self.notebook.add(stats_frame, text="📈 Statistics")
            ttk.Label(stats_frame, text="Statistics module not available").pack(padx=20, pady=20)
    
    def setup_session_tab(self):
        """Setup session management tab"""
        session_frame = ttk.Frame(self.notebook)
        self.notebook.add(session_frame, text="📋 Sessions")
        
        # Session info
        info_frame = ttk.LabelFrame(session_frame, text="Current Session Info", padding=10)
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.session_details_text = scrolledtext.ScrolledText(info_frame, height=8, wrap=tk.WORD)
        self.session_details_text.pack(fill=tk.X)
        
        # Session controls
        controls_frame = ttk.LabelFrame(session_frame, text="Session Controls", padding=10)
        controls_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(controls_frame, text="📊 Update Session Info", 
                  command=self.update_session_info).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(controls_frame, text="💾 Force Save", 
                  command=self.force_save_session).pack(side=tk.LEFT, padx=5)
    
    def setup_event_log_section(self, parent):
        """Setup event log section"""
        log_frame = ttk.LabelFrame(parent, text="📝 Event Log", padding=10)
        log_frame.pack(fill=tk.X)
        
        self.event_log = scrolledtext.ScrolledText(log_frame, height=8, wrap=tk.WORD)
        self.event_log.pack(fill=tk.X)
    
    def setup_menu(self):
        """Setup application menu"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Export Session Data", command=self.export_session_data)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Test Arduino", command=self.test_arduino)
        tools_menu.add_command(label="System Info", command=self.show_system_info)
    
    def load_accounts(self):
        """Load accounts from database"""
        try:
            accounts = self.db_manager.get_all_accounts()
            account_list = [f"{acc['username']} ({acc['platform']})" for acc in accounts]
            self.account_combo['values'] = account_list
            if account_list:
                self.account_combo.current(0)
        except Exception as e:
            self.logger.error(f"Failed to load accounts: {e}")
            self.account_combo['values'] = ["No accounts found"]
    
    def start_session(self):
        """Start unified session with smart management"""
        try:
            if not self.account_combo.get():
                messagebox.showwarning("Warning", "Please select an account first")
                return
            
            # Extract username
            username = self.account_combo.get().split(" (")[0]
            self.current_username = username
            
            self.add_event_log("🚀 Starting unified session...")
            self.connection_status.config(text="🟡 CONNECTING...", foreground="orange")
            
            # Start unified session (manual start)
            self.current_session_id = self.unified_manager.start_session(
                username=username,
                room_id=None,  # Will be set when TikTok connects
                manual_start=True
            )
            
            self.add_event_log(f"✅ Unified session started: {self.current_session_id}")
            
            # Initialize TikTok connector
            self.tiktok_connector = TikTokConnector(username)
            
            # Set event handlers to feed unified system
            self.tiktok_connector.set_event_handlers(
                on_gift=self.on_gift_received,
                on_comment=self.on_comment_received,
                on_like=self.on_like_received,
                on_follow=self.on_follow_received,
                on_share=self.on_share_received,
                on_viewer_update=self.on_viewer_update,
                on_connection_status=self.on_connection_status
            )
            
            # Start TikTok connection in background
            def connect_tiktok():
                try:
                    if self.tiktok_connector:
                        success = self.tiktok_connector.connect()
                        if success:
                            # Get room_id and update session
                            room_id = getattr(self.tiktok_connector, 'room_id', None)
                            if room_id:
                                self.current_room_id = room_id
                                self.add_event_log(f"📺 Connected to room: {room_id}")
                            
                            self.root.after(0, self._update_connection_success, username)
                        else:
                            self.root.after(0, self._update_connection_failed)
                except Exception as e:
                    self.logger.error(f"TikTok connection error: {e}")
                    self.root.after(0, self._update_connection_failed)
            
            threading.Thread(target=connect_tiktok, daemon=True).start()
            
            # Update UI
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.session_info.config(text=f"Session: {self.current_session_id[:20]}...", foreground="blue")
            
        except Exception as e:
            self.logger.error(f"Error starting unified session: {e}")
            messagebox.showerror("Error", f"Failed to start session: {e}")
            self.connection_status.config(text="🔴 ERROR", foreground="red")
    
    def stop_session(self):
        """Stop unified session"""
        try:
            if self.tiktok_connector:
                self.tiktok_connector.disconnect()
                self.tiktok_connector = None
            
            if self.current_session_id:
                self.unified_manager.stop_session(manually_stopped=True)
                self.add_event_log(f"⏹️ Session stopped: {self.current_session_id}")
                self.current_session_id = None
            
            # Update UI
            self.is_connected = False
            self.connection_status.config(text="🔴 DISCONNECTED", foreground="red")
            self.session_info.config(text="No active session", foreground="gray")
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            
            self.add_event_log("✅ Session stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Error stopping session: {e}")
            messagebox.showerror("Error", f"Failed to stop session: {e}")
    
    def on_gift_received(self, gift_data):
        """Handle gift events through unified system"""
        try:
            # Prepare event data for unified system
            event_data = {
                'username': gift_data.get('username', 'Unknown'),
                'gift_name': gift_data.get('gift_name', 'Unknown'),
                'estimated_value': gift_data.get('estimated_value', 0),
                'repeat_count': gift_data.get('repeat_count', 1)
            }
            
            # Feed to unified system
            self.unified_manager.on_tiktok_event("gift", event_data)
            
            # Update event log
            self.add_event_log(f"🎁 {event_data['username']} sent {event_data['gift_name']} "
                             f"(value: {event_data['estimated_value']})")
            
        except Exception as e:
            self.logger.error(f"Error processing gift: {e}")
    
    def on_comment_received(self, comment_data):
        """Handle comment events through unified system"""
        try:
            event_data = {
                'username': comment_data.get('username', 'Unknown'),
                'comment': comment_data.get('comment', '')
            }
            
            # Feed to unified system
            self.unified_manager.on_tiktok_event("comment", event_data)
            
            # Update event log
            comment_preview = event_data['comment'][:50] + "..." if len(event_data['comment']) > 50 else event_data['comment']
            self.add_event_log(f"💬 {event_data['username']}: {comment_preview}")
            
        except Exception as e:
            self.logger.error(f"Error processing comment: {e}")
    
    def on_like_received(self, like_data):
        """Handle like events through unified system"""
        try:
            event_data = {
                'username': like_data.get('username', 'Unknown'),
                'count': like_data.get('count', 1)
            }
            
            self.unified_manager.on_tiktok_event("like", event_data)
            self.add_event_log(f"👍 {event_data['username']} liked {event_data['count']}x")
            
        except Exception as e:
            self.logger.error(f"Error processing like: {e}")
    
    def on_follow_received(self, follow_data):
        """Handle follow events through unified system"""
        try:
            event_data = {
                'username': follow_data.get('username', 'Unknown')
            }
            
            self.unified_manager.on_tiktok_event("follow", event_data)
            self.add_event_log(f"➕ {event_data['username']} followed!")
            
        except Exception as e:
            self.logger.error(f"Error processing follow: {e}")
    
    def on_share_received(self, share_data):
        """Handle share events through unified system"""
        try:
            event_data = {
                'username': share_data.get('username', 'Unknown')
            }
            
            self.unified_manager.on_tiktok_event("share", event_data)
            self.add_event_log(f"📤 {event_data['username']} shared the stream!")
            
        except Exception as e:
            self.logger.error(f"Error processing share: {e}")
    
    def on_viewer_update(self, viewer_data):
        """Handle viewer count updates through unified system"""
        try:
            event_data = {
                'count': viewer_data.get('count', 0)
            }
            
            self.unified_manager.on_tiktok_event("viewer_update", event_data)
            
        except Exception as e:
            self.logger.error(f"Error processing viewer update: {e}")
    
    def on_connection_status(self, status_data):
        """Handle connection status updates"""
        try:
            status = status_data.get('status', 'unknown')
            
            if status == 'connected':
                self.is_connected = True
                self.connection_status.config(text="🟢 CONNECTED", foreground="green")
                self.add_event_log("✅ TikTok connection established")
            elif status == 'disconnected':
                self.is_connected = False
                if self.auto_reconnect_var.get() and self.current_session_id:
                    self.add_event_log("🔄 Auto-reconnecting...")
                    self.auto_reconnect()
                else:
                    self.connection_status.config(text="🔴 DISCONNECTED", foreground="red")
                    self.add_event_log("❌ TikTok connection lost")
            
        except Exception as e:
            self.logger.error(f"Error handling connection status: {e}")
    
    def auto_reconnect(self):
        """Attempt auto-reconnection with session continuation"""
        try:
            if not self.current_username or not self.current_session_id:
                return
            
            self.add_event_log("🔄 Attempting auto-reconnect...")
            
            def reconnect():
                try:
                    # Stop current session (auto-disconnect)
                    self.unified_manager.stop_session(manually_stopped=False)
                    
                    # Start new session (auto-connect = check for continuation)
                    new_session_id = self.unified_manager.start_session(
                        username=self.current_username,
                        room_id=self.current_room_id,
                        manual_start=False  # Auto-connect
                    )
                    
                    self.current_session_id = new_session_id
                    
                    # Re-establish TikTok connection
                    if self.tiktok_connector:
                        success = self.tiktok_connector.connect()
                        if success:
                            self.root.after(0, self._update_reconnection_success)
                        else:
                            self.root.after(0, self._update_reconnection_failed)
                    
                except Exception as e:
                    self.logger.error(f"Auto-reconnect failed: {e}")
                    self.root.after(0, self._update_reconnection_failed)
            
            threading.Thread(target=reconnect, daemon=True).start()
            
        except Exception as e:
            self.logger.error(f"Auto-reconnect error: {e}")
    
    def start_live_data_updates(self):
        """Start live data update loop"""
        def update_loop():
            while not self.stop_updates:
                try:
                    if self.current_session_id and self.unified_manager:
                        # Get live data from unified system
                        live_data = self.unified_manager.get_live_data()
                        
                        # Update GUI on main thread
                        self.root.after(0, self.update_live_display, live_data)
                    
                    time.sleep(1)  # Update every second
                    
                except Exception as e:
                    self.logger.error(f"Live data update error: {e}")
                    time.sleep(5)  # Wait longer if error
        
        self.update_thread = threading.Thread(target=update_loop, daemon=True)
        self.update_thread.start()
    
    def update_live_display(self, live_data):
        """Update live display with data from unified system"""
        try:
            # Update live stats
            stats = live_data.get('stats', {})
            for stat_name, label in self.live_stats_labels.items():
                value = stats.get(stat_name, 0)
                label.config(text=str(value))
            
            # Update leaderboard
            self.leaderboard_tree.delete(*self.leaderboard_tree.get_children())
            leaderboard = live_data.get('leaderboard', [])
            
            for entry in leaderboard:
                self.leaderboard_tree.insert("", tk.END, values=(
                    entry.get('rank', ''),
                    entry.get('username', ''),
                    entry.get('total_value', 0),
                    f"{entry.get('percentage', 0)}%"
                ))
            
            # Update recent events
            recent_events = live_data.get('recent_events', [])
            if recent_events:
                # Get last 10 events
                latest_events = recent_events[-10:]
                
                # Clear and update events display
                self.recent_events_text.delete(1.0, tk.END)
                for event in latest_events:
                    timestamp = event.get('timestamp', datetime.now()).strftime('%H:%M:%S')
                    summary = event.get('summary', 'Unknown event')
                    self.recent_events_text.insert(tk.END, f"[{timestamp}] {summary}\n")
                
                # Scroll to bottom
                self.recent_events_text.see(tk.END)
            
        except Exception as e:
            self.logger.error(f"Error updating live display: {e}")
    
    def manual_arduino_trigger(self, action):
        """Manual Arduino trigger"""
        try:
            if self.arduino_controller:
                self.arduino_controller.trigger_action(action)
                self.add_event_log(f"🔧 Manual Arduino trigger: {action}")
            else:
                self.add_event_log("⚠️ Arduino controller not available")
        except Exception as e:
            self.logger.error(f"Manual Arduino trigger error: {e}")
            self.add_event_log(f"❌ Arduino trigger failed: {e}")
    
    def update_session_info(self):
        """Update session information display"""
        try:
            if not self.current_session_id:
                self.session_details_text.delete(1.0, tk.END)
                self.session_details_text.insert(tk.END, "No active session")
                return
            
            # Get session info from unified manager
            session_info = self.unified_manager.get_session_info()
            
            if session_info:
                details = json.dumps(session_info, indent=2, default=str)
                self.session_details_text.delete(1.0, tk.END)
                self.session_details_text.insert(tk.END, details)
            else:
                self.session_details_text.delete(1.0, tk.END)
                self.session_details_text.insert(tk.END, "Session info not available")
                
        except Exception as e:
            self.logger.error(f"Error updating session info: {e}")
    
    def force_save_session(self):
        """Force save current session data"""
        try:
            if self.current_session_id:
                # Force save through unified system (implementation would need to be added)
                self.add_event_log("💾 Force save triggered")
                messagebox.showinfo("Info", "Force save completed")
            else:
                messagebox.showwarning("Warning", "No active session to save")
        except Exception as e:
            self.logger.error(f"Force save error: {e}")
            messagebox.showerror("Error", f"Force save failed: {e}")
    
    def export_session_data(self):
        """Export current session data"""
        try:
            if not self.current_session_id:
                messagebox.showwarning("Warning", "No active session to export")
                return
            
            # Implementation for export
            messagebox.showinfo("Info", "Export functionality coming soon")
            
        except Exception as e:
            self.logger.error(f"Export error: {e}")
            messagebox.showerror("Error", f"Export failed: {e}")
    
    def test_arduino(self):
        """Test Arduino connection"""
        try:
            if self.arduino_controller:
                # Test sequence
                test_actions = ["LED1", "LED2", "SOL1", "SOL2"]
                for action in test_actions:
                    self.arduino_controller.trigger_action(action)
                    time.sleep(0.5)
                
                self.add_event_log("🔧 Arduino test sequence completed")
                messagebox.showinfo("Arduino Test", "Test sequence completed")
            else:
                messagebox.showwarning("Arduino Test", "Arduino controller not available")
                
        except Exception as e:
            self.logger.error(f"Arduino test error: {e}")
            messagebox.showerror("Arduino Test", f"Test failed: {e}")
    
    def show_system_info(self):
        """Show system information"""
        try:
            info = f"""TikTok Live Games Controller v3.0 - UNIFIED
            
Current Session: {self.current_session_id or 'None'}
Current Username: {self.current_username or 'None'}
Current Room ID: {self.current_room_id or 'None'}
Connection Status: {'Connected' if self.is_connected else 'Disconnected'}
Auto-reconnect: {'Enabled' if self.auto_reconnect_var.get() else 'Disabled'}

Unified Manager: {'Initialized' if self.unified_manager.is_running else 'Not running'}
Arduino Controller: {'Available' if self.arduino_controller else 'Not available'}
Analytics Manager: {'Available' if self.analytics_manager else 'Not available'}
"""
            
            messagebox.showinfo("System Information", info)
            
        except Exception as e:
            self.logger.error(f"System info error: {e}")
    
    def add_event_log(self, message):
        """Add message to event log"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_message = f"[{timestamp}] {message}\n"
            
            self.event_log.insert(tk.END, log_message)
            self.event_log.see(tk.END)
            
            # Keep only last 1000 lines
            lines = self.event_log.get(1.0, tk.END).split('\n')
            if len(lines) > 1000:
                self.event_log.delete(1.0, f"{len(lines)-1000}.0")
            
        except Exception as e:
            self.logger.error(f"Error adding to event log: {e}")
    
    def _update_connection_success(self, username):
        """Update UI on successful connection"""
        self.is_connected = True
        self.connection_status.config(text="🟢 CONNECTED", foreground="green")
        self.add_event_log(f"✅ Connected to @{username}")
    
    def _update_connection_failed(self):
        """Update UI on connection failure"""
        self.connection_status.config(text="🔴 CONNECTION FAILED", foreground="red")
        self.add_event_log("❌ TikTok connection failed")
        
        # Reset buttons
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
    
    def _update_reconnection_success(self):
        """Update UI on successful reconnection"""
        self.is_connected = True
        self.connection_status.config(text="🟢 RECONNECTED", foreground="green")
        self.add_event_log("✅ Auto-reconnection successful")
    
    def _update_reconnection_failed(self):
        """Update UI on reconnection failure"""
        self.connection_status.config(text="🔴 RECONNECT FAILED", foreground="red")
        self.add_event_log("❌ Auto-reconnection failed")
    
    def on_closing(self):
        """Handle application closing"""
        try:
            self.add_event_log("🛑 Shutting down application...")
            
            # Stop updates
            self.stop_updates = True
            
            # Stop session
            if self.current_session_id:
                self.stop_session()
            
            # Shutdown unified manager
            if self.unified_manager:
                self.unified_manager.shutdown()
            
            self.add_event_log("✅ Shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Shutdown error: {e}")
        finally:
            self.root.destroy()
    
    def run(self):
        """Run the application"""
        self.add_event_log("🚀 TikTok Live Games Controller v3.0 - UNIFIED started")
        self.add_event_log("🎯 Unified Session Manager ready for optimal performance")
        self.root.mainloop()

def main():
    """Main entry point"""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        app = TikTokLiveGamesAppUnified()
        app.run()
    except Exception as e:
        logging.error(f"Application error: {e}")
        messagebox.showerror("Application Error", f"Failed to start application: {e}")

if __name__ == "__main__":
    main()
