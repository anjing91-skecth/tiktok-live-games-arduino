#!/usr/bin/env python3
"""
Memory Optimizer - Optimasi dan Cleanup Memori
==============================================
Script untuk optimasi memori dan pembersihan data
"""

import gc
import psutil
import os
import json
import sqlite3
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any

class MemoryOptimizer:
    """Advanced memory optimization system"""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.process = psutil.Process(os.getpid())
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging"""
        logger = logging.getLogger('MemoryOptimizer')
        logger.setLevel(logging.INFO)
        
        # Console handler
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def get_memory_before(self) -> float:
        """Get memory usage before optimization"""
        try:
            return self.process.memory_info().rss / (1024 * 1024)
        except:
            return 0.0
    
    def perform_garbage_collection(self) -> Dict[str, Any]:
        """Perform comprehensive garbage collection"""
        self.logger.info("🧹 Starting garbage collection...")
        
        before_mb = self.get_memory_before()
        
        # Multiple GC passes
        collected_objects = 0
        for i in range(3):
            collected = gc.collect()
            collected_objects += collected
            self.logger.info(f"  Pass {i+1}: Collected {collected} objects")
        
        # Clear specific caches
        gc.disable()
        gc.enable()
        
        after_mb = self.get_memory_before()
        freed_mb = before_mb - after_mb
        
        result = {
            'before_mb': before_mb,
            'after_mb': after_mb,
            'freed_mb': freed_mb,
            'collected_objects': collected_objects,
            'efficiency': f"{(freed_mb/max(before_mb, 1)*100):.1f}%"
        }
        
        self.logger.info(f"✅ GC Complete: {freed_mb:.1f}MB freed ({result['efficiency']})")
        return result
    
    def cleanup_log_files(self, days_to_keep: int = 7) -> Dict[str, Any]:
        """Clean up old log files"""
        self.logger.info(f"📁 Cleaning log files older than {days_to_keep} days...")
        
        log_dir = Path("logs")
        if not log_dir.exists():
            return {'cleaned_files': 0, 'freed_mb': 0}
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        cleaned_files = 0
        freed_bytes = 0
        
        for log_file in log_dir.glob("*.log"):
            try:
                file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                if file_time < cutoff_date:
                    file_size = log_file.stat().st_size
                    log_file.unlink()
                    cleaned_files += 1
                    freed_bytes += file_size
                    self.logger.info(f"  Deleted: {log_file.name}")
            except Exception as e:
                self.logger.warning(f"  Failed to delete {log_file.name}: {e}")
        
        freed_mb = freed_bytes / (1024 * 1024)
        self.logger.info(f"✅ Log cleanup: {cleaned_files} files, {freed_mb:.1f}MB freed")
        
        return {
            'cleaned_files': cleaned_files,
            'freed_mb': freed_mb
        }
    
    def optimize_database(self) -> Dict[str, Any]:
        """Optimize database files"""
        self.logger.info("🗄️ Optimizing databases...")
        
        database_dir = Path("database")
        if not database_dir.exists():
            return {'optimized_dbs': 0, 'before_mb': 0, 'after_mb': 0}
        
        optimized_dbs = 0
        total_before = 0
        total_after = 0
        
        for db_file in database_dir.glob("*.db"):
            try:
                # Get size before
                before_size = db_file.stat().st_size
                total_before += before_size
                
                # Optimize database
                with sqlite3.connect(str(db_file)) as conn:
                    conn.execute("VACUUM")
                    conn.execute("ANALYZE")
                    conn.commit()
                
                # Get size after
                after_size = db_file.stat().st_size
                total_after += after_size
                
                freed = (before_size - after_size) / (1024 * 1024)
                self.logger.info(f"  {db_file.name}: {freed:.1f}MB freed")
                optimized_dbs += 1
                
            except Exception as e:
                self.logger.warning(f"  Failed to optimize {db_file.name}: {e}")
        
        total_freed = (total_before - total_after) / (1024 * 1024)
        self.logger.info(f"✅ DB optimization: {optimized_dbs} databases, {total_freed:.1f}MB freed")
        
        return {
            'optimized_dbs': optimized_dbs,
            'before_mb': total_before / (1024 * 1024),
            'after_mb': total_after / (1024 * 1024),
            'freed_mb': total_freed
        }
    
    def cleanup_temp_files(self) -> Dict[str, Any]:
        """Clean up temporary files"""
        self.logger.info("🗑️ Cleaning temporary files...")
        
        temp_patterns = [
            "*.tmp",
            "*.temp",
            "*~",
            "*.bak",
            "__pycache__/**/*"
        ]
        
        cleaned_files = 0
        freed_bytes = 0
        
        for pattern in temp_patterns:
            for temp_file in Path(".").rglob(pattern):
                try:
                    if temp_file.is_file():
                        file_size = temp_file.stat().st_size
                        temp_file.unlink()
                        cleaned_files += 1
                        freed_bytes += file_size
                        self.logger.info(f"  Deleted: {temp_file}")
                except Exception as e:
                    self.logger.warning(f"  Failed to delete {temp_file}: {e}")
        
        freed_mb = freed_bytes / (1024 * 1024)
        self.logger.info(f"✅ Temp cleanup: {cleaned_files} files, {freed_mb:.1f}MB freed")
        
        return {
            'cleaned_files': cleaned_files,
            'freed_mb': freed_mb
        }
    
    def create_optimization_report(self, results: Dict[str, Any]) -> str:
        """Create optimization report"""
        try:
            report = f"""
