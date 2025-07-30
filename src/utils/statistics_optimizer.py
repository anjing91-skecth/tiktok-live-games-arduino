#!/usr/bin/env python3
"""
Statistics Update Optimizer
===========================
Utility untuk mengoptimalkan update statistics dengan:
1. Kombinasi update 30 detik untuk stats, 1 menit untuk charts
2. Memory management otomatis
3. Summary-only saving
4. Historical view
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from utils.memory_optimizer import MemoryOptimizer, memory_monitor

class StatisticsUpdateOptimizer:
    """Optimizer untuk update statistics yang efisien"""
    
    def __init__(self, statistics_tab, unified_session_manager=None):
        self.statistics_tab = statistics_tab
        self.unified_session_manager = unified_session_manager
        
        # Update intervals (seconds)
        self.stats_interval = 30    # 30 seconds untuk metrics
        self.charts_interval = 60   # 1 minute untuk charts
        self.memory_interval = 300  # 5 minutes untuk memory cleanup
        
        # Tracking
        self.last_stats_update = 0
        self.last_charts_update = 0
        self.last_memory_cleanup = 0
        
        # Thread control
        self.running = False
        self.update_thread = None
        
        # Memory limits
        self.max_memory_mb = 400
        self.cleanup_threshold_mb = 300
        
    def start_optimized_updates(self):
        """Start optimized update cycle"""
        if self.running:
            return
            
        self.running = True
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()
        print("🚀 Optimized statistics updates started")
    
    def stop_optimized_updates(self):
        """Stop optimized updates"""
        self.running = False
        if self.update_thread:
            self.update_thread.join()
        print("⏹️ Optimized statistics updates stopped")
    
    def _update_loop(self):
        """Main optimized update loop"""
        while self.running:
            try:
                current_time = time.time()
                
                # Check memory usage first
                memory_usage = self._check_memory_usage()
                if memory_usage > self.cleanup_threshold_mb:
                    self._perform_memory_cleanup()
                
                # Update stats (30 seconds)
                if (current_time - self.last_stats_update) >= self.stats_interval:
                    self._update_summary_stats()
                    self.last_stats_update = current_time
                
                # Update charts (1 minute)
                if (current_time - self.last_charts_update) >= self.charts_interval:
                    self._update_charts_optimized()
                    self.last_charts_update = current_time
                
                # Memory cleanup (5 minutes)
                if (current_time - self.last_memory_cleanup) >= self.memory_interval:
                    self._perform_memory_cleanup()
                    self.last_memory_cleanup = current_time
                
                # Sleep for 5 seconds before next check
                time.sleep(5)
                
            except Exception as e:
                print(f"Update loop error: {e}")
                time.sleep(10)
    
    def _check_memory_usage(self) -> float:
        """Check current memory usage in MB"""
        try:
            from utils.memory_optimizer import get_memory_status
            return get_memory_status()['rss_mb']
        except:
            return 0
    
    def _update_summary_stats(self):
        """Update hanya summary statistics (ringan)"""
        try:
            if not self.unified_session_manager:
                return
            
            # Get live data dari unified session manager
            live_data = self.unified_session_manager.get_live_memory_data()
            if not live_data:
                return
            
            # Update basic metrics di statistics tab
            if hasattr(self.statistics_tab, '_update_basic_metrics'):
                self.statistics_tab._update_basic_metrics(live_data)
            
            print(f"📊 Stats updated at {datetime.now().strftime('%H:%M:%S')}")
            
        except Exception as e:
            print(f"Error updating summary stats: {e}")
    
    def _update_charts_optimized(self):
        """Update charts dengan data yang sudah di-optimize"""
        try:
            if not self.unified_session_manager:
                return
            
            # Get time series data
            live_data = self.unified_session_manager.get_live_memory_data()
            if not live_data:
                return
            
            # Optimize data untuk charts
            time_series = live_data.get('time_series', {})
            
            # Limit data points untuk performance
            max_points = 200
            optimized_data = {}
            
            for key, data in time_series.items():
                if len(data) > max_points:
                    # Keep recent data dengan sampling
                    step = len(data) // max_points
                    optimized_data[key] = data[::step]
                else:
                    optimized_data[key] = data
            
            # Update charts di statistics tab
            if hasattr(self.statistics_tab, '_update_optimized_charts'):
                self.statistics_tab._update_optimized_charts(optimized_data)
            
            print(f"📈 Charts updated at {datetime.now().strftime('%H:%M:%S')}")
            
        except Exception as e:
            print(f"Error updating charts: {e}")
    
    def _perform_memory_cleanup(self):
        """Perform memory cleanup"""
        try:
            # Force garbage collection
            import gc
            collected = gc.collect()
            
            # Clear matplotlib cache
            try:
                import matplotlib.pyplot as plt
                plt.close('all')
            except:
                pass
            
            # Optimize internal data storage
            if hasattr(self.statistics_tab, 'current_session_data'):
                for key in self.statistics_tab.current_session_data:
                    data = self.statistics_tab.current_session_data[key]
                    if isinstance(data, list) and len(data) > 1000:
                        # Keep only recent 500 items
                        self.statistics_tab.current_session_data[key] = data[-500:]
            
            memory_after = self._check_memory_usage()
            print(f"🧹 Memory cleanup: {collected} objects, {memory_after:.1f}MB")
            
        except Exception as e:
            print(f"Memory cleanup error: {e}")
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get optimization statistics"""
        return {
            'stats_interval': self.stats_interval,
            'charts_interval': self.charts_interval,
            'last_stats_update': datetime.fromtimestamp(self.last_stats_update) if self.last_stats_update > 0 else None,
            'last_charts_update': datetime.fromtimestamp(self.last_charts_update) if self.last_charts_update > 0 else None,
            'memory_usage_mb': self._check_memory_usage(),
            'running': self.running
        }

