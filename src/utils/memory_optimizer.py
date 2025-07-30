#!/usr/bin/env python3
"""
Memory Monitor & Optimizer
===========================
Monitor penggunaan memory dan optimasi otomatis untuk stabilitas sistem.
"""

import psutil
import gc
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional
import os
import sys

class MemoryMonitor:
    """Monitor memory usage dan automatic cleanup"""
    
    def __init__(self):
        self.process = psutil.Process()
        self.monitoring = False
        self.memory_history = []
        self.max_memory_mb = 500  # Alert jika melebihi 500MB
        self.cleanup_interval = 300  # Cleanup setiap 5 menit
        self.monitor_thread = None
        
    def get_memory_usage(self) -> Dict:
        """Get current memory usage"""
        memory_info = self.process.memory_info()
        memory_percent = self.process.memory_percent()
        
        return {
            'rss_mb': memory_info.rss / 1024 / 1024,  # Physical memory
            'vms_mb': memory_info.vms / 1024 / 1024,  # Virtual memory
            'percent': memory_percent,
            'timestamp': datetime.now()
        }
    
    def start_monitoring(self):
        """Start memory monitoring"""
        if self.monitoring:
            return
            
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        print("🔍 Memory monitoring started")
    
    def stop_monitoring(self):
        """Stop memory monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
        print("⏹️ Memory monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        last_cleanup = time.time()
        
        while self.monitoring:
            try:
                usage = self.get_memory_usage()
                self.memory_history.append(usage)
                
                # Keep only last 100 records
                if len(self.memory_history) > 100:
                    self.memory_history = self.memory_history[-100:]
                
                # Check for high memory usage
                if usage['rss_mb'] > self.max_memory_mb:
                    print(f"⚠️ High memory usage: {usage['rss_mb']:.1f}MB")
                    self.force_cleanup()
                
                # Periodic cleanup
                current_time = time.time()
                if current_time - last_cleanup > self.cleanup_interval:
                    self.auto_cleanup()
                    last_cleanup = current_time
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                print(f"Memory monitoring error: {e}")
                time.sleep(30)
    
    def auto_cleanup(self):
        """Automatic memory cleanup"""
        print("🧹 Running automatic memory cleanup...")
        
        # Force garbage collection
        collected = gc.collect()
        
        # Get memory after cleanup
        usage_after = self.get_memory_usage()
        
        print(f"✅ Cleanup complete: {collected} objects collected, "
              f"Memory: {usage_after['rss_mb']:.1f}MB")
    
    def force_cleanup(self):
        """Force aggressive cleanup"""
        print("🚨 Force cleanup triggered!")
        
        # Multiple garbage collection passes
        for i in range(3):
            collected = gc.collect()
            print(f"  Pass {i+1}: {collected} objects")
        
        # Clear internal caches if available
        self.clear_matplotlib_cache()
        
        usage_after = self.get_memory_usage()
        print(f"✅ Force cleanup complete: Memory: {usage_after['rss_mb']:.1f}MB")
    
    def clear_matplotlib_cache(self):
        """Clear matplotlib caches"""
        try:
            import matplotlib.pyplot as plt
            plt.close('all')  # Close all figures
            
            # Clear font cache if available
            import matplotlib.font_manager as fm
            if hasattr(fm, '_fmcache'):
                fm._fmcache.clear()
                
        except Exception as e:
            print(f"Matplotlib cache clear error: {e}")
    
    def get_memory_report(self) -> str:
        """Generate memory usage report"""
        if not self.memory_history:
            return "No memory data available"
        
        current = self.memory_history[-1]
        avg_memory = sum(m['rss_mb'] for m in self.memory_history) / len(self.memory_history)
        max_memory = max(m['rss_mb'] for m in self.memory_history)
        
        return f"""Memory Usage Report:
Current: {current['rss_mb']:.1f}MB ({current['percent']:.1f}%)
Average: {avg_memory:.1f}MB
Peak: {max_memory:.1f}MB
History: {len(self.memory_history)} records
"""

class MemoryOptimizer:
    """Optimasi memory untuk komponen sistem"""
    
    @staticmethod
    def optimize_data_storage(data_list: List, max_size: int = 1000):
        """Optimize data storage by limiting size"""
        if len(data_list) > max_size:
            # Keep most recent data
            return data_list[-max_size:]
        return data_list
    
    @staticmethod
    def optimize_chart_data(chart_data: List, max_points: int = 200):
        """Optimize chart data for better performance"""
        if len(chart_data) <= max_points:
            return chart_data
        
        # Downsample data - keep every nth point
        step = len(chart_data) // max_points
        return chart_data[::step]
    
    @staticmethod
    def clear_old_logs(log_dir: str, days_to_keep: int = 7):
        """Clear old log files"""
        try:
            from pathlib import Path
            import time
            
            log_path = Path(log_dir)
            if not log_path.exists():
                return
            
            cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)
            
            for log_file in log_path.glob("*.log"):
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
                    print(f"🗑️ Deleted old log: {log_file.name}")
                    
        except Exception as e:
            print(f"Log cleanup error: {e}")

# Global memory monitor instance
memory_monitor = MemoryMonitor()

def start_memory_monitoring():
    """Start global memory monitoring"""
    memory_monitor.start_monitoring()

def stop_memory_monitoring():
    """Stop global memory monitoring"""
    memory_monitor.stop_monitoring()

def get_memory_status():
    """Get current memory status"""
    return memory_monitor.get_memory_usage()

def force_memory_cleanup():
    """Force memory cleanup"""
    memory_monitor.force_cleanup()

if __name__ == "__main__":
    # Test memory monitoring
    monitor = MemoryMonitor()
    monitor.start_monitoring()
    
    print("Memory monitoring test - Press Ctrl+C to stop")
    try:
        while True:
            usage = monitor.get_memory_usage()
            print(f"Memory: {usage['rss_mb']:.1f}MB ({usage['percent']:.1f}%)")
            time.sleep(10)
    except KeyboardInterrupt:
        monitor.stop_monitoring()
        print("Memory monitoring stopped")
