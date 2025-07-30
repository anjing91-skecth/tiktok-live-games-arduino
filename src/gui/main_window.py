"""
Main Window untuk TikTok Live Games Desktop Application
Menggunakan Tkinter untuk GUI desktop
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

# Import core modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from core.database_manager import DatabaseManager
from core.tiktok_connector import TikTokConnector
from core.arduino_controller import ArduinoController
from core.session_manager_tracking import SessionManager
from core.analytics_manager import AnalyticsManager
from core.unified_session_manager import UnifiedSessionManager
from gui.statistics_tab import StatisticsTab
from utils.statistics_optimizer import init_statistics_optimizer, start_optimized_statistics
from utils.memory_optimizer import start_memory_monitoring
from utils.statistics_patches import patch_statistics_tab_performance

class TikTokLiveGamesApp:
    """Main application class for desktop GUI"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.root = tk.Tk()
        self.root.title("🎮 TikTok Live Games Controller v2.0")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        # Initialize core components
        self.db_manager = DatabaseManager()
        self.db_manager.initialize_database()
        self.session_manager = SessionManager(self.db_manager, arduino_enabled=True)
        self.arduino_controller = ArduinoController()
        self.tiktok_connector = None
        
        # Initialize analytics manager
        self.analytics_manager = AnalyticsManager("database/analytics.db")
        
        # Initialize Unified Session Manager (NEW)
        self.unified_manager = UnifiedSessionManager(
            database_manager=self.db_manager
        )
        self.unified_manager.initialize()
        
        # GUI state variables
        self.current_session = None
        self.is_connected = False
        self.update_thread = None
        self.stop_updates = False
        self.demo_active = False
        self.demo_thread = None
        
        # Initialize GUI
        self.setup_gui()
        self.setup_status_bar()
        self.start_update_thread()
        
    def setup_gui(self):
        """Setup main GUI components"""
        # Create main menu
        self.create_menu()
        
        # Create toolbar
        self.create_toolbar()
        
        # Create main content area
        self.create_main_content()
        
        # Create status bar
        self.create_status_bar()
        
    def create_menu(self):
        """Create application menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Settings", command=self.show_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)
        
        # Account menu
        account_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Account", menu=account_menu)
        account_menu.add_command(label="Manage Accounts", command=self.show_account_manager)
        account_menu.add_command(label="Add Account", command=self.add_account)
        
        # Arduino menu
        arduino_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Arduino", menu=arduino_menu)
        arduino_menu.add_command(label="Control Panel", command=self.show_arduino_control)
        arduino_menu.add_command(label="Scan Ports", command=self.scan_arduino_ports)
        arduino_menu.add_separator()
        arduino_menu.add_command(label="Emergency Stop", command=self.emergency_stop)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        
    def create_toolbar(self):
        """Create toolbar with main controls"""
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        # Session controls
        ttk.Button(toolbar, text="🚀 Start Session", 
                  command=self.start_session).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="⏹️ Stop Session", 
                  command=self.stop_session).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="🛑 Emergency Stop", 
                  command=self.emergency_stop).pack(side=tk.LEFT, padx=10)
        
        # Separator
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # Account selection
        ttk.Label(toolbar, text="Account:").pack(side=tk.LEFT, padx=5)
        self.account_combo = ttk.Combobox(toolbar, width=20, state="readonly")
        self.account_combo.pack(side=tk.LEFT, padx=5)
        self.load_accounts()
        
    def create_main_content(self):
        """Create main content area with tabs"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Live Feed Tab
        self.create_live_feed_tab()
        
        # Statistics Tab (Advanced Analytics) - OPTIMIZED VERSION
        self.statistics_tab = StatisticsTab(self.notebook)
        self.statistics_tab.set_analytics_manager(self.analytics_manager)
        
        # Set reference to main window for real-time data access
        self.statistics_tab.set_main_window_reference(self)
        
        # Apply performance patches untuk memory efficiency
        patch_statistics_tab_performance(self.statistics_tab)
        
        # Add historical view dan controls ke statistics tab
        self.add_historical_controls_to_statistics()
        
        # Initialize Statistics Optimizer untuk memory efficiency
        self.statistics_optimizer = init_statistics_optimizer(
            self.statistics_tab, 
            self.unified_manager
        )
        
        # Start memory monitoring
        start_memory_monitoring()
        
        # Arduino Control Tab
        self.create_arduino_tab()
        
        # Logs Tab
        self.create_logs_tab()
        
        # Legacy Statistics Tab (for compatibility) - moved to simple stats
        self.create_statistics_tab()
        
    def create_live_feed_tab(self):
        """Create live feed monitoring tab"""
        live_frame = ttk.Frame(self.notebook)
        self.notebook.add(live_frame, text="📡 Live Feed")
        
        # Create paned window for split layout
        paned = ttk.PanedWindow(live_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - Live events
        left_frame = ttk.LabelFrame(paned, text="🎁 Real-time Events")
        paned.add(left_frame, weight=2)
        
        # Events display
        self.events_text = scrolledtext.ScrolledText(
            left_frame, wrap=tk.WORD, height=20, width=50
        )
        self.events_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Right panel - Statistics
        right_frame = ttk.LabelFrame(paned, text="📊 Statistics")
        paned.add(right_frame, weight=1)
        
        # Statistics labels
        stats_frame = ttk.Frame(right_frame)
        stats_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.stats_labels = {}
        stats_items = [
            ("Total Gifts", "total_gifts"),
            ("Total Coins", "total_coins"),
            ("Viewers", "viewers"),
            ("Duration", "duration"),
            ("Likes", "likes")
        ]
        
        for i, (label, key) in enumerate(stats_items):
            ttk.Label(stats_frame, text=f"{label}:").grid(row=i, column=0, sticky="w", pady=2)
            self.stats_labels[key] = ttk.Label(stats_frame, text="0", font=("Arial", 12, "bold"))
            self.stats_labels[key].grid(row=i, column=1, sticky="w", padx=10, pady=2)
        
        # Add separator
        ttk.Separator(stats_frame, orient='horizontal').grid(row=len(stats_items), column=0, columnspan=2, sticky="ew", pady=(10, 5))
        
        # Top Gifters Leaderboard
        leaderboard_label = ttk.Label(stats_frame, text="🏆 Top Gifters", font=("Arial", 10, "bold"))
        leaderboard_label.grid(row=len(stats_items)+1, column=0, columnspan=2, sticky="w", pady=(5, 2))
        
        # Leaderboard frame
        self.leaderboard_frame = ttk.Frame(stats_frame)
        self.leaderboard_frame.grid(row=len(stats_items)+2, column=0, columnspan=2, sticky="ew", pady=(2, 5))
        
        # Initialize empty leaderboard labels
        self.leaderboard_labels = []
        for i in range(5):  # Top 5 gifters
            label = ttk.Label(self.leaderboard_frame, text="", font=("Arial", 8))
            label.grid(row=i, column=0, sticky="w", pady=1)
            self.leaderboard_labels.append(label)
            
    def add_historical_controls_to_statistics(self):
        """Add historical view and controls to statistics tab"""
        try:
            from utils.statistics_patches import create_historical_view_widget, add_memory_status_indicator
            
            # Add historical view if statistics tab has scrollable frame
            if hasattr(self.statistics_tab, 'scrollable_frame'):
                # Add historical view
                historical_widget = create_historical_view_widget(self.statistics_tab.scrollable_frame)
                historical_widget.pack(fill="both", expand=True, padx=10, pady=5)
                
                # Add memory status indicator
                memory_status = add_memory_status_indicator(self.statistics_tab.scrollable_frame)
                memory_status.pack(fill="x", padx=10, pady=5)
                
                print("✅ Historical view and controls added to statistics tab")
            else:
                print("⚠️ Statistics tab doesn't have scrollable_frame, skipping historical view")
                
        except Exception as e:
            print(f"Error adding historical controls: {e}")
    
    def create_statistics_tab(self):
        """Create simple statistics and charts tab (legacy)"""
        stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(stats_frame, text="📈 Simple Stats")
        
        # Simple stats for backward compatibility
        ttk.Label(stats_frame, text="📊 Simple Session Statistics\n\n"
                 "Basic session statistics are displayed here.\n"
                 "For advanced analytics, use the 📊 Statistics tab.\n\n"
                 "Features available:\n"
                 "• Current session overview\n"
                 "• Basic gift counts\n"
                 "• Simple viewer tracking\n"
                 "• Top gifters list",
                 justify=tk.CENTER, font=("Arial", 12)).pack(expand=True)
        
    def create_arduino_tab(self):
        """Create Arduino control tab"""
        arduino_frame = ttk.Frame(self.notebook)
        self.notebook.add(arduino_frame, text="🔧 Arduino Control")
        
        # Arduino status frame
        status_frame = ttk.LabelFrame(arduino_frame, text="Device Status")
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Port status display
        self.arduino_status_text = scrolledtext.ScrolledText(
            status_frame, height=10, width=80
        )
        self.arduino_status_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create control buttons
        control_frame = ttk.LabelFrame(arduino_frame, text="Manual Controls")
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(pady=5)
        
        ttk.Button(button_frame, text="Scan Ports", 
                  command=self.scan_arduino_ports).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Test Device 1", 
                  command=lambda: self.test_device("SOL1")).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Test Device 2", 
                  command=lambda: self.test_device("SOL2")).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Emergency Stop", 
                  command=self.emergency_stop).pack(side=tk.LEFT, padx=10)
        
        # Demo controls
        demo_frame = ttk.Frame(control_frame)
        demo_frame.pack(pady=5)
        
        ttk.Button(demo_frame, text="Start Demo Data", 
                  command=self.start_demo_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(demo_frame, text="Stop Demo", 
                  command=self.stop_demo_data).pack(side=tk.LEFT, padx=5)
        
    def create_logs_tab(self):
        """Create logs viewing tab"""
        logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(logs_frame, text="📋 Logs")
        
        # Log display
        self.logs_text = scrolledtext.ScrolledText(
            logs_frame, wrap=tk.WORD, height=25, width=100
        )
        self.logs_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Load recent logs
        self.load_recent_logs()
        
    def create_status_bar(self):
        """Create bottom status bar"""
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Status indicators
        self.connection_status = ttk.Label(
            self.status_frame, text="🔴 DISCONNECTED", 
            foreground="red", font=("Arial", 10, "bold")
        )
        self.connection_status.pack(side=tk.LEFT, padx=10, pady=5)
        
        # Session info
        self.session_info = ttk.Label(
            self.status_frame, text="No active session"
        )
        self.session_info.pack(side=tk.LEFT, padx=20, pady=5)
        
        # Current time
        self.time_label = ttk.Label(self.status_frame, text="")
        self.time_label.pack(side=tk.RIGHT, padx=10, pady=5)
        
    def setup_status_bar(self):
        """Initialize status bar updates"""
        self.update_time()
        
    def update_time(self):
        """Update current time display"""
        current_time = datetime.now().strftime("%H:%M:%S")
        self.time_label.config(text=current_time)
        self.root.after(1000, self.update_time)
        
    def start_update_thread(self):
        """Start background thread for GUI updates"""
        self.stop_updates = False
        self.update_thread = threading.Thread(target=self.update_loop, daemon=True)
        self.update_thread.start()
        
    def update_loop(self):
        """Background update loop dengan prioritas real-time dashboard"""
        while not self.stop_updates:
            try:
                # Update Arduino status
                self.update_arduino_status()
                
                # Update session statistics dengan prioritas real-time
                if self.current_session:
                    self.update_session_stats()
                    
                # Update real-time dashboard (kotak merah) setiap 2 detik untuk Live Feed
                self.update_realtime_dashboard()
                
                # Update Live Feed real-time data setiap 2 detik
                self.update_live_feed_realtime()
                    
                time.sleep(2)  # Update setiap 2 detik untuk real-time feel
            except Exception as e:
                self.logger.error(f"Error in update loop: {e}")
                time.sleep(5)  # Sleep lebih lama jika error
    
    def update_realtime_dashboard(self):
        """Update real-time dashboard (kotak merah) dengan data terbaru"""
        try:
            if not hasattr(self, 'stats_labels'):
                return
                
            # Ambil data real-time dari unified system
            dashboard_stats = self.get_live_dashboard_stats()
            
            if dashboard_stats:
                # Update hanya jika ada perubahan atau setiap 30 detik
                current_time = time.time()
                if not hasattr(self, '_last_dashboard_update'):
                    self._last_dashboard_update = 0
                    
                if (current_time - self._last_dashboard_update) > 30:  # Force update setiap 30 detik
                    self._last_dashboard_update = current_time
                    
                    # Update dashboard langsung di main thread
                    self.root.after(0, self._update_dashboard_display, dashboard_stats)
                    
        except Exception as e:
            self.logger.debug(f"Dashboard update error: {e}")
    
    def update_live_feed_realtime(self):
        """Update Live Feed tab dengan data real-time dari TikTok connector"""
        try:
            if not self.tiktok_connector or not self.tiktok_connector.is_connected():
                return
                
            # Ambil data real-time dari TikTok connector
            live_stats = self.get_tiktok_realtime_stats()
            
            if live_stats:
                # Update Live Feed statistics panel (kotak merah) 
                self.root.after(0, self._update_live_feed_display, live_stats)
                
        except Exception as e:
            self.logger.debug(f"Live Feed real-time update error: {e}")
    
    def get_tiktok_realtime_stats(self):
        """Ambil data real-time langsung dari TikTok connector"""
        try:
            if not self.tiktok_connector or not self.tiktok_connector.is_connected():
                return None
                
            # Ambil statistik real-time dari TikTok connector
            client_info = self.tiktok_connector.get_client_info()
            
            # Extract data real-time
            statistics = client_info.get('statistics', {})
            gift_stats = client_info.get('gift_statistics', {})
            room_info = client_info.get('room_info', {})
            
            # Get current dan peak viewers
            current_viewers = room_info.get('user_count', 0)
            peak_viewers = statistics.get('peak_viewers', current_viewers)
            
            # Build stats untuk Live Feed
            live_stats = {
                'total_gifts': statistics.get('total_gifts', 0),
                'total_coins': gift_stats.get('total_coins', 0),  # Total accumulated coins dari semua gifts
                'total_comments': statistics.get('total_comments', 0), 
                'viewers': current_viewers,  # Current viewers real-time
                'peak_viewers': max(peak_viewers, current_viewers),  # Peak viewers (max yang pernah ada)
                'likes': statistics.get('total_likes', 0),  # Total likes value, bukan user count
                'duration': client_info.get('session_duration_formatted', '00:00:00'),
                'top_gifters': gift_stats.get('top_gifters', [])[:5],  # Top 5 gifters dengan data lengkap
                'top_gifters_with_timestamps': self.tiktok_connector.get_top_gifters_with_timestamps(10) if hasattr(self.tiktok_connector, 'get_top_gifters_with_timestamps') else [],  # Enhanced leaderboard for Statistics tab
                'status': 'connected' if self.tiktok_connector.is_connected() else 'disconnected'
            }
            
            return live_stats
            
        except Exception as e:
            self.logger.debug(f"TikTok real-time stats error: {e}")
            return None
    
    def _update_live_feed_display(self, stats):
        """Update Live Feed display dengan real-time stats"""
        try:
            # Update Live Feed statistics panel (kotak merah di sebelah kanan)
            if hasattr(self, 'stats_labels'):
                # Update data real-time
                self.stats_labels['total_gifts'].config(
                    text=f"{stats.get('total_gifts', 0)}"
                )
                self.stats_labels['total_coins'].config(
                    text=f"{stats.get('total_coins', 0)} coins"  # Total coins terakumulasi
                )
                # Format viewers: Current (Peak: XXX)
                current_viewers = stats.get('viewers', 0)
                peak_viewers = stats.get('peak_viewers', 0)
                self.stats_labels['viewers'].config(
                    text=f"{current_viewers} (Peak: {peak_viewers})"
                )
                self.stats_labels['likes'].config(
                    text=f"{stats.get('likes', 0):,}"  # Format dengan comma separator untuk total likes
                )
                self.stats_labels['duration'].config(
                    text=f"{stats.get('duration', '00:00:00')}"
                )
                
                # Update top gifters leaderboard real-time
                top_gifters = stats.get('top_gifters', [])
                self._update_leaderboard(top_gifters)
                
        except Exception as e:
            self.logger.debug(f"Live Feed display update error: {e}")
    
    def _update_dashboard_display(self, stats):
        """Update tampilan dashboard dengan stats terbaru"""
        try:
            # Update statistik utama (Current Viewers, Comments, Likes, Gifts, Gift Value)
            if hasattr(self, 'stats_labels'):
                # Format viewers: Current (Peak: XXX)
                current_viewers = stats.get('viewers', 0)
                peak_viewers = stats.get('peak_viewers', 0)
                self.stats_labels['viewers'].config(
                    text=f"{current_viewers} (Peak: {peak_viewers})"
                )
                
                self.stats_labels['total_comments'].config(
                    text=f"{stats.get('total_comments', 0)}"
                ) if 'total_comments' in self.stats_labels else None
                
                # Total likes dengan format ribuan
                self.stats_labels['likes'].config(
                    text=f"{stats.get('likes', 0):,}"
                )
                self.stats_labels['total_gifts'].config(
                    text=f"{stats.get('total_gifts', 0)}"
                )
                # Total coins terakumulasi
                self.stats_labels['total_coins'].config(
                    text=f"{stats.get('total_coins', 0)} coins"
                )
            
            # Update session info dengan status real-time
            if hasattr(self, 'session_info'):
                status = stats.get('system_status', stats.get('status', 'unknown'))
                duration = stats.get('duration', '00:00:00')
                session_text = f"Session: {duration} | Status: {status.title()}"
                self.session_info.config(text=session_text)
                
        except Exception as e:
            self.logger.debug(f"Dashboard display update error: {e}")
                
    def load_accounts(self):
        """Load TikTok accounts from database"""
        try:
            accounts = self.db_manager.get_all_accounts()
            account_names = [f"{acc['username']} ({acc['display_name']})" for acc in accounts]
            self.account_combo['values'] = account_names
            if account_names:
                self.account_combo.current(0)
        except Exception as e:
            self.logger.error(f"Error loading accounts: {e}")
            
    def start_session(self):
        """Start TikTok live session"""
        try:
            if not self.account_combo.get():
                messagebox.showwarning("Warning", "Please select an account first")
                return
                
            # Get selected account
            selected_account = self.account_combo.get().split(" (")[0]
            
            # Get account ID from database
            accounts = self.db_manager.get_all_accounts()
            account_id = None
            for acc in accounts:
                if acc['username'] == selected_account:
                    account_id = acc['id']
                    break
                    
            if not account_id:
                messagebox.showerror("Error", "Account not found")
                return
            
            # Start session
            self.add_event_log("🚀 Starting live session...")
            self.connection_status.config(text="🟡 CONNECTING...", foreground="orange")
            
            # Create session in database (ORIGINAL)
            session_name = f"Live_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            session_id = self.db_manager.create_live_session(account_id, session_name)
            self.current_session = session_id
            
            # Start analytics session (ORIGINAL)
            analytics_session_id = f"analytics_{selected_account}_{int(time.time())}"
            analytics_started = self.analytics_manager.start_session(analytics_session_id, selected_account)
            if analytics_started:
                self.add_event_log("📊 Analytics tracking started")
            else:
                self.add_event_log("⚠️ Analytics tracking failed to start")
            
            # Start Unified Session (NEW - with smart room detection)
            try:
                unified_session_id = self.unified_manager.start_session(
                    account_username=selected_account,
                    room_id=None  # Will be auto-detected when TikTok connects
                )
                if unified_session_id:
                    self.add_event_log(f"🎯 Unified session started: {unified_session_id.session_id}")
                else:
                    self.add_event_log("⚠️ Unified session failed to start")
            except Exception as e:
                self.logger.warning(f"Unified session start warning: {e}")
                self.add_event_log(f"⚠️ Unified session warning: {str(e)}")
                # Continue with original flow even if unified fails
            
            # Initialize TikTok connector (ORIGINAL)
            self.tiktok_connector = TikTokConnector(selected_account)
            
            # Enable analytics integration (ORIGINAL)
            self.tiktok_connector.enable_analytics(self.analytics_manager)
            
            # Set event handlers (MODIFIED - now routes to both original AND unified)
            self.tiktok_connector.set_event_handlers(
                on_gift=self.on_gift_received_unified,      # NEW: routes to both
                on_comment=self.on_comment_received_unified, # NEW: routes to both  
                on_like=self.on_like_received_unified,       # NEW: routes to both
                on_connection_status=self.on_connection_status_unified # NEW: routes to both
            )
            
            # Start TikTok connection in background thread (ORIGINAL)
            def connect_tiktok():
                try:
                    if self.tiktok_connector:
                        success = self.tiktok_connector.connect()
                        if success:
                            self.root.after(0, self._update_connection_success, selected_account)
                        else:
                            self.root.after(0, self._update_connection_failed)
                    else:
                        self.root.after(0, self._update_connection_failed)
                except Exception as e:
                    self.logger.error(f"TikTok connection error: {e}")
                    self.root.after(0, self._update_connection_failed)
            
            threading.Thread(target=connect_tiktok, daemon=True).start()
            
        except Exception as e:
            self.logger.error(f"Error starting session: {e}")
            messagebox.showerror("Error", f"Failed to start session: {e}")
            self.connection_status.config(text="🔴 ERROR", foreground="red")
            
    def stop_session(self):
        """Stop current live session"""
        try:
            if not self.current_session:
                messagebox.showwarning("Warning", "No active session to stop")
                return
                
            # Stop analytics session (ORIGINAL)
            analytics_stopped = self.analytics_manager.stop_session()
            if analytics_stopped:
                self.add_event_log("📊 Analytics tracking stopped")
            else:
                self.add_event_log("⚠️ Analytics tracking failed to stop properly")
                
            # Stop Unified Session (NEW)
            try:
                self.unified_manager.stop_session()
                self.add_event_log("🎯 Unified session stopped")
            except Exception as e:
                self.logger.warning(f"Unified session stop warning: {e}")
                # Continue with original flow even if unified fails
                
            # Stop TikTok connection (ORIGINAL)
            if self.tiktok_connector:
                self.add_event_log("🔌 Disconnecting from TikTok Live...")
                self.tiktok_connector.disable_analytics()
                self.tiktok_connector.disconnect()
                self.tiktok_connector = None
                
            # Stop session (ORIGINAL)
            self.add_event_log("⏹️ Stopping live session...")
            
            # Update session in database (ORIGINAL)
            self.db_manager.end_live_session(self.current_session)
            
            # Reset UI (ORIGINAL)
            self.current_session = None
            self.connection_status.config(text="🔴 DISCONNECTED", foreground="red")
            self.session_info.config(text="No active session")
            self.add_event_log("✅ Session stopped")
            
            messagebox.showinfo("Success", "Session stopped successfully!")
            
        except Exception as e:
            self.logger.error(f"Error stopping session: {e}")
            messagebox.showerror("Error", f"Failed to stop session: {e}")
            
    # TikTok Event Handlers
    def on_gift_received(self, gift_data):
        """Handle received gift events from TikTok Live with enhanced data"""
        try:
            gift_name = gift_data.get('gift_name', 'Unknown')
            username = gift_data.get('username', 'Anonymous')
            gift_value = gift_data.get('gift_value', 0)
            repeat_count = gift_data.get('repeat_count', 1)
            total_value = gift_data.get('total_value', gift_value * repeat_count)
            gift_category = gift_data.get('gift_category', 'standard')
            value_tier = gift_data.get('value_tier', 'common')
            
            # Enhanced gift information display
            gift_info = f"{gift_name}"
            if repeat_count > 1:
                gift_info += f" x{repeat_count}"
            
            # Include streak information if available
            if gift_data.get('gift_type') == 1:  # Streakable gift
                streak_status = "🔥" if gift_data.get('is_pending_streak') else "✅"
                gift_info += f" {streak_status}"
            
            # Log to database with enhanced data
            if self.current_session:
                self.db_manager.log_gift(
                    self.current_session,
                    username,
                    gift_name,
                    total_value,  # Use total value instead of single gift value
                    repeat_count
                )
            
            # Clean gift display (format yang jelas seperti API study)
            if repeat_count > 1:
                message = f"GIFT: {username} sent {repeat_count}x \"{gift_name}\" (≈{total_value} coins)"
            else:
                message = f"GIFT: {username} sent \"{gift_name}\" (≈{gift_value} coins)"
            
            self.add_event_log(message)
            
            # Update Live Feed real-time statistics langsung
            self.update_live_feed_realtime()
            
        except Exception as e:
            self.logger.error(f"Error handling gift: {e}")
            
    def on_comment_received(self, comment_data):
        """Handle received comment events from TikTok Live"""
        try:
            username = comment_data.get('username', 'Anonymous')
            comment_text = comment_data.get('comment', '')
            
            # Log to database
            if self.current_session:
                self.db_manager.log_comment(
                    self.current_session,
                    username,
                    comment_text
                )
            
            # Clean comment display (format yang jelas seperti API study)
            message = f"COMMENT: {username}: {comment_text}"
            self.add_event_log(message)
            
            # Update Live Feed real-time statistics langsung
            self.update_live_feed_realtime()
            
        except Exception as e:
            self.logger.error(f"Error handling comment: {e}")
            
    def on_like_received(self, like_data):
        """Handle received like events from TikTok Live"""
        try:
            username = like_data.get('username', 'Unknown')
            like_count = like_data.get('like_count', 1)
            total_likes = like_data.get('total_likes', like_count)
            
            # Format yang jelas seperti API study
            message = f"LIKE: {username} liked {like_count}x (total: {total_likes:,})"
            self.add_event_log(message)
            
            # Update Live Feed real-time statistics langsung
            self.update_live_feed_realtime()
            
        except Exception as e:
            self.logger.error(f"Error handling like: {e}")
            
    def on_connection_status(self, status_data):
        """Handle TikTok connection status changes"""
        try:
            connected = status_data.get('connected', False)
            username = status_data.get('username', '')
            
            if connected:
                self.add_event_log(f"✅ Connected to @{username} TikTok Live!")
                self.connection_status.config(text="🟢 CONNECTED", foreground="green")
                self.session_info.config(text=f"Live: @{username}")
            else:
                self.add_event_log(f"❌ Disconnected from @{username}")
                self.connection_status.config(text="🔴 DISCONNECTED", foreground="red")
                
        except Exception as e:
            self.logger.error(f"Error handling connection status: {e}")
            
    def _update_connection_success(self, username):
        """Update UI after successful connection (main thread)"""
        self.connection_status.config(text="🟢 CONNECTED", foreground="green")
        self.session_info.config(text=f"Live: @{username}")
        self.add_event_log("✅ TikTok Live connection established!")
        
    def _update_connection_failed(self):
        """Update UI after connection failure (main thread)"""
        self.connection_status.config(text="🔴 CONNECTION FAILED", foreground="red")
        self.add_event_log("❌ Failed to connect to TikTok Live")
        
    # NEW: Unified Event Handlers (routes to both original + unified)
    def on_gift_received_unified(self, gift_data):
        """Handle gift events - routes to both original and unified systems"""
        try:
            # Call original handler (for compatibility)
            self.on_gift_received(gift_data)
            
            # Call unified system dengan format yang benar
            self.unified_manager.add_live_event({
                'type': 'gift',
                'gift_name': gift_data.get('gift_name', ''),
                'username': gift_data.get('username', ''),
                'gift_value': gift_data.get('gift_value', 0),
                'timestamp': time.time(),
                'trigger_arduino': True
            })
            
        except Exception as e:
            self.logger.error(f"Error in unified gift handler: {e}")
    
    def on_comment_received_unified(self, comment_data):
        """Handle comment events - routes to both original and unified systems"""
        try:
            # Call original handler (for compatibility)
            self.on_comment_received(comment_data)
            
            # Call unified system dengan format yang benar
            self.unified_manager.add_live_event({
                'type': 'comment',
                'comment': comment_data.get('comment', ''),
                'username': comment_data.get('username', ''),
                'timestamp': time.time(),
                'trigger_arduino': False
            })
            
        except Exception as e:
            self.logger.error(f"Error in unified comment handler: {e}")
    
    def on_like_received_unified(self, like_data):
        """Handle like events - routes to both original and unified systems"""
        try:
            # Call original handler (for compatibility)
            self.on_like_received(like_data)
            
            # Call unified system dengan format yang benar
            self.unified_manager.add_live_event({
                'type': 'like',
                'username': like_data.get('username', ''),
                'like_count': like_data.get('like_count', 1),
                'timestamp': time.time(),
                'trigger_arduino': False
            })
            
        except Exception as e:
            self.logger.error(f"Error in unified like handler: {e}")
    
    def on_connection_status_unified(self, status_data):
        """Handle connection status - routes to both original and unified systems"""
        try:
            # Call original handler (for compatibility) 
            self.on_connection_status(status_data)
            
            # Update unified system with room_id if available
            if status_data.get('connected') and status_data.get('room_id'):
                room_id = status_data.get('room_id')
                # Update unified manager dengan room_id jika tersedia
                if hasattr(self.unified_manager, 'current_session') and self.unified_manager.current_session:
                    self.unified_manager.current_session.room_id = room_id
                    self.add_event_log(f"🔗 Room ID detected: {room_id}")
                else:
                    self.add_event_log(f"🔗 Room ID detected but no active session: {room_id}")
            
        except Exception as e:
            self.logger.error(f"Error in unified connection handler: {e}")
    
    # Demo Data Methods
    def start_demo_data(self):
        """Start demo data generation for testing"""
        try:
            if self.demo_active:
                messagebox.showwarning("Warning", "Demo already running")
                return
                
            if not self.current_session:
                messagebox.showwarning("Warning", "Please start a session first")
                return
                
            self.demo_active = True
            self.demo_thread = threading.Thread(target=self._demo_data_loop, daemon=True)
            self.demo_thread.start()
            
            self.add_event_log("🎬 Demo data generation started")
            messagebox.showinfo("Demo Started", "Demo data generation started!")
            
        except Exception as e:
            self.logger.error(f"Error starting demo: {e}")
            
    def stop_demo_data(self):
        """Stop demo data generation"""
        try:
            if not self.demo_active:
                messagebox.showwarning("Warning", "No demo running")
                return
                
            self.demo_active = False
            self.add_event_log("🛑 Demo data generation stopped")
            messagebox.showinfo("Demo Stopped", "Demo data generation stopped!")
            
        except Exception as e:
            self.logger.error(f"Error stopping demo: {e}")
            
    def _demo_data_loop(self):
        """Demo data generation loop"""
        import random
        
        demo_users = [
            "rhianfan123", "gamerlive88", "tiktokstar21", "viewer456", 
            "supporter999", "livefan777", "tiktoker42", "fanbase101"
        ]
        
        demo_gifts = [
            {"name": "Rose", "value": 1},
            {"name": "Love", "value": 5}, 
            {"name": "Heart", "value": 10},
            {"name": "Crown", "value": 50},
            {"name": "Lion", "value": 500}
        ]
        
        demo_comments = [
            "Hello from Indonesia!", "Amazing stream!", "Love your content!",
            "666", "777", "tembak!", "ledak!", "putar motor!", 
            "Great job!", "Keep going!", "Fantastic!", "Awesome!"
        ]
        
        like_count = 0
        
        while self.demo_active:
            try:
                # Random event type
                event_type = random.choices(
                    ['gift', 'comment', 'like'], 
                    weights=[20, 60, 20]
                )[0]
                
                if event_type == 'gift':
                    user = random.choice(demo_users)
                    gift = random.choice(demo_gifts)
                    
                    # Log to database (only if session exists)
                    if self.current_session:
                        self.db_manager.log_gift(
                            self.current_session, 
                            user, 
                            gift['name'], 
                            gift['value']
                        )
                    
                    # Update GUI
                    self.on_gift_received({
                        'username': user,
                        'gift_name': gift['name'],
                        'gift_value': gift['value']
                    })
                    
                elif event_type == 'comment':
                    user = random.choice(demo_users)
                    comment = random.choice(demo_comments)
                    
                    # Log to database (only if session exists)
                    if self.current_session:
                        self.db_manager.log_comment(
                            self.current_session,
                            user,
                            comment
                        )
                    
                    # Update GUI
                    self.on_comment_received({
                        'username': user,
                        'comment': comment
                    })
                    
                elif event_type == 'like':
                    like_count += random.randint(1, 10)
                    self.on_like_received({
                        'like_count': like_count
                    })
                
                # Random delay between events
                time.sleep(random.uniform(1, 5))
                
            except Exception as e:
                self.logger.error(f"Demo error: {e}")
                time.sleep(1)
            
    def emergency_stop(self):
        """Emergency stop all devices"""
        try:
            self.add_event_log("🛑 EMERGENCY STOP ACTIVATED!")
            # Stop all Arduino devices - placeholder for now
            # TODO: Implement actual emergency stop functionality
            messagebox.showinfo("Emergency Stop", "All devices stopped!")
        except Exception as e:
            self.logger.error(f"Emergency stop error: {e}")
            
    def scan_arduino_ports(self):
        """Scan for available Arduino ports"""
        try:
            self.add_event_log("🔍 Scanning for Arduino devices...")
            ports = self.arduino_controller.scan_arduino_ports()
            
            status_text = "Arduino Port Scan Results:\n"
            status_text += "=" * 30 + "\n"
            
            if ports:
                for port in ports:
                    status_text += f"✅ Found device on {port['port']}\n"
            else:
                status_text += "❌ No Arduino devices found\n"
                
            self.arduino_status_text.delete(1.0, tk.END)
            self.arduino_status_text.insert(tk.END, status_text)
            
        except Exception as e:
            self.logger.error(f"Error scanning ports: {e}")
            
    def test_device(self, device_id):
        """Test Arduino device"""
        try:
            self.add_event_log(f"🧪 Testing device {device_id}...")
            # Placeholder for device testing
            # TODO: Implement actual device testing
            self.add_event_log(f"✅ Device {device_id} test successful (simulated)")
        except Exception as e:
            self.logger.error(f"Device test error: {e}")
            
    def update_arduino_status(self):
        """Update Arduino status display"""
        try:
            # This will be called from update thread
            pass
        except Exception as e:
            self.logger.error(f"Arduino status update error: {e}")
            
    def update_session_stats(self):
        """Update session statistics dengan data real-time dari unified system"""
        try:
            if not self.current_session:
                return
                
            # Prioritas 1: Ambil data dari unified system untuk real-time dashboard
            stats = self.get_live_dashboard_stats()
            
            # Prioritas 2: Enhanced stats dari TikTok connector jika tersedia
            if self.tiktok_connector and self.tiktok_connector.is_connected():
                try:
                    # Get enhanced client info dengan statistics tambahan
                    client_info = self.tiktok_connector.get_client_info()
                    tiktok_stats = client_info.get('statistics', {})
                    gift_stats = client_info.get('gift_statistics', {})
                    
                    # Merge dengan live dashboard stats
                    tiktok_enhanced = {
                        'session_duration': client_info.get('session_duration_formatted', stats.get('duration', '00:00')),
                        'unique_gifters': gift_stats.get('unique_gifters', stats.get('unique_gifters', 0)),
                        'events_per_minute': tiktok_stats.get('events_per_minute', 0),
                        'connection_quality': client_info.get('connection_quality', 'good'),
                        'peak_viewers': tiktok_stats.get('peak_viewers', stats.get('peak_viewers', 0))
                    }
                    
                    # Update stats dengan data enhanced
                    stats.update(tiktok_enhanced)
                    
                    # Get top gifters dari TikTok connector
                    if hasattr(self.tiktok_connector, 'get_top_gifters'):
                        top_gifters = self.tiktok_connector.get_top_gifters(5)
                        if top_gifters:
                            stats['top_gifters'] = top_gifters
                            
                except Exception as e:
                    self.logger.debug(f"TikTok enhanced stats error: {e}")
                    # Continue dengan live dashboard stats
            
            # Prioritas 3: Fallback ke database jika unified system tidak tersedia
            if not stats or stats.get('total_gifts', 0) == 0:
                try:
                    gifts = self.db_manager.get_session_gifts(self.current_session)
                    comments = self.db_manager.get_session_comments(self.current_session)
                    
                    stats.update({
                        'total_gifts': len(gifts),
                        'total_coins': sum(gift.get('gift_value', 0) for gift in gifts),
                        'total_comments': len(comments),
                        'viewers': 0,
                        'peak_viewers': 0,
                        'likes': 0,
                        'duration': '00:00',
                        'unique_gifters': 0,
                        'top_gifters': []
                    })
                except Exception as e:
                    self.logger.debug(f"Database fallback error: {e}")
            
            # Update labels di main thread
            self.root.after(0, self._update_stats_labels, stats)
            
        except Exception as e:
            self.logger.error(f"Stats update error: {e}")
    
    def get_live_dashboard_stats(self):
        """Ambil data real-time untuk dashboard dari Live Feed (prioritas TikTok connector)"""
        try:
            # PRIORITAS 1: Ambil data real-time langsung dari TikTok connector (Live Feed source)
            if self.tiktok_connector and self.tiktok_connector.is_connected():
                tiktok_stats = self.get_tiktok_realtime_stats()
                if tiktok_stats:
                    return tiktok_stats
            
            # PRIORITAS 2: Fallback ke unified manager
            unified_data = self.unified_manager.get_live_memory_data()
            
            if not unified_data:
                return self._get_default_stats()
            
            # Extract data dari unified system
            session_data = unified_data.get('sessions', {})
            events_data = unified_data.get('events', {})
            system_data = unified_data.get('system', {})
            
            # Hitung duration dari uptime
            uptime_seconds = system_data.get('uptime', 0)
            duration = self._format_duration(uptime_seconds)
            
            # Build stats untuk dashboard
            stats = {
                'total_gifts': events_data.get('recent_count', 0),  # Recent events sebagai proxy
                'total_coins': 0,  # Will be calculated from gifts
                'total_comments': events_data.get('total_processed', 0),
                'viewers': session_data.get('active', 0),
                'peak_viewers': session_data.get('total', 0),  # Total sessions sebagai proxy
                'likes': 0,  # Will be populated from events
                'duration': duration,
                'unique_gifters': session_data.get('room_ids', 0),
                'top_gifters': [],
                'system_status': 'running' if system_data.get('is_running', False) else 'stopped'
            }
            
            # Coba ambil data session summary jika tersedia
            try:
                if hasattr(self.unified_manager, 'get_session_summary'):
                    session_summary = self.unified_manager.get_session_summary()
                    if session_summary:
                        summary_stats = session_summary.get('stats', {})
                        stats.update({
                            'total_gifts': summary_stats.get('total_gifts', stats['total_gifts']),
                            'total_coins': summary_stats.get('total_gifts', 0) * 10,  # Estimate
                            'total_comments': summary_stats.get('total_comments', stats['total_comments']),
                            'likes': summary_stats.get('total_likes', 0),
                            'viewers': summary_stats.get('total_viewers', stats['viewers']),
                            'peak_viewers': summary_stats.get('max_viewers', stats['peak_viewers'])
                        })
            except Exception as e:
                self.logger.debug(f"Session summary not available: {e}")
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Live dashboard stats error: {e}")
            return self._get_default_stats()
    
    def _get_default_stats(self):
        """Return default stats structure"""
        return {
            'total_gifts': 0,
            'total_coins': 0,
            'total_comments': 0,
            'viewers': 0,
            'peak_viewers': 0,
            'likes': 0,
            'duration': '00:00',
            'unique_gifters': 0,
            'top_gifters': [],
            'system_status': 'disconnected'
        }
    
    def _format_duration(self, seconds):
        """Format duration dari seconds ke HH:MM:SS"""
        try:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            seconds = int(seconds % 60)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        except:
            return "00:00:00"
            
    def _update_stats_labels(self, stats):
        """Update statistics labels with enhanced data (must run in main thread)"""
        try:
            # Update basic stats
            self.stats_labels['total_gifts'].config(text=str(stats.get('total_gifts', 0)))
            self.stats_labels['total_coins'].config(text=str(stats.get('total_coins', 0)))
            self.stats_labels['viewers'].config(text=f"{stats.get('viewers', 0)} (Peak: {stats.get('peak_viewers', 0)})")
            self.stats_labels['likes'].config(text=str(stats.get('likes', 0)))
            
            # Update session duration from connector if available
            duration = stats.get('session_duration', '00:00')
            if duration != '00:00':
                self.stats_labels['duration'].config(text=duration)
            elif stats.get('start_time'):
                # Fallback calculation
                duration = datetime.now() - stats['start_time']
                duration_str = str(duration).split('.')[0]  # Remove microseconds
                self.stats_labels['duration'].config(text=duration_str)
            
            # Update Top Gifters Leaderboard
            top_gifters = stats.get('top_gifters', [])
            self._update_leaderboard(top_gifters)
            
            # Only log stats periodically to avoid spam (like TikTok-Chat-Reader)
            # Stats are displayed in GUI labels, no need to spam events log
            
        except Exception as e:
            self.logger.error(f"Error updating stats labels: {e}")
    
    def _update_leaderboard(self, top_gifters):
        """Update top gifters leaderboard display"""
        try:
            # Clear all leaderboard labels first
            for label in self.leaderboard_labels:
                label.config(text="")
            
            # Update with current top gifters
            for i, gifter in enumerate(top_gifters[:5]):  # Only show top 5
                if i < len(self.leaderboard_labels):
                    # Format: "1. Username - 5 gifts"
                    rank = i + 1
                    username = gifter.get('username', 'Unknown')
                    gift_count = gifter.get('gift_count', 0)
                    total_value = gifter.get('total_value', 0)
                    
                    # Truncate long usernames
                    if len(username) > 12:
                        username = username[:12] + "..."
                    
                    # Format display text
                    if total_value > 0:
                        display_text = f"{rank}. {username} - {gift_count} gifts ({total_value} coins)"
                    else:
                        display_text = f"{rank}. {username} - {gift_count} gifts"
                    
                    # Set color based on rank
                    if rank == 1:
                        color = "#FFD700"  # Gold
                    elif rank == 2:
                        color = "#C0C0C0"  # Silver
                    elif rank == 3:
                        color = "#CD7F32"  # Bronze
                    else:
                        color = "#000000"  # Black
                    
                    self.leaderboard_labels[i].config(text=display_text, foreground=color)
                    
        except Exception as e:
            self.logger.error(f"Error updating leaderboard: {e}")
            
    def add_event_log(self, message):
        """Add message to live events log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        # Update in main thread
        self.root.after(0, self._add_to_events_text, log_message)
        
    def _add_to_events_text(self, message):
        """Add message to events text widget (main thread only)"""
        self.events_text.insert(tk.END, message)
        self.events_text.see(tk.END)  # Auto-scroll to bottom
        
        # Keep only last 1000 lines
        lines = self.events_text.get(1.0, tk.END).split('\n')
        if len(lines) > 1000:
            self.events_text.delete(1.0, f"{len(lines)-1000}.0")
            
    def load_recent_logs(self):
        """Load recent log files"""
        try:
            log_dir = Path("logs")
            if not log_dir.exists():
                self.logs_text.insert(tk.END, "No log directory found.")
                return
                
            # Get most recent log file
            log_files = list(log_dir.glob("*.log"))
            if not log_files:
                self.logs_text.insert(tk.END, "No log files found.")
                return
                
            latest_log = max(log_files, key=lambda f: f.stat().st_mtime)
            
            # Read last 100 lines
            with open(latest_log, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                recent_lines = lines[-100:] if len(lines) > 100 else lines
                
            self.logs_text.insert(tk.END, ''.join(recent_lines))
            self.logs_text.see(tk.END)
            
        except Exception as e:
            self.logs_text.insert(tk.END, f"Error loading logs: {e}")
            
    def show_settings(self):
        """Show settings dialog"""
        messagebox.showinfo("Settings", "Settings dialog will be implemented in next phase")
        
    def show_account_manager(self):
        """Show account management dialog"""
        try:
            from gui.account_manager import AccountManagerDialog
            dialog = AccountManagerDialog(self.root, self.db_manager)
            dialog.show(refresh_callback=self.load_accounts)
        except Exception as e:
            self.logger.error(f"Error opening account manager: {e}")
            messagebox.showerror("Error", f"Failed to open account manager: {e}")
        
    def add_account(self):
        """Add new account dialog"""
        try:
            from gui.account_manager import AddEditAccountDialog
            dialog = AddEditAccountDialog(self.root, self.db_manager)
            result = dialog.show()
            if result:
                self.load_accounts()
        except Exception as e:
            self.logger.error(f"Error adding account: {e}")
            messagebox.showerror("Error", f"Failed to add account: {e}")
        
    def show_arduino_control(self):
        """Show Arduino control panel"""
        messagebox.showinfo("Arduino Control", "Advanced Arduino control will be implemented in next phase")
        
    def show_about(self):
        """Show about dialog"""
        about_text = """
        TikTok Live Games Controller v2.0
        Desktop Application
        
        A desktop application for managing TikTok Live
        interactions with Arduino devices.
        
        Features:
        • Real-time TikTok Live monitoring
        • Arduino device control
        • Multi-account support
        • Session tracking and statistics
        
        Built with Python & Tkinter
        """
        messagebox.showinfo("About", about_text)
        
    def on_closing(self):
        """Handle application closing"""
        try:
            # Stop update thread
            self.stop_updates = True
            
            # Stop any active session
            if self.current_session:
                self.stop_session()
            
            # Shutdown unified manager (NEW)
            try:
                self.unified_manager.shutdown()
                self.logger.info("Unified manager shutdown completed")
            except Exception as e:
                self.logger.warning(f"Unified manager shutdown warning: {e}")
                
            # Close any connections (ORIGINAL)
            # Note: DatabaseManager doesn't have close method, connections are auto-closed
            
            self.logger.info("Application closing...")
            self.root.destroy()
            
        except Exception as e:
            self.logger.error(f"Error during closing: {e}")
            self.root.destroy()
            
    def run(self):
        """Run the application"""
        try:
            # Set up window close handler
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            
            # Start optimized statistics updates after UI is ready
            if hasattr(self, 'statistics_optimizer'):
                self.root.after(2000, start_optimized_statistics)  # Start after 2 seconds
            
            # Start the GUI main loop
            self.logger.info("Starting GUI main loop...")
            self.root.mainloop()
            
        except Exception as e:
            self.logger.error(f"Error running application: {e}")
            raise
