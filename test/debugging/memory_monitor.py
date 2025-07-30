#!/usr/bin/env python3
"""
Memory Monitor - Real-time Memory Usage Monitor
==============================================
Monitor penggunaan memori sistem secara real-time
"""

import time
import psutil
import os
import logging
from datetime import datetime
from pathlib import Path

class MemoryMonitor:
    """Real-time memory monitoring system"""
    
    def __init__(self, check_interval: int = 5):
        self.check_interval = check_interval
        self.process = psutil.Process(os.getpid())
        self.logger = self._setup_logging()
        
        # Memory thresholds (MB)
        self.warning_threshold = 400
        self.critical_threshold = 600
        
        # Statistics
        self.peak_memory = 0
        self.start_time = time.time()
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for memory monitor"""
        logger = logging.getLogger('MemoryMonitor')
        logger.setLevel(logging.INFO)
        
        # Create logs directory
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # File handler
        file_handler = logging.FileHandler(
            log_dir / f"memory_monitor_{datetime.now().strftime('%Y%m%d')}.log"
        )
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def get_memory_info(self) -> dict:
        """Get detailed memory information"""
        try:
            # Process memory
            process_memory = self.process.memory_info()
            process_mb = process_memory.rss / (1024 * 1024)
            
            # System memory
            system_memory = psutil.virtual_memory()
            system_available_mb = system_memory.available / (1024 * 1024)
            system_total_mb = system_memory.total / (1024 * 1024)
            system_used_percent = system_memory.percent
            
            # CPU info
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Update peak
            if process_mb > self.peak_memory:
                self.peak_memory = process_mb
            
            return {
                'timestamp': datetime.now(),
                'process_memory_mb': process_mb,
                'system_available_mb': system_available_mb,
                'system_total_mb': system_total_mb,
                'system_used_percent': system_used_percent,
                'cpu_percent': cpu_percent,
                'peak_memory_mb': self.peak_memory,
                'uptime_minutes': (time.time() - self.start_time) / 60
            }
        except Exception as e:
            self.logger.error(f"Failed to get memory info: {e}")
            return {}
    
    def check_memory_status(self, memory_info: dict) -> str:
        """Check memory status and return alert level"""
        process_mb = memory_info.get('process_memory_mb', 0)
        
        if process_mb > self.critical_threshold:
            return "CRITICAL"
        elif process_mb > self.warning_threshold:
            return "WARNING"
        else:
            return "OK"
    
    def log_memory_status(self, memory_info: dict):
        """Log current memory status"""
        if not memory_info:
            return
            
        status = self.check_memory_status(memory_info)
        
        log_msg = (
            f"📊 Process: {memory_info['process_memory_mb']:.1f}MB "
            f"(Peak: {memory_info['peak_memory_mb']:.1f}MB) | "
            f"System: {memory_info['system_used_percent']:.1f}% "
            f"({memory_info['system_available_mb']:.0f}MB free) | "
            f"CPU: {memory_info['cpu_percent']:.1f}% | "
            f"Status: {status}"
        )
        
        if status == "CRITICAL":
            self.logger.error(log_msg)
        elif status == "WARNING":
            self.logger.warning(log_msg)
        else:
            self.logger.info(log_msg)
    
    def monitor_continuous(self):
        """Start continuous monitoring"""
        self.logger.info("🚀 Memory Monitor started")
        self.logger.info(f"⚙️ Check interval: {self.check_interval}s")
        self.logger.info(f"⚠️ Warning threshold: {self.warning_threshold}MB")
        self.logger.info(f"🚨 Critical threshold: {self.critical_threshold}MB")
        
        try:
            while True:
                memory_info = self.get_memory_info()
                self.log_memory_status(memory_info)
                
                # Check for memory leaks (continuous growth)
                if memory_info.get('uptime_minutes', 0) > 10:  # After 10 minutes
                    growth_rate = self.peak_memory / (memory_info.get('uptime_minutes', 1) / 60)  # MB per hour
                    if growth_rate > 50:  # Growing more than 50MB per hour
                        self.logger.warning(f"🔍 Potential memory leak detected: {growth_rate:.1f}MB/hour growth rate")
                
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            self.logger.info("🛑 Memory Monitor stopped by user")
        except Exception as e:
            self.logger.error(f"Memory Monitor crashed: {e}")
    
    def create_memory_report(self) -> str:
        """Create detailed memory report"""
        try:
            memory_info = self.get_memory_info()
            
            report = f"""
=== MEMORY USAGE REPORT ===
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

PROCESS MEMORY:
- Current: {memory_info['process_memory_mb']:.1f} MB
- Peak: {memory_info['peak_memory_mb']:.1f} MB
- Uptime: {memory_info['uptime_minutes']:.1f} minutes

SYSTEM MEMORY:
- Total: {memory_info['system_total_mb']:.0f} MB
- Available: {memory_info['system_available_mb']:.0f} MB
- Used: {memory_info['system_used_percent']:.1f}%

SYSTEM PERFORMANCE:
- CPU Usage: {memory_info['cpu_percent']:.1f}%

STATUS: {self.check_memory_status(memory_info)}

RECOMMENDATIONS:
"""
            
            status = self.check_memory_status(memory_info)
            if status == "CRITICAL":
                report += "- IMMEDIATE ACTION REQUIRED: Restart application\n"
                report += "- Consider reducing data retention settings\n"
                report += "- Check for memory leaks\n"
            elif status == "WARNING":
                report += "- Monitor closely\n"
                report += "- Consider manual memory cleanup\n"
                report += "- Reduce update frequencies\n"
            else:
                report += "- Memory usage is healthy\n"
                report += "- No action required\n"
            
            # Save report
            report_dir = Path("logs")
            report_dir.mkdir(exist_ok=True)
            report_file = report_dir / f"memory_report_{int(time.time())}.txt"
            
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            
            self.logger.info(f"📋 Memory report saved: {report_file}")
            return str(report_file)
            
        except Exception as e:
            self.logger.error(f"Failed to create memory report: {e}")
            return ""

def main():
    """Main function for memory monitoring"""
    print("🔍 TikTok Live Games - Memory Monitor")
    print("=====================================")
    
    # Create monitor
    monitor = MemoryMonitor(check_interval=5)
    
    try:
        # Create initial report
        report_file = monitor.create_memory_report()
        print(f"📋 Initial report: {report_file}")
        
        # Start continuous monitoring
        monitor.monitor_continuous()
        
    except Exception as e:
        print(f"❌ Monitor failed: {e}")

if __name__ == "__main__":
    main()
