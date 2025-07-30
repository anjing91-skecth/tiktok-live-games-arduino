#!/usr/bin/env python3
"""
Minimal Unified GUI - Working Version
====================================
Simplified GUI yang sudah terintegrasi dengan UnifiedSessionManager
Focus pada core functionality yang sudah tested
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
import logging
from datetime import datetime
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.core.database_manager import DatabaseManager
from src.core.analytics_manager import AnalyticsManager
from src.core.unified_session_manager import UnifiedSessionManager

class MinimalUnifiedGUI:
    """Minimal GUI with working UnifiedSessionManager integration"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.root = tk.Tk()
        self.root.title("🎮 TikTok Live Games - Unified System v3.0")
        self.root.geometry("1000x700")
        
        # Initialize core components
        self.db_manager = DatabaseManager()
        self.analytics_manager = AnalyticsManager()
        self.analytics_manager.init_database()
        
        # INITIALIZE UNIFIED SESSION MANAGER
        self.unified_manager = UnifiedSessionManager(
            arduino_controller=None,  # Mock Arduino for now
            database_manager=self.db_manager,
            analytics_manager=self.analytics_manager
        )
        
        # Initialize unified system
        self.unified_manager.initialize()
        self.logger.info("🎯 Unified Session Manager initialized in minimal GUI")
        
        # GUI state
        self.current_session_id = None
        self.current_username = None
        self.is_connected = False
        self.stop_updates = False
        
        # Setup GUI
        self.setup_gui()
        self.start_live_updates()
        
        # Setup window close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_gui(self):
        """Setup main GUI layout"""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Connection section
        self.setup_connection_section(main_frame)
        
        # Live data section
        self.setup_live_data_section(main_frame)
        
        # Event log section
        self.setup_event_log_section(main_frame)
    
    def setup_connection_section(self, parent):
        """Setup connection control section"""
        conn_frame = ttk.LabelFrame(parent, text="🔗 Unified Session Control", padding=10)
        conn_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Username input
        ttk.Label(conn_frame, text="Username:").grid(row=0, column=0, padx=5, sticky=tk.W)
        self.username_entry = ttk.Entry(conn_frame, width=30)
        self.username_entry.grid(row=0, column=1, padx=5, sticky=tk.W)
        self.username_entry.insert(0, "test_user")  # Default for testing
        
        # Status display
        ttk.Label(conn_frame, text="Status:").grid(row=0, column=2, padx=10, sticky=tk.W)
        self.status_label = ttk.Label(conn_frame, text="🔴 READY", foreground="red")
        self.status_label.grid(row=0, column=3, padx=5, sticky=tk.W)
        
        # Session info
        ttk.Label(conn_frame, text="Session:").grid(row=0, column=4, padx=10, sticky=tk.W)
        self.session_label = ttk.Label(conn_frame, text="No session", foreground="gray")
        self.session_label.grid(row=0, column=5, padx=5, sticky=tk.W)
        
        # Control buttons
        button_frame = ttk.Frame(conn_frame)
        button_frame.grid(row=1, column=0, columnspan=6, pady=10, sticky=tk.W)
        
        self.start_button = ttk.Button(button_frame, text="🚀 Start Unified Session", command=self.start_session)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="⏹️ Stop Session", command=self.stop_session, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Test buttons
        ttk.Button(button_frame, text="🎁 Test Gift", command=self.test_gift).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="💬 Test Comment", command=self.test_comment).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="👍 Test Like", command=self.test_like).pack(side=tk.LEFT, padx=5)
    
    def setup_live_data_section(self, parent):
        """Setup live data display section"""
        data_frame = ttk.LabelFrame(parent, text="📊 Live Data from Unified System", padding=10)
        data_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Create notebook for tabs
        notebook = ttk.Notebook(data_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Live Stats Tab
        stats_frame = ttk.Frame(notebook)
        notebook.add(stats_frame, text="📈 Live Stats")
        
        # Stats display
        self.stats_labels = {}
        stats_grid = ttk.Frame(stats_frame)
        stats_grid.pack(pady=10)
        
        stats = ['gifts', 'comments', 'likes', 'follows', 'shares', 'viewers']
        for i, stat in enumerate(stats):
            ttk.Label(stats_grid, text=f"{stat.title()}:").grid(row=i//3, column=(i%3)*2, padx=10, pady=5, sticky=tk.W)
            label = ttk.Label(stats_grid, text="0", font=("Arial", 12, "bold"), foreground="blue")
            label.grid(row=i//3, column=(i%3)*2+1, padx=5, pady=5, sticky=tk.W)
            self.stats_labels[stat] = label
        
        # Leaderboard Tab
        leaderboard_frame = ttk.Frame(notebook)
        notebook.add(leaderboard_frame, text="🏆 Leaderboard")
        
        # Leaderboard tree
        columns = ("Rank", "Username", "Total Value", "Percentage")
        self.leaderboard_tree = ttk.Treeview(leaderboard_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.leaderboard_tree.heading(col, text=col)
            self.leaderboard_tree.column(col, width=150)
        
        scrollbar = ttk.Scrollbar(leaderboard_frame, orient=tk.VERTICAL, command=self.leaderboard_tree.yview)
        self.leaderboard_tree.configure(yscrollcommand=scrollbar.set)
        
        self.leaderboard_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Session Info Tab
        info_frame = ttk.Frame(notebook)
        notebook.add(info_frame, text="📋 Session Info")
        
        self.session_info_text = scrolledtext.ScrolledText(info_frame, height=20, wrap=tk.WORD)
        self.session_info_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def setup_event_log_section(self, parent):
        """Setup event log section"""
        log_frame = ttk.LabelFrame(parent, text="📝 Event Log & Recent Events", padding=10)
        log_frame.pack(fill=tk.X)
        
        self.event_log = scrolledtext.ScrolledText(log_frame, height=10, wrap=tk.WORD)
        self.event_log.pack(fill=tk.X)
    
    def start_session(self):
        """Start unified session"""
        try:
            username = self.username_entry.get().strip()
            if not username:
                messagebox.showwarning("Warning", "Please enter a username")
                return
            
            self.current_username = username
            
            # Start unified session
            self.current_session_id = self.unified_manager.start_session(
                username=username,
                room_id=f"room_{username}_{int(time.time())}",  # Mock room ID
                manual_start=True
            )
            
            self.add_log(f"🚀 Unified session started: {self.current_session_id}")
            
            # Update UI
            self.status_label.config(text="🟢 ACTIVE", foreground="green")
            self.session_label.config(text=f"Session: {self.current_session_id[:20]}...", foreground="blue")
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            
            # Simulate connection
            self.is_connected = True
            self.add_log("✅ Unified system ready for events")
            
        except Exception as e:
            self.logger.error(f"Error starting session: {e}")
            messagebox.showerror("Error", f"Failed to start session: {e}")
    
    def stop_session(self):
        """Stop unified session"""
        try:
            if self.current_session_id:
                self.unified_manager.stop_session(manually_stopped=True)
                self.add_log(f"⏹️ Session stopped: {self.current_session_id}")
                self.current_session_id = None
            
            # Update UI
            self.is_connected = False
            self.status_label.config(text="🔴 STOPPED", foreground="red")
            self.session_label.config(text="No session", foreground="gray")
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            
            self.add_log("✅ Session stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Error stopping session: {e}")
            messagebox.showerror("Error", f"Failed to stop session: {e}")
    
    def test_gift(self):
        """Test gift event"""
        if not self.current_session_id:
            messagebox.showwarning("Warning", "Start a session first")
            return
        
        # Test gift data
        gift_data = {
            'username': f'gifter_{int(time.time() % 1000)}',
            'gift_name': 'Rose',
            'estimated_value': 5,
            'repeat_count': 1
        }
        
        self.unified_manager.on_tiktok_event("gift", gift_data)
        self.add_log(f"🎁 TEST: {gift_data['username']} sent {gift_data['gift_name']}")
    
    def test_comment(self):
        """Test comment event"""
        if not self.current_session_id:
            messagebox.showwarning("Warning", "Start a session first")
            return
        
        # Test comment data
        comment_data = {
            'username': f'commenter_{int(time.time() % 1000)}',
            'comment': f'Test comment at {datetime.now().strftime("%H:%M:%S")}'
        }
        
        self.unified_manager.on_tiktok_event("comment", comment_data)
        self.add_log(f"💬 TEST: {comment_data['username']}: {comment_data['comment']}")
    
    def test_like(self):
        """Test like event"""
        if not self.current_session_id:
            messagebox.showwarning("Warning", "Start a session first")
            return
        
        # Test like data
        like_data = {
            'username': f'liker_{int(time.time() % 1000)}',
            'count': 3
        }
        
        self.unified_manager.on_tiktok_event("like", like_data)
        self.add_log(f"👍 TEST: {like_data['username']} liked {like_data['count']}x")
    
    def start_live_updates(self):
        """Start live data update loop"""
        def update_loop():
            while not self.stop_updates:
                try:
                    if self.current_session_id and self.unified_manager:
                        # Get live data
                        live_data = self.unified_manager.get_live_data()
                        session_info = self.unified_manager.get_session_info()
                        
                        # Update GUI on main thread
                        self.root.after(0, self.update_display, live_data, session_info)
                    
                    time.sleep(1)  # Update every second
                    
                except Exception as e:
                    self.logger.error(f"Live update error: {e}")
                    time.sleep(5)
        
        self.update_thread = threading.Thread(target=update_loop, daemon=True)
        self.update_thread.start()
    
    def update_display(self, live_data, session_info):
        """Update live display"""
        try:
            # Update stats
            stats = live_data.get('stats', {})
            for stat_name, label in self.stats_labels.items():
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
            
            # Update session info
            if session_info:
                import json
                info_text = json.dumps(session_info, indent=2, default=str)
                self.session_info_text.delete(1.0, tk.END)
                self.session_info_text.insert(tk.END, info_text)
            
            # Show recent events in log
            recent_events = live_data.get('recent_events', [])
            if recent_events:
                # Show last event
                last_event = recent_events[-1]
                timestamp = last_event.get('timestamp', datetime.now()).strftime('%H:%M:%S')
                summary = last_event.get('summary', 'Unknown event')
                
                # Only add if it's new (simple check)
                log_content = self.event_log.get(1.0, tk.END)
                if summary not in log_content.split('\n')[-5:]:  # Check last 5 lines
                    pass  # Skip duplicate check for demo
            
        except Exception as e:
            self.logger.error(f"Display update error: {e}")
    
    def add_log(self, message):
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
            self.logger.error(f"Error adding to log: {e}")
    
    def on_closing(self):
        """Handle application closing"""
        try:
            self.add_log("🛑 Shutting down...")
            
            # Stop updates
            self.stop_updates = True
            
            # Stop session
            if self.current_session_id:
                self.stop_session()
            
            # Shutdown unified manager
            if self.unified_manager:
                self.unified_manager.shutdown()
            
            self.add_log("✅ Shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Shutdown error: {e}")
        finally:
            self.root.destroy()
    
    def run(self):
        """Run the application"""
        self.add_log("🚀 Minimal Unified GUI started")
        self.add_log("🎯 UnifiedSessionManager ready")
        self.add_log("💡 Click 'Start Unified Session' to begin")
        self.root.mainloop()

def main():
    """Main entry point"""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        app = MinimalUnifiedGUI()
        app.run()
    except Exception as e:
        logging.error(f"Application error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