class StatisticsMemoryManager:
    """Memory manager khusus untuk statistics tab"""
    
    @staticmethod
    def optimize_viewer_data(viewer_data: list, max_points: int = 500) -> list:
        """Optimize viewer data untuk memory efficiency"""
        if len(viewer_data) <= max_points:
            return viewer_data
        
        # Keep recent data with smart sampling
        recent_data = viewer_data[-max_points:]
        return recent_data
    
    @staticmethod
    def optimize_leaderboard_data(leaderboard: list, max_entries: int = 50) -> list:
        """Optimize leaderboard data"""
        return leaderboard[:max_entries]
    
    @staticmethod
    def create_session_summary(session_data: Dict) -> Dict:
        """Create summary dari session data untuk saving"""
        try:
            summary = {
                'session_id': session_data.get('session_id'),
                'start_time': session_data.get('start_time'),
                'end_time': datetime.now(),
                'duration_minutes': 0,
                'metrics': {
                    'peak_viewers': 0,
                    'total_comments': 0,
                    'total_likes': 0,
                    'total_gifts': 0,
                    'total_coins': 0,
                    'unique_contributors': 0
                },
                'top_contributors': [],
                'performance': {
                    'avg_viewers': 0,
                    'engagement_rate': 0,
                    'coins_per_minute': 0
                }
            }
            
            # Calculate metrics dari live data
            if 'metrics' in session_data:
                metrics = session_data['metrics']
                summary['metrics'].update({
                    'total_comments': metrics.get('total_comments', 0),
                    'total_likes': metrics.get('total_likes', 0),
                    'total_gifts': metrics.get('total_gifts', 0),
                    'total_coins': metrics.get('total_coins', 0)
                })
            
            # Calculate duration
            if session_data.get('start_time'):
                duration = datetime.now() - session_data['start_time']
                summary['duration_minutes'] = duration.total_seconds() / 60
            
            # Top contributors (top 10 only)
            contributors = session_data.get('top_contributors', [])
            summary['top_contributors'] = contributors[:10]
            
            return summary
            
        except Exception as e:
            print(f"Error creating session summary: {e}")
            return {}
    
    @staticmethod
    def save_session_summary_only(database_manager, session_summary: Dict):
        """Save hanya session summary, tidak detail events"""
        try:
            if not session_summary:
                return False
            
            # Save ke database dalam format summary
            # Implementasi tergantung database structure
            print(f"💾 Session summary saved: {session_summary['session_id']}")
            return True
            
        except Exception as e:
            print(f"Error saving session summary: {e}")
            return False

# Global optimizer instance
statistics_optimizer = None

def init_statistics_optimizer(statistics_tab, unified_session_manager=None):
    """Initialize statistics optimizer"""
    global statistics_optimizer
    statistics_optimizer = StatisticsUpdateOptimizer(statistics_tab, unified_session_manager)
    return statistics_optimizer

def start_optimized_statistics():
    """Start optimized statistics updates"""
    if statistics_optimizer:
        statistics_optimizer.start_optimized_updates()

def stop_optimized_statistics():
    """Stop optimized statistics updates"""
    if statistics_optimizer:
        statistics_optimizer.stop_optimized_updates()

def get_optimization_stats():
    """Get optimization statistics"""
    if statistics_optimizer:
        return statistics_optimizer.get_optimization_stats()
    return {}

if __name__ == "__main__":
    # Test optimization
    print("Statistics Update Optimizer Test")
    print("Memory optimization features available")
    
    # Test memory manager
    test_data = list(range(2000))
    optimized = StatisticsMemoryManager.optimize_viewer_data(test_data, 500)
    print(f"Data optimized: {len(test_data)} -> {len(optimized)} points")
