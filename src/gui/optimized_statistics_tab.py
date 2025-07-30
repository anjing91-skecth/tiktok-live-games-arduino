#!/usr/bin/env python3
"""
Optimized Statistics Tab - Lightweight & Memory Efficient
==========================================================
Tab statistik yang dioptimalkan dengan:
1. Update interval 30-60 detik
2. Memory management
3. Unified session manager integration
4. Summary-only saving
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import pandas as pd
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
from pathlib import Path

# Fix relative import issue
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from core.analytics_manager import AnalyticsManager
from utils.memory_optimizer import MemoryOptimizer

class OptimizedStatisticsTab:
    """Optimized statistics tab dengan memory management"""
    
    def __init__(self, parent_notebook, unified_session_manager=None):
        self.parent = parent_notebook
        self.unified_session_manager = unified_session_manager
        self.analytics_manager: Optional[AnalyticsManager] = None
        
        # Create the main frame
        self.frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.frame, text="📊 Statistics")
        
        # Optimized state tracking
        self.is_updating = False
        self.stats_update_interval = 30  # 30 seconds for stats
        self.chart_update_interval = 60  # 1 minute for charts
        self.last_stats_update = 0
        self.last_chart_update = 0
        
        # Memory optimized data storage
        self.max_data_points = 500  # Limit data points for memory
        self.max_chart_points = 200  # Limit chart points
        
        # Real-time data from unified session manager
        self.current_session_data = {
            'viewers': [],
            'activities': [],
            'gifts': [],
            'comments': [],
            'likes': []
        }
        
        # Historical view settings
        self.historical_days = 7
        self.show_trends = True
        
        self.setup_ui()
        self.start_optimized_updates()
    
    def setup_ui(self):
        """Setup optimized UI layout"""
        # Main container
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # === TOP CONTROLS ===
        self.create_control_panel(main_frame)
        
        # === SUMMARY CARDS ===
        self.create_summary_cards(main_frame)
        
        # === LIGHTWEIGHT CHARTS ===
        self.create_lightweight_charts(main_frame)
        
        # === SIMPLIFIED LEADERBOARD ===
        self.create_simple_leaderboard(main_frame)
        
        # === HISTORICAL VIEW ===
        self.create_historical_view(main_frame)
    
    def create_control_panel(self, parent):
        """Create control panel with settings"""
        control_frame = ttk.LabelFrame(parent, text="⚙️ Controls & Settings", padding=5)
        control_frame.pack(fill="x", pady=(0, 5))
        
        # Row 1: Update controls
        row1 = ttk.Frame(control_frame)
        row1.pack(fill="x", pady=2)
        
        # Auto update toggle
        self.auto_update_var = tk.BooleanVar(value=True)
        auto_check = ttk.Checkbutton(row1, text="Auto Update", 
                                   variable=self.auto_update_var,
                                   command=self.toggle_auto_update)
        auto_check.pack(side="left", padx=(0, 10))
        
        # Update interval selection
        ttk.Label(row1, text="Update:").pack(side="left", padx=(0, 5))
        self.update_interval_var = tk.StringVar(value="30s")
        interval_combo = ttk.Combobox(row1, textvariable=self.update_interval_var,
                                    values=["30s", "1m", "2m", "5m"], width=8)
        interval_combo.pack(side="left", padx=(0, 10))
        interval_combo.bind("<<ComboboxSelected>>", self.on_interval_change)
        
        # Manual refresh
        refresh_btn = ttk.Button(row1, text="🔄 Refresh", command=self.manual_refresh)
        refresh_btn.pack(side="left", padx=(0, 10))
        
        # Memory status
        self.memory_label = ttk.Label(row1, text="Memory: --", foreground="gray")
        self.memory_label.pack(side="right")
        
        # Row 2: Historical view controls
        row2 = ttk.Frame(control_frame)
        row2.pack(fill="x", pady=2)
        
        ttk.Label(row2, text="Historical:").pack(side="left", padx=(0, 5))
        self.historical_var = tk.StringVar(value="7 days")
        historical_combo = ttk.Combobox(row2, textvariable=self.historical_var,
                                      values=["1 day", "3 days", "7 days", "30 days"], width=10)
        historical_combo.pack(side="left", padx=(0, 10))
        historical_combo.bind("<<ComboboxSelected>>", self.on_historical_change)
        
        # Export summary
        export_btn = ttk.Button(row2, text="📊 Export Summary", command=self.export_summary)
        export_btn.pack(side="left", padx=(0, 10))
        
        # Cleanup button
        cleanup_btn = ttk.Button(row2, text="🧹 Memory Cleanup", command=self.force_cleanup)
        cleanup_btn.pack(side="right")
    
    def create_summary_cards(self, parent):
        """Create summary metric cards"""
        cards_frame = ttk.LabelFrame(parent, text="📈 Session Summary", padding=5)
        cards_frame.pack(fill="x", pady=(0, 5))
        
        # Configure grid
        for i in range(6):
            cards_frame.columnconfigure(i, weight=1)
        
        # Session info
        self.session_label = ttk.Label(cards_frame, text="No Session", font=("Arial", 10, "bold"))
        self.session_label.grid(row=0, column=0, columnspan=2, sticky="w", padx=5)
        
        self.status_indicator = ttk.Label(cards_frame, text="●", foreground="red", font=("Arial", 12))
        self.status_indicator.grid(row=0, column=2, sticky="w")
        
        self.duration_label = ttk.Label(cards_frame, text="Duration: --", foreground="gray")
        self.duration_label.grid(row=0, column=3, columnspan=3, sticky="e", padx=5)
        
        # Metrics row
        metrics = [
            ("👥", "Viewers", "viewers_label"),
            ("💬", "Comments", "comments_label"),
            ("❤️", "Likes", "likes_label"),
            ("🎁", "Gifts", "gifts_label"),
            ("💰", "Coins", "coins_label"),
            ("📊", "Avg/min", "rate_label")
        ]
        
        self.metric_labels = {}
        for i, (icon, label, attr) in enumerate(metrics):
            frame = ttk.Frame(cards_frame)
            frame.grid(row=1, column=i, padx=5, pady=5, sticky="ew")
            
            ttk.Label(frame, text=icon, font=("Arial", 14)).pack()
            ttk.Label(frame, text=label, font=("Arial", 8)).pack()
            
            value_label = ttk.Label(frame, text="0", font=("Arial", 11, "bold"))
            value_label.pack()
            self.metric_labels[attr] = value_label
            setattr(self, attr, value_label)
    
    def create_lightweight_charts(self, parent):
        """Create lightweight charts with limited data points"""
        charts_frame = ttk.LabelFrame(parent, text="📊 Trends (Lightweight)", padding=5)
        charts_frame.pack(fill="both", expand=True, pady=(0, 5))
        
        # Configure grid for 2 charts side by side
        charts_frame.columnconfigure(0, weight=1)
        charts_frame.columnconfigure(1, weight=1)
        
        # Viewer trend chart (left)
        viewer_frame = ttk.Frame(charts_frame)
        viewer_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        self.viewer_fig = Figure(figsize=(6, 3), dpi=80)
        self.viewer_ax = self.viewer_fig.add_subplot(111)
        self.viewer_canvas = FigureCanvasTkAgg(self.viewer_fig, viewer_frame)
        self.viewer_canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Activity trend chart (right)
        activity_frame = ttk.Frame(charts_frame)
        activity_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        
        self.activity_fig = Figure(figsize=(6, 3), dpi=80)
        self.activity_ax = self.activity_fig.add_subplot(111)
        self.activity_canvas = FigureCanvasTkAgg(self.activity_fig, activity_frame)
        self.activity_canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Initialize empty charts
        self.viewer_ax.set_title("Viewer Trend")
        self.activity_ax.set_title("Activity Rate")
        for ax in [self.viewer_ax, self.activity_ax]:
            ax.grid(True, alpha=0.3)
            ax.set_xlabel("Time")
    
    def create_simple_leaderboard(self, parent):
        """Create simplified leaderboard"""
        leaderboard_frame = ttk.LabelFrame(parent, text="🏆 Top Contributors", padding=5)
        leaderboard_frame.pack(fill="x", pady=(0, 5))
        
        # Configure grid
        leaderboard_frame.columnconfigure(1, weight=1)
        
        # Top 5 contributors only for performance
        self.leaderboard_labels = []
        for i in range(5):
            rank_label = ttk.Label(leaderboard_frame, text=f"{i+1}.", width=3)
            rank_label.grid(row=i, column=0, sticky="w", padx=(5, 10))
            
            name_label = ttk.Label(leaderboard_frame, text="--", anchor="w")
            name_label.grid(row=i, column=1, sticky="ew", padx=(0, 10))
            
            value_label = ttk.Label(leaderboard_frame, text="--", width=15, anchor="e")
            value_label.grid(row=i, column=2, sticky="e", padx=(0, 5))
            
            self.leaderboard_labels.append((name_label, value_label))
    
    def create_historical_view(self, parent):
        """Create historical data view"""
        historical_frame = ttk.LabelFrame(parent, text="📅 Historical Summary", padding=5)
        historical_frame.pack(fill="x", pady=(0, 5))
        
        # Summary metrics
        self.historical_text = tk.Text(historical_frame, height=6, wrap="word")
        self.historical_text.pack(fill="x")
        
        # Update with placeholder
        self.historical_text.insert("1.0", "Historical data will be displayed here...")
        self.historical_text.config(state="disabled")
    
    def start_optimized_updates(self):
        """Start optimized update cycle"""
        if not hasattr(self, '_update_thread'):
            self._update_thread = threading.Thread(target=self._update_loop, daemon=True)
            self._update_thread.start()
    
    def _update_loop(self):
        """Optimized update loop with different intervals"""
        while True:
            try:
                current_time = time.time()
                
                # Update stats every 30 seconds
                if (current_time - self.last_stats_update) >= self.stats_update_interval:
                    if self.auto_update_var.get():
                        self.update_summary_stats()
                        self.last_stats_update = current_time
                
                # Update charts every 1 minute
                if (current_time - self.last_chart_update) >= self.chart_update_interval:
                    if self.auto_update_var.get():
                        self.update_lightweight_charts()
                        self.last_chart_update = current_time
                
                # Update memory status every 30 seconds
                self.update_memory_status()
                
                # Sleep for 5 seconds to check conditions
                time.sleep(5)
                
            except Exception as e:
                print(f"Update loop error: {e}")
                time.sleep(10)
    
    def update_summary_stats(self):
        """Update summary statistics from unified session manager"""
        try:
            if not self.unified_session_manager:
                return
            
            # Get real-time data from unified session manager
            live_data = self.unified_session_manager.get_live_memory_data()
            
            if not live_data:
                return
            
            # Update session info
            session_id = live_data.get('session_id', 'No Session')
            self.session_label.config(text=session_id[:20])
            
            is_active = live_data.get('is_active', False)
            if is_active:
                self.status_indicator.config(foreground="green")
                
                # Calculate duration
                start_time = live_data.get('start_time')
                if start_time:
                    duration = datetime.now() - start_time
                    duration_str = str(duration).split('.')[0]  # Remove microseconds
                    self.duration_label.config(text=f"Duration: {duration_str}")
            else:
                self.status_indicator.config(foreground="red")
                self.duration_label.config(text="Duration: --")
            
            # Update metrics
            metrics = live_data.get('metrics', {})
            
            self.viewers_label.config(text=str(metrics.get('current_viewers', 0)))
            self.comments_label.config(text=str(metrics.get('total_comments', 0)))
            self.likes_label.config(text=str(metrics.get('total_likes', 0)))
            self.gifts_label.config(text=str(metrics.get('total_gifts', 0)))
            self.coins_label.config(text=f"{metrics.get('total_coins', 0):.0f}")
            
            # Calculate rate (activity per minute)
            if start_time:
                minutes = max(1, (datetime.now() - start_time).total_seconds() / 60)
                total_activity = metrics.get('total_comments', 0) + metrics.get('total_gifts', 0)
                rate = total_activity / minutes
                self.rate_label.config(text=f"{rate:.1f}")
            else:
                self.rate_label.config(text="--")
            
            # Update leaderboard
            self.update_simple_leaderboard(live_data)
            
        except Exception as e:
            print(f"Error updating summary stats: {e}")
    
    def update_simple_leaderboard(self, live_data):
        """Update simplified leaderboard"""
        try:
            contributors = live_data.get('top_contributors', [])
            
            for i, (name_label, value_label) in enumerate(self.leaderboard_labels):
                if i < len(contributors):
                    contributor = contributors[i]
                    name = contributor.get('username', f'User{i+1}')[:15]
                    value = contributor.get('total_coins', 0)
                    
                    name_label.config(text=name)
                    value_label.config(text=f"{value:.0f} coins")
                else:
                    name_label.config(text="--")
                    value_label.config(text="--")
                    
        except Exception as e:
            print(f"Error updating leaderboard: {e}")
    
    def update_lightweight_charts(self):
        """Update charts with optimized data"""
        try:
            if not self.unified_session_manager:
                return
            
            live_data = self.unified_session_manager.get_live_memory_data()
            if not live_data:
                return
            
            # Get time series data
            time_series = live_data.get('time_series', {})
            
            # Update viewer chart
            viewer_data = time_series.get('viewers', [])
            if viewer_data:
                # Optimize data points for performance
                optimized_data = MemoryOptimizer.optimize_chart_data(viewer_data, self.max_chart_points)
                
                times = [entry['timestamp'] for entry in optimized_data]
                counts = [entry['count'] for entry in optimized_data]
                
                self.viewer_ax.clear()
                self.viewer_ax.plot(times, counts, 'b-', linewidth=2, alpha=0.8)
                self.viewer_ax.set_title("Viewer Trend")
                self.viewer_ax.grid(True, alpha=0.3)
                self.viewer_fig.autofmt_xdate()
                self.viewer_canvas.draw()
            
            # Update activity chart
            activity_data = time_series.get('activity_rate', [])
            if activity_data:
                optimized_data = MemoryOptimizer.optimize_chart_data(activity_data, self.max_chart_points)
                
                times = [entry['timestamp'] for entry in optimized_data]
                rates = [entry['rate'] for entry in optimized_data]
                
                self.activity_ax.clear()
                self.activity_ax.plot(times, rates, 'g-', linewidth=2, alpha=0.8)
                self.activity_ax.set_title("Activity Rate")
                self.activity_ax.set_ylabel("Events/min")
                self.activity_ax.grid(True, alpha=0.3)
                self.activity_fig.autofmt_xdate()
                self.activity_canvas.draw()
            
        except Exception as e:
            print(f"Error updating charts: {e}")
    
    def update_memory_status(self):
        """Update memory usage display"""
        try:
            from utils.memory_optimizer import get_memory_status
            memory_info = get_memory_status()
            memory_mb = memory_info['rss_mb']
            
            color = "green" if memory_mb < 200 else "orange" if memory_mb < 400 else "red"
            self.memory_label.config(text=f"Memory: {memory_mb:.0f}MB", foreground=color)
            
        except Exception as e:
            self.memory_label.config(text="Memory: Error", foreground="red")
    
    def toggle_auto_update(self):
        """Toggle auto update on/off"""
        if self.auto_update_var.get():
            print("✅ Auto update enabled")
        else:
            print("⏸️ Auto update paused")
    
    def on_interval_change(self, event=None):
        """Handle update interval change"""
        interval_str = self.update_interval_var.get()
        
        if interval_str == "30s":
            self.stats_update_interval = 30
        elif interval_str == "1m":
            self.stats_update_interval = 60
        elif interval_str == "2m":
            self.stats_update_interval = 120
        elif interval_str == "5m":
            self.stats_update_interval = 300
        
        print(f"📊 Update interval changed to {interval_str}")
    
    def on_historical_change(self, event=None):
        """Handle historical period change"""
        period = self.historical_var.get()
        print(f"📅 Historical period changed to {period}")
        self.update_historical_view()
    
    def update_historical_view(self):
        """Update historical data view"""
        try:
            period = self.historical_var.get()
            days = int(period.split()[0])
            
            # Get historical summary (placeholder for now)
            summary_text = f"""Historical Summary - Last {period}:

