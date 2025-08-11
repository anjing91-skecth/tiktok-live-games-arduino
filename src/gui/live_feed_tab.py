"""
Live Feed Tab - Modular Version
===============================

Refactored version using modular components while maintaining
exact same UI functionality and user experience.

Enhanced features:
- Advanced TikTok Live event handling
- Comprehensive event statistics
- Real-time event log with detailed information
- Enhanced viewer tracking with peak statistics
- Gift value tracking with USD conversion

Integration with TikTokTrackerOptimized for robust event processing
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from src.tracker.tiktok_tracker_optimized import TikTokTrackerOptimized

# Import modular components
from live_feed_components import LiveFeedEventHandlers, LiveFeedTracker


class LiveFeedTab:
    """Optimized Live Feed Tab with essential features and improved performance"""
    
    def __init__(self, parent_notebook, tab_name: str = "Live Feed"):
        self.parent_notebook = parent_notebook
        self.tab_name = tab_name
        self.logger = logging.getLogger(__name__)
        
        # Current tracking - now delegated to tracker component
        self.current_username = ""
        self.current_account = {'username': 'demo', 'arduino_port': 'N/A', 'id': 0}
        
        # Create tab frame
        self.frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.frame, text=f"📺 {tab_name}")
        
        # Widgets dictionary for easy access
        self.widgets = {}
        
        # Create UI
        self._create_widgets()
        
        # Statistics tracking (enhanced from main program)
        self.statistics = {
            'viewers': 0,
            'comments': 0,
            'likes': 0,
            'followers': 0,
            'shares': 0,
            'coins': 0,
            'gifts': 0,
            'peak_viewers': 0
        }
        
        # Leaderboard data storage
        self.leaderboard_data = []
        
        # Initialize modular components
        self.event_handlers = LiveFeedEventHandlers(self.statistics, self.widgets, self.logger)
        self.tracker = LiveFeedTracker(self.widgets, self.statistics, self.logger)
        
        # Set up component callbacks
        self.event_handlers.set_callbacks(
            self.add_event_log,
            self.update_statistic, 
            self._update_leaderboard,
            self.stop_tracking
        )
        
        self.tracker.set_callbacks(
            self.add_event_log,
            self.event_handlers
        )
    
    def get_frame(self):
        """Get the main frame"""
        return self.frame
    
    # ===========================================
    # PROPERTY DELEGATION FOR ARDUINO INTEGRATION
    # ===========================================
    
    @property
    def current_tracker(self):
        """Expose current tracker for Arduino tab integration"""
        return self.tracker.current_tracker if self.tracker else None
    
    def _create_widgets(self):
        """Create enhanced UI based on main program structure"""
        # Create main paned window for better layout
        paned = ttk.PanedWindow(self.frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Event log (2/3 width)
        left_frame = ttk.LabelFrame(paned, text="🔴 Real-time Events")
        paned.add(left_frame, weight=2)
        
        log_container = ttk.Frame(left_frame)
        log_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Event log text area with scrollbar
        self.widgets['event_log'] = tk.Text(log_container, height=15, state=tk.DISABLED, 
                                           wrap=tk.WORD, font=("Consolas", 10))
        scrollbar_log = ttk.Scrollbar(log_container, orient=tk.VERTICAL, 
                                     command=self.widgets['event_log'].yview)
        self.widgets['event_log'].configure(yscrollcommand=scrollbar_log.set)
        
        self.widgets['event_log'].pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_log.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Log controls
        controls_frame = ttk.Frame(left_frame)
        controls_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(controls_frame, text="Clear Log", 
                  command=self.clear_event_log).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(controls_frame, text="Export Log", 
                  command=self.export_event_log).pack(side=tk.LEFT)
        
        # Right panel - Statistics and info (1/3 width)
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=1)
        
        # Account info section
        info_frame = ttk.LabelFrame(right_frame, text="📱 Account Info")
        info_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        info_container = ttk.Frame(info_frame)
        info_container.pack(fill=tk.X, padx=15, pady=15)
        
        ttk.Label(info_container, text="Username:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        self.widgets['username_label'] = ttk.Label(info_container, text=f"@{self.current_account['username']}", 
                 font=('Arial', 10))
        self.widgets['username_label'].pack(anchor=tk.W, pady=(0, 10))
        
        ttk.Label(info_container, text="Status:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        self.widgets['status_label'] = ttk.Label(info_container, text="🔴 Not Tracking", font=('Arial', 10))
        self.widgets['status_label'].pack(anchor=tk.W)
        
        # Session Statistics
        stats_frame = ttk.LabelFrame(right_frame, text="📊 Session Statistics")
        stats_frame.pack(fill=tk.X, padx=10, pady=5)
        
        stats_container = ttk.Frame(stats_frame)
        stats_container.pack(fill=tk.X, padx=10, pady=10)
        
        # Create statistics labels (enhanced from main program)
        self.widgets['stats_labels'] = {}
        stats_items = [
            ("👥 Viewers:", "viewers", "0"),
            ("💎 Total Coins:", "coins", "0"),
            ("💬 Comments:", "comments", "0"),
            ("❤️ Likes:", "likes", "0"),
            ("👥 Follows:", "followers", "0"),
            ("📤 Shares:", "shares", "0")
        ]
        
        for i, (label, key, default) in enumerate(stats_items):
            row = i // 2
            col = i % 2
            
            ttk.Label(stats_container, text=label).grid(row=row, column=col*2, 
                                                       sticky="w", padx=(0, 5), pady=2)
            
            self.widgets['stats_labels'][key] = ttk.Label(stats_container, 
                                                         text=default, 
                                                         font=("Arial", 10, "bold"))
            self.widgets['stats_labels'][key].grid(row=row, column=col*2+1, sticky="w", 
                                                  padx=(0, 20), pady=2)
        
        # Control buttons
        control_frame = ttk.Frame(right_frame)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Start/Stop tracking button (now always enabled if account selected)
        self.widgets['track_button'] = ttk.Button(control_frame, 
                                                 text="🔴 Start Tracking",
                                                 command=self.toggle_tracking,
                                                 state=tk.NORMAL)
        self.widgets['track_button'].pack(fill=tk.X, pady=2)
        
        # Top Gifters Leaderboard (enhanced from main program)
        leaderboard_frame = ttk.LabelFrame(right_frame, text="🏆 Top Gifters")
        leaderboard_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 10))
        
        # Leaderboard tree
        columns = ("Rank", "Username", "Coins", "Gifts")
        self.widgets['leaderboard_tree'] = ttk.Treeview(leaderboard_frame, columns=columns, 
                                                       show="headings", height=6)
        
        # Configure columns
        self.widgets['leaderboard_tree'].heading("Rank", text="#")
        self.widgets['leaderboard_tree'].heading("Username", text="Username")
        self.widgets['leaderboard_tree'].heading("Coins", text="💎 Coins")
        self.widgets['leaderboard_tree'].heading("Gifts", text="🎁 Gifts")
        
        self.widgets['leaderboard_tree'].column("Rank", width=30)
        self.widgets['leaderboard_tree'].column("Username", width=80)
        self.widgets['leaderboard_tree'].column("Coins", width=60)
        self.widgets['leaderboard_tree'].column("Gifts", width=40)
        
        scrollbar_leader = ttk.Scrollbar(leaderboard_frame, orient=tk.VERTICAL,
                                        command=self.widgets['leaderboard_tree'].yview)
        self.widgets['leaderboard_tree'].configure(yscrollcommand=scrollbar_leader.set)
        
        self.widgets['leaderboard_tree'].pack(side=tk.LEFT, fill=tk.BOTH, expand=True, 
                                             padx=(5, 0), pady=5)
        scrollbar_leader.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 5), pady=5)
    
    def set_selected_account(self, username: str):
        """Set selected account for tracking using modular tracker"""
        self.current_username = username
        self.tracker.set_current_username(username)
        
        # Update current account info
        self.current_account['username'] = username
        
        # Update username label in Account Info
        if 'username_label' in self.widgets:
            self.widgets['username_label'].config(text=f"@{username}")
    
    def toggle_tracking(self):
        """Start or stop tracking using modular tracker"""
        self.tracker.toggle_tracking()
    
    def start_tracking(self):
        """Start TikTok Live tracking using modular tracker"""
        self.tracker.start_tracking()
    
    def stop_tracking(self):
        """Stop TikTok Live tracking using modular tracker"""
        self.tracker.stop_tracking()
    
    def _reset_statistics(self):
        """Reset all statistics to zero"""
        for stat in self.statistics:
            self.statistics[stat] = 0
            if stat in self.widgets.get('stats_labels', {}):
                self.widgets['stats_labels'][stat].config(text="0")
    
    def add_event_log(self, message: str):
        """Add message to event log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        event_log = self.widgets['event_log']
        event_log.config(state=tk.NORMAL)
        event_log.insert(tk.END, log_message)
        event_log.see(tk.END)
        event_log.config(state=tk.DISABLED)
    
    def update_statistic(self, stat_name: str, value: int):
        """Update a specific statistic"""
        if stat_name in self.statistics:
            self.statistics[stat_name] = value
            if stat_name in self.widgets['stats_labels']:
                self.widgets['stats_labels'][stat_name].config(text=str(value))
    
    # ===========================================
    # ENHANCED EVENT HANDLERS FOR TikTokLive API
    # ===========================================
    
    def on_connect(self, event):
        """Handle successful connection to TikTok Live"""
        # Update UI to connected state
        self.widgets['track_button'].config(text="🟢 Stop Tracking", state=tk.NORMAL)
        self.widgets['status_label'].config(text="🟢 Connected")
        
        # Extract room ID safely
        room_id = getattr(event, 'room_id', 'Unknown')
        unique_id = getattr(event, 'unique_id', self.current_username)
        
        self.add_event_log(f"🎭 Connected to @{unique_id} (Room: {room_id})")
    
    def on_disconnect(self, event):
        """Handle disconnection from TikTok Live"""
        # Update UI to disconnected state but keep stop button until fully stopped
        self.widgets['status_label'].config(text="🔴 Disconnected")
        self.add_event_log(f"📤 Disconnected from live stream")
        
        # Check if this is an intentional stop or connection lost
        if self.current_tracker and hasattr(self.current_tracker, 'is_running') and not self.current_tracker.is_running:
            # Intentional stop - reset button
            self.widgets['track_button'].config(text="🔴 Start Tracking", state=tk.NORMAL)
            self.widgets['status_label'].config(text="🔴 Not Tracking")
    
    def on_live_end(self, event):
        """Handle when live stream ends"""
        self.widgets['status_label'].config(text="🔚 Stream Ended")
        self.add_event_log(f"📺 Live stream has ended")
        # Auto stop tracking when stream ends
        self.stop_tracking()
    
    def on_comment(self, event):
        """Handle comment event with enhanced data"""
        try:
            username = event.user.unique_id if hasattr(event, 'user') and hasattr(event.user, 'unique_id') else 'Unknown'
            comment_text = event.comment if hasattr(event, 'comment') else event.content
            
            self.statistics['comments'] += 1
            self.update_statistic('comments', self.statistics['comments'])
            self.add_event_log(f"💬 {username}: {comment_text}")
            
        except Exception as e:
            self.logger.error(f"Error handling comment event: {e}")
            self.add_event_log(f"💬 Comment received (error in display)")
    
    def on_gift(self, event):
        """Handle gift event with diamond/coin display"""
        try:
            username = event.user.unique_id if hasattr(event, 'user') and hasattr(event.user, 'unique_id') else 'Unknown'
            gift_name = event.gift.name if hasattr(event, 'gift') and hasattr(event.gift, 'name') else 'Unknown Gift'
            repeat_count = getattr(event, 'repeat_count', 1)
            
            # Get diamond count (TikTok's virtual currency)
            diamond_count = 0
            if hasattr(event, 'gift') and hasattr(event.gift, 'diamond_count'):
                diamond_count = event.gift.diamond_count * repeat_count
                
                # Update statistics
                self.statistics['gifts'] += repeat_count
                self.statistics['coins'] += diamond_count  # Use diamonds as coins
                self.update_statistic('gifts', self.statistics['gifts'])
                self.update_statistic('coins', self.statistics['coins'])
                
                # Add to leaderboard
                self._update_leaderboard(username, diamond_count, repeat_count)
                
                # Display with diamond count
                self.add_event_log(f"🎁 {username} sent {repeat_count}x {gift_name} ({diamond_count} diamonds)")
                
            else:
                # Fallback without diamond count
                self.statistics['gifts'] += repeat_count
                self.update_statistic('gifts', self.statistics['gifts'])
                
                self.add_event_log(f"🎁 {username} sent {repeat_count}x {gift_name}")
            
        except Exception as e:
            self.logger.error(f"Error handling gift event: {e}")
            self.add_event_log(f"🎁 Gift received (error in display)")
    
    def on_like(self, event):
        """Handle like event with enhanced data"""
        try:
            username = event.user.unique_id if hasattr(event, 'user') and hasattr(event.user, 'unique_id') else 'Unknown'
            like_count = getattr(event, 'count', 1)
            
            self.statistics['likes'] += like_count
            self.update_statistic('likes', self.statistics['likes'])
            
            if like_count > 1:
                self.add_event_log(f"❤️ {username} liked! (+{like_count})")
            else:
                self.add_event_log(f"❤️ {username} liked!")
            
        except Exception as e:
            self.logger.error(f"Error handling like event: {e}")
            self.add_event_log(f"❤️ Like received")
    
    def on_follow(self, event):
        """Handle follow event with enhanced data"""
        try:
            username = event.user.unique_id if hasattr(event, 'user') and hasattr(event.user, 'unique_id') else 'Unknown'
            
            self.statistics['followers'] += 1
            self.update_statistic('followers', self.statistics['followers'])
            self.add_event_log(f"➕ {username} followed the stream!")
            
        except Exception as e:
            self.logger.error(f"Error handling follow event: {e}")
            self.add_event_log(f"➕ New follower!")
    
    def on_share(self, event):
        """Handle share event"""
        try:
            username = event.user.unique_id if hasattr(event, 'user') and hasattr(event.user, 'unique_id') else 'Unknown'
            
            self.statistics['shares'] += 1
            self.update_statistic('shares', self.statistics['shares'])
            self.add_event_log(f"📤 {username} shared the stream!")
            
        except Exception as e:
            self.logger.error(f"Error handling share event: {e}")
            self.add_event_log(f"📤 Stream shared!")
    
    def on_join(self, event):
        """Handle join event - don't display in GUI as requested"""
        try:
            # Don't add to event log as requested by user
            # username = event.user.unique_id if hasattr(event, 'user') and hasattr(event.user, 'unique_id') else 'Unknown'
            # self.add_event_log(f"👋 {username} joined the stream!")
            pass
            
        except Exception as e:
            self.logger.error(f"Error handling join event: {e}")
            self.add_event_log(f"� Someone joined the stream!")
    
    def on_viewer_update(self, event):
        """Handle viewer count update with enhanced anti-fluctuation"""
        try:
            # Use m_total field as confirmed from optimized tracker study
            viewer_count = getattr(event, 'm_total', 0)
            
            # Enhanced anti-fluctuation logic from main program
            current_viewers = self.statistics.get('viewers', 0)
            
            # Ignore sudden drops of more than 20%
            if viewer_count > 0 and current_viewers > 0:
                percentage_change = abs(viewer_count - current_viewers) / current_viewers
                if percentage_change > 0.2 and viewer_count < current_viewers:
                    self.add_event_log(f"⚠️ Viewer fluctuation ignored: {viewer_count} (was {current_viewers})")
                    return
            
            self.statistics['viewers'] = viewer_count
            self.update_statistic('viewers', viewer_count)
            # Don't log viewer count as requested by user
            # self.add_event_log(f"👥 Viewers: {viewer_count}")
            
        except Exception as e:
            self.logger.error(f"Error handling viewer update: {e}")

    # ===========================================
    # LEGACY EVENT HANDLERS (for compatibility)
    # ===========================================
    
    def _update_leaderboard(self, username: str, coins: int, gifts: int):
        """Update leaderboard with new gift data"""
        # Find existing user or create new entry
        for gifter in self.leaderboard_data:
            if gifter['username'] == username:
                gifter['coins'] += coins
                gifter['gifts'] += gifts
                break
        else:
            self.leaderboard_data.append({
                'username': username,
                'coins': coins,
                'gifts': gifts
            })
        
        # Sort by coins (descending)
        self.leaderboard_data.sort(key=lambda x: x['coins'], reverse=True)
        
        # Update leaderboard display
        self._refresh_leaderboard()
    
    def _refresh_leaderboard(self):
        """Refresh leaderboard display"""
        tree = self.widgets['leaderboard_tree']
        
        # Clear existing items
        for item in tree.get_children():
            tree.delete(item)
        
        # Add top 10 gifters
        for i, gifter in enumerate(self.leaderboard_data[:10]):
            rank = i + 1
            tree.insert('', tk.END, values=(
                rank,
                gifter['username'],
                gifter['coins'],
                gifter['gifts']
            ))
    
    def clear_event_log(self):
        """Clear event log"""
        event_log = self.widgets['event_log']
        event_log.config(state=tk.NORMAL)
        event_log.delete(1.0, tk.END)
        event_log.config(state=tk.DISABLED)
    
    def export_event_log(self):
        """Export event log to file"""
        try:
            filename = filedialog.asksaveasfilename(
                title="Export Event Log",
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            
            if filename:
                content = self.widgets['event_log'].get(1.0, tk.END)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("Success", f"Event log exported to {filename}")
        
        except Exception as e:
            self.logger.error(f"Error exporting event log: {e}")
            messagebox.showerror("Error", f"Failed to export event log: {e}")
    
    def cleanup(self):
        """Cleanup resources when tab is closed"""
        if self.current_tracker:
            self.current_tracker.stop()  # Use optimized tracker method