=== MEMORY OPTIMIZATION REPORT ===
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

GARBAGE COLLECTION:
- Memory Before: {results['gc']['before_mb']:.1f} MB
- Memory After: {results['gc']['after_mb']:.1f} MB
- Memory Freed: {results['gc']['freed_mb']:.1f} MB
- Objects Collected: {results['gc']['collected_objects']}
- Efficiency: {results['gc']['efficiency']}

LOG FILE CLEANUP:
- Files Deleted: {results['logs']['cleaned_files']}
- Space Freed: {results['logs']['freed_mb']:.1f} MB

DATABASE OPTIMIZATION:
- Databases Optimized: {results['db']['optimized_dbs']}
- Space Before: {results['db']['before_mb']:.1f} MB
- Space After: {results['db']['after_mb']:.1f} MB
- Space Freed: {results['db']['freed_mb']:.1f} MB

TEMPORARY FILES:
- Files Deleted: {results['temp']['cleaned_files']}
- Space Freed: {results['temp']['freed_mb']:.1f} MB

TOTAL OPTIMIZATION:
- Total Memory Freed: {results['gc']['freed_mb']:.1f} MB
- Total Disk Freed: {(results['logs']['freed_mb'] + results['db']['freed_mb'] + results['temp']['freed_mb']):.1f} MB

RECOMMENDATIONS:
"""
            
            total_freed = results['gc']['freed_mb']
            if total_freed > 50:
                report += "- Excellent optimization results\n"
                report += "- Consider running optimization weekly\n"
            elif total_freed > 20:
                report += "- Good optimization results\n"
                report += "- Run optimization bi-weekly\n"
            else:
                report += "- Minimal optimization gains\n"
                report += "- System is already well optimized\n"
            
            # Save report
            report_dir = Path("logs")
            report_dir.mkdir(exist_ok=True)
            report_file = report_dir / f"optimization_report_{int(datetime.now().timestamp())}.txt"
            
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            
            self.logger.info(f"📋 Optimization report saved: {report_file}")
            return str(report_file)
            
        except Exception as e:
            self.logger.error(f"Failed to create optimization report: {e}")
            return ""
    
    def optimize_all(self) -> Dict[str, Any]:
        """Perform complete optimization"""
        self.logger.info("🚀 Starting complete memory optimization...")
        
        # Get initial memory status
        initial_memory = self.get_memory_before()
        self.logger.info(f"📊 Initial memory usage: {initial_memory:.1f}MB")
        
        results = {}
        
        # 1. Garbage Collection
        results['gc'] = self.perform_garbage_collection()
        
        # 2. Clean log files
        results['logs'] = self.cleanup_log_files()
        
        # 3. Optimize databases
        results['db'] = self.optimize_database()
        
        # 4. Clean temp files
        results['temp'] = self.cleanup_temp_files()
        
        # Final memory check
        final_memory = self.get_memory_before()
        total_freed = initial_memory - final_memory
        
        self.logger.info(f"✅ Optimization complete!")
        self.logger.info(f"📊 Final memory usage: {final_memory:.1f}MB")
        self.logger.info(f"🎯 Total memory freed: {total_freed:.1f}MB")
        
        # Create report
        report_file = self.create_optimization_report(results)
        
        return {
            'initial_memory_mb': initial_memory,
            'final_memory_mb': final_memory,
            'total_freed_mb': total_freed,
            'results': results,
            'report_file': report_file
        }

def main():
    """Main optimization function"""
    print("🔧 TikTok Live Games - Memory Optimizer")
    print("=======================================")
    
    optimizer = MemoryOptimizer()
    
    try:
        results = optimizer.optimize_all()
        
        print("\n📊 OPTIMIZATION SUMMARY:")
        print(f"Memory Freed: {results['total_freed_mb']:.1f}MB")
        print(f"Report: {results['report_file']}")
        print("\n✅ Optimization completed successfully!")
        
    except Exception as e:
        print(f"❌ Optimization failed: {e}")

if __name__ == "__main__":
    main()