📊 Session Performance:
• Average viewers: 150 ± 25
• Peak viewers: 300
• Total sessions: 12
• Average duration: 2h 15m

🎁 Gift Activity:
• Total gifts: 1,247
• Total value: 15,680 coins
• Top gift: Rose (45 times)
• Peak hour: 8-9 PM

👥 Engagement:
• Comments per session: 850 avg
• Likes per session: 320 avg
• Active contributors: 89 unique
• Return viewers: 65%

💡 Insights:
• Best performing time: 8-10 PM
• Most engaging content: Gaming streams
• Growth trend: +15% viewers
"""
            
            self.historical_text.config(state="normal")
            self.historical_text.delete("1.0", "end")
            self.historical_text.insert("1.0", summary_text)
            self.historical_text.config(state="disabled")
            
        except Exception as e:
            print(f"Error updating historical view: {e}")
    
    def manual_refresh(self):
        """Manual refresh all data"""
        print("🔄 Manual refresh triggered")
        self.update_summary_stats()
        self.update_lightweight_charts()
        self.update_historical_view()
        messagebox.showinfo("Refresh", "Data refreshed successfully!")
    
    def export_summary(self):
        """Export session summary"""
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("JSON files", "*.json")],
                title="Export Session Summary"
            )
            
            if file_path:
                if file_path.endswith('.json'):
                    # Export as JSON
                    summary_data = {
                        'export_time': datetime.now().isoformat(),
                        'session_id': self.session_label.cget('text'),
                        'metrics': {
                            'viewers': self.viewers_label.cget('text'),
                            'comments': self.comments_label.cget('text'),
                            'likes': self.likes_label.cget('text'),
                            'gifts': self.gifts_label.cget('text'),
                            'coins': self.coins_label.cget('text')
                        }
                    }
                    
                    with open(file_path, 'w') as f:
                        json.dump(summary_data, f, indent=2)
                else:
                    # Export as text
                    summary_text = f"""TikTok Live Games - Session Summary
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Session: {self.session_label.cget('text')}
Duration: {self.duration_label.cget('text')}

Metrics:
👥 Viewers: {self.viewers_label.cget('text')}
💬 Comments: {self.comments_label.cget('text')}
❤️ Likes: {self.likes_label.cget('text')}
🎁 Gifts: {self.gifts_label.cget('text')}
💰 Coins: {self.coins_label.cget('text')}
📊 Rate: {self.rate_label.cget('text')} events/min
"""
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(summary_text)
                
                messagebox.showinfo("Export", f"Summary exported to:\n{file_path}")
                
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export: {e}")
    
    def force_cleanup(self):
        """Force memory cleanup"""
        try:
            from utils.memory_optimizer import force_memory_cleanup
            force_memory_cleanup()
            
            # Clear chart caches
            plt.close('all')
            
            # Optimize internal data
            for key in self.current_session_data:
                self.current_session_data[key] = MemoryOptimizer.optimize_data_storage(
                    self.current_session_data[key], self.max_data_points
                )
            
            messagebox.showinfo("Cleanup", "Memory cleanup completed!")
            
        except Exception as e:
            messagebox.showerror("Cleanup Error", f"Cleanup failed: {e}")
    
    def set_analytics_manager(self, analytics_manager):
        """Set analytics manager reference"""
        self.analytics_manager = analytics_manager
    
    def set_unified_session_manager(self, unified_session_manager):
        """Set unified session manager reference"""
        self.unified_session_manager = unified_session_manager
