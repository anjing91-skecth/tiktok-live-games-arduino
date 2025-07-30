#!/usr/bin/env python3
"""
Unified Session Manager - Smart Session Management dengan Room ID Detection
===============================================================
Implementasi session management yang optimal dengan:
1. Real-time Arduino triggers
2. Smart session continuation berdasarkan Room ID  
3. Triple priority data flow
4. 3-month retention dengan auto-archive
"""

import time
import threading
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import sqlite3
import re
from collections import defaultdict, deque
import psutil
import gc

from .database_manager import DatabaseManager
# from .tiktok_live_connector import TikTokLiveConnector  # Optional import
# from .arduino_controller import ArduinoController  # Optional import


class UnifiedSessionManager:
    """
    Unified Session Manager yang menggabungkan semua komponen
    dengan optimasi memory dan performance
    """
    
    def __init__(self, database_manager=None):
        self.logger = logging.getLogger(__name__)
        
        # Database & Core Components
        self.db_manager = database_manager or DatabaseManager()
        self.tiktok_connector = None
        self.arduino_controller = None
        
        # Session State
        self.current_session = None
        self.sessions = {}
        self.room_id_sessions = {}  # Room ID → Session mapping
        self.is_running = False
        
        # Threading & Async
        self.event_loop = None
        self.background_thread = None
        self.arduino_thread = None
        self.lock = threading.Lock()
        
        # Data Flow Components
        self.data_flow = None
        self.background_saver = None
        self.archive_scheduler = None
        
        # Memory Optimization
        self.memory_threshold = 500 * 1024 * 1024  # 500MB
        self.last_memory_cleanup = time.time()
        self.cleanup_interval = 300  # 5 minutes
        
        # Initialize components
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all internal components"""
        try:
            # Data Flow Manager
            self.data_flow = TriplePriorityDataFlow(self.db_manager)
            
            # Background Saver
            self.background_saver = BackgroundSaver(self.db_manager)
            
            # Archive Scheduler
            self.archive_scheduler = AutoArchiveScheduler(self.db_manager)
            
            # Arduino Controller (optional)
            try:
                from .arduino_controller import ArduinoController
                self.arduino_controller = ArduinoController()
            except ImportError:
                self.arduino_controller = None
                self.logger.warning("[ARDUINO] Arduino controller not available")
            
            self.logger.info("[ARDUINO] Arduino real-time thread started")
            
        except Exception as e:
            self.logger.error(f"[ERROR] Failed to initialize components: {e}")
            raise

    def get_live_memory_data(self) -> Dict:
        """Get real-time memory and system data for statistics"""
        try:
            # Get memory info
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()
            
            # Get CPU info
            cpu_percent = process.cpu_percent()
            
            # Get session stats - FIX: SessionData objects, not dict
            active_sessions = len([s for s in self.sessions.values() if hasattr(s, 'is_active') and s.is_active])
            total_sessions = len(self.sessions)
            
            # Get current session stats if available
            current_stats = self._get_current_session_stats()
            
            # Get recent events count (last 5 minutes)
            recent_events = self._get_recent_events_count()
            
            return {
                'memory': {
                    'rss': memory_info.rss,
                    'vms': memory_info.vms,
                    'percent': memory_percent,
                    'formatted_rss': f"{memory_info.rss / 1024 / 1024:.1f} MB",
                    'formatted_vms': f"{memory_info.vms / 1024 / 1024:.1f} MB"
                },
                'cpu': {
                    'percent': cpu_percent
                },
                'sessions': {
                    'active': active_sessions,
                    'total': total_sessions,
                    'room_ids': len(self.room_id_sessions)
                },
                'events': {
                    'recent_count': recent_events,
                    'total_processed': getattr(self, 'total_events_processed', 0)
                },
                'system': {
                    'uptime': time.time() - getattr(self, 'start_time', time.time()),
                    'last_cleanup': self.last_memory_cleanup,
                    'is_running': self.is_running
                },
                # Add current session statistics
                'current_session': current_stats
            }
        except Exception as e:
            self.logger.error(f"[ERROR] Failed to get live memory data: {e}")
            return self._get_default_live_data()
    
    def _get_current_session_stats(self) -> Dict:
        """Get current session statistics"""
        try:
            if not self.current_session:
                return {}
            
            session = self.current_session
            stats = {
                'total_viewers': session.summary_stats.get('total_viewers', 0),
                'max_viewers': session.summary_stats.get('max_viewers', 0),
                'total_gifts': session.summary_stats.get('total_gifts', 0),
                'total_comments': session.summary_stats.get('total_comments', 0),
                'total_likes': session.summary_stats.get('total_likes', 0),
                'likes': session.summary_stats.get('total_likes', 0),  # Alias for likes
                'viewers': session.summary_stats.get('total_viewers', 0),  # Current viewers
                'total_coins': session.summary_stats.get('total_gifts', 0) * 10,  # Estimate coins
                'unique_gifters': len(set(event.get('username', '') for event in session.live_events if event.get('type') == 'gift')),
                'duration': self._format_session_duration(session.start_time),
                'top_gifters': self._get_top_gifters_from_session(session)
            }
            return stats
        except Exception as e:
            self.logger.debug(f"Error getting current session stats: {e}")
            return {}
    
    def _get_default_live_data(self) -> Dict:
        """Return default live data structure"""
        return {
            'memory': {'rss': 0, 'vms': 0, 'percent': 0, 'formatted_rss': '0.0 MB', 'formatted_vms': '0.0 MB'},
            'cpu': {'percent': 0},
            'sessions': {'active': 0, 'total': 0, 'room_ids': 0},
            'events': {'recent_count': 0, 'total_processed': 0},
            'system': {'uptime': 0, 'last_cleanup': 0, 'is_running': False},
            'current_session': {}
        }
    
    def _format_session_duration(self, start_time) -> str:
        """Format session duration"""
        try:
            duration = datetime.now() - start_time
            total_seconds = int(duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        except:
            return "00:00:00"
    
    def _get_top_gifters_from_session(self, session) -> List[Dict]:
        """Get top gifters from session events"""
        try:
            gifter_stats = defaultdict(lambda: {'gift_count': 0, 'total_value': 0})
            
            for event in session.live_events:
                if event.get('type') == 'gift':
                    username = event.get('username', 'Unknown')
                    gift_value = event.get('gift_value', 0)
                    gifter_stats[username]['gift_count'] += 1
                    gifter_stats[username]['total_value'] += gift_value
            
            # Sort by total value
            top_gifters = []
            for username, stats in sorted(gifter_stats.items(), key=lambda x: x[1]['total_value'], reverse=True)[:5]:
                top_gifters.append({
                    'username': username,
                    'gift_count': stats['gift_count'],
                    'total_value': stats['total_value']
                })
            
            return top_gifters
        except Exception as e:
            self.logger.debug(f"Error getting top gifters: {e}")
            return []
    
    def _get_recent_events_count(self) -> int:
        """Get count of events in the last 5 minutes"""
        try:
            if not self.current_session:
                return 0
            
            session_id = self.current_session.session_id
            
            # Get events from the last 5 minutes
            five_minutes_ago = datetime.now() - timedelta(minutes=5)
            
            query = """
            SELECT COUNT(*) FROM live_events 
            WHERE session_id = ? AND timestamp > ?
            """
            
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute(query, (session_id, five_minutes_ago.isoformat()))
                return cursor.fetchone()[0]
                
        except Exception as e:
            self.logger.error(f"[ERROR] Failed to get recent events count: {e}")
            return 0

    def initialize(self):
        """Initialize the unified session manager"""
        try:
            self.start_time = time.time()
            
            # Initialize data flow
            self.data_flow.start_processing()
            
            # Start archive scheduler
            self.archive_scheduler.start_scheduler()
            
            # Initialize smart session continuation
            self.session_continuation = SmartSessionContinuation(self)
            
            self.logger.info("[TARGET] Unified Session Manager initialized")
            
        except Exception as e:
            self.logger.error(f"[ERROR] Initialization error: {e}")
            raise
    
    def start_session(self, account_username, room_id=None):
        """Start a new session atau continue existing session"""
        try:
            # Check if we should continue existing session
            if room_id and self.session_continuation.should_continue_session(room_id):
                if self.session_continuation.continue_session(room_id):
                    return self.current_session
            
            # Create new session
            session_id = f"session_{account_username}_{int(time.time())}"
            
            session = SessionData(session_id, account_username, room_id)
            
            # Store session
            self.sessions[session_id] = session
            self.current_session = session
            
            # Track by room ID if available
            if room_id:
                self.room_id_sessions[room_id] = {
                    'session_id': session_id,
                    'last_activity': datetime.now().isoformat()
                }
            
            # Save to database
            self._save_session_to_db(session)
            
            self.logger.info(f"[SESSION] Session started: {session_id}")
            return session
            
        except Exception as e:
            self.logger.error(f"[ERROR] Start session error: {e}")
            return None
    
    def stop_session(self, session_id=None):
        """Stop current or specified session"""
        try:
            target_session = None
            
            if session_id:
                target_session = self.sessions.get(session_id)
            else:
                target_session = self.current_session
            
            if not target_session:
                return False
            
            # Mark session as ended
            target_session.is_active = False
            target_session.is_connected = False
            target_session.end_time = datetime.now()
            
            # Update in database
            self._update_session_in_db(target_session)
            
            # Clear current session if it's the one being stopped
            if self.current_session == target_session:
                self.current_session = None
            
            self.logger.info(f"[STOP][SESSION] Session stopped: {target_session.session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"[ERROR] Stop session error: {e}")
            return False
    
    def add_live_event(self, event_data):
        """Add live event to current session"""
        try:
            if not self.current_session:
                return False
            
            # Detect room ID if not set
            if not self.current_session.room_id:
                room_id = self.session_continuation.detect_room_id(event_data)
                if room_id:
                    self.current_session.room_id = room_id
                    self.room_id_sessions[room_id] = {
                        'session_id': self.current_session.session_id,
                        'last_activity': datetime.now().isoformat()
                    }
            
            # Add to session
            self.current_session.add_event(event_data)
            
            # Add to appropriate priority queue
            event_type = event_data.get('type', '')
            if event_type in ['gift', 'comment'] and event_data.get('trigger_arduino', False):
                self.data_flow.add_critical(event_data)
            else:
                self.data_flow.add_high(event_data)
            
            return True
            
        except Exception as e:
            self.logger.error(f"[ERROR] Add live event error: {e}")
            return False
    
    def get_session_summary(self, session_id=None):
        """Get session summary"""
        try:
            target_session = None
            
            if session_id:
                target_session = self.sessions.get(session_id)
            else:
                target_session = self.current_session
            
            if not target_session:
                return None
            
            return target_session.get_summary()
            
        except Exception as e:
            self.logger.error(f"[ERROR] Get session summary error: {e}")
            return None
    
    def cleanup_memory(self):
        """Perform memory cleanup"""
        try:
            current_time = time.time()
            
            # Check if cleanup is needed
            if (current_time - self.last_memory_cleanup) < self.cleanup_interval:
                return
            
            # Get current memory usage
            process = psutil.Process()
            memory_info = process.memory_info()
            
            if memory_info.rss > self.memory_threshold:
                self.logger.info("[MEMORY] Starting memory cleanup...")
                
                # Clean old session data
                self._cleanup_old_sessions()
                
                # Clear event queues if too large
                self._cleanup_data_flow_queues()
                
                # Force garbage collection
                gc.collect()
                
                self.logger.info("[MEMORY] Memory cleanup completed")
            
            self.last_memory_cleanup = current_time
            
        except Exception as e:
            self.logger.error(f"[ERROR] Memory cleanup error: {e}")
    
    def _cleanup_old_sessions(self):
        """Clean up old session data from memory"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=2)
            
            sessions_to_remove = []
            for session_id, session in self.sessions.items():
                if (not session.is_active and 
                    session.last_activity < cutoff_time):
                    sessions_to_remove.append(session_id)
            
            for session_id in sessions_to_remove:
                del self.sessions[session_id]
                self.logger.debug(f"[MEMORY] Cleaned session: {session_id}")
                
        except Exception as e:
            self.logger.error(f"[ERROR] Session cleanup error: {e}")
    
    def _cleanup_data_flow_queues(self):
        """Clean up data flow queues if too large"""
        try:
            max_queue_size = 1000
            
            if len(self.data_flow.normal_queue) > max_queue_size:
                # Keep only recent items
                with self.data_flow.lock:
                    items_to_keep = list(self.data_flow.normal_queue)[-max_queue_size//2:]
                    self.data_flow.normal_queue.clear()
                    self.data_flow.normal_queue.extend(items_to_keep)
                
                self.logger.debug("[MEMORY] Cleaned normal priority queue")
                
        except Exception as e:
            self.logger.error(f"[ERROR] Queue cleanup error: {e}")
    
    def _save_session_to_db(self, session):
        """Save session to database"""
        try:
            query = """
            INSERT INTO sessions (
                session_id, account_username, room_id, start_time,
                is_active, is_connected
            ) VALUES (?, ?, ?, ?, ?, ?)
            """
            
            with self.db_manager.get_connection() as conn:
                conn.execute(query, (
                    session.session_id,
                    session.account_username,
                    session.room_id,
                    session.start_time.isoformat(),
                    session.is_active,
                    session.is_connected
                ))
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"[ERROR] Save session to DB error: {e}")
    
    def _update_session_in_db(self, session):
        """Update session in database"""
        try:
            query = """
            UPDATE sessions SET
                end_time = ?, is_active = ?, is_connected = ?,
                last_activity = ?
            WHERE session_id = ?
            """
            
            with self.db_manager.get_connection() as conn:
                conn.execute(query, (
                    session.end_time.isoformat() if session.end_time else None,
                    session.is_active,
                    session.is_connected,
                    session.last_activity.isoformat(),
                    session.session_id
                ))
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"[ERROR] Update session in DB error: {e}")
    
    def get_all_sessions(self):
        """Get all sessions"""
        return {
            'current_session': self.current_session.get_summary() if self.current_session else None,
            'all_sessions': [session.get_summary() for session in self.sessions.values()],
            'room_id_mapping': self.room_id_sessions.copy()
        }
    
    def get_statistics(self):
        """Get comprehensive statistics"""
        try:
            return {
                'memory_usage': self._get_memory_stats(),
                'session_stats': self._get_session_stats(),
                'data_flow_stats': self._get_data_flow_stats(),
                'system_stats': self._get_system_stats()
            }
            
        except Exception as e:
            self.logger.error(f"[ERROR] Get statistics error: {e}")
            return {}
    
    def _get_memory_stats(self):
        """Get memory statistics"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            
            return {
                'rss_mb': memory_info.rss / 1024 / 1024,
                'vms_mb': memory_info.vms / 1024 / 1024,
                'percent': process.memory_percent(),
                'threshold_mb': self.memory_threshold / 1024 / 1024,
                'last_cleanup': self.last_memory_cleanup
            }
            
        except Exception as e:
            self.logger.error(f"[ERROR] Memory stats error: {e}")
            return {}
    
    def _get_session_stats(self):
        """Get session statistics"""
        try:
            active_sessions = len([s for s in self.sessions.values() if s.is_active])
            
            return {
                'total_sessions': len(self.sessions),
                'active_sessions': active_sessions,
                'room_ids_tracked': len(self.room_id_sessions),
                'current_session_id': self.current_session.session_id if self.current_session else None
            }
            
        except Exception as e:
            self.logger.error(f"[ERROR] Session stats error: {e}")
            return {}
    
    def _get_data_flow_stats(self):
        """Get data flow statistics"""
        try:
            return {
                'queue_sizes': {
                    'critical': len(self.data_flow.critical_queue),
                    'high': len(self.data_flow.high_queue),
                    'normal': len(self.data_flow.normal_queue)
                },
                'processed_counts': self.data_flow.processed_counts.copy(),
                'last_processed': self.data_flow.last_processed_time.copy(),
                'is_processing': self.data_flow.is_processing
            }
            
        except Exception as e:
            self.logger.error(f"[ERROR] Data flow stats error: {e}")
            return {}
    
    def _get_system_stats(self):
        """Get system statistics"""
        try:
            return {
                'uptime': time.time() - getattr(self, 'start_time', time.time()),
                'is_running': self.is_running,
                'arduino_connected': getattr(self.arduino_controller, 'is_connected', False),
                'tiktok_connected': getattr(self.tiktok_connector, 'is_connected', False)
            }
            
        except Exception as e:
            self.logger.error(f"[ERROR] System stats error: {e}")
            return {}
    
    def shutdown(self):
        """Shutdown the unified session manager"""
        try:
            self.logger.info("[SYSTEM] Shutting down Unified Session Manager...")
            
            # Stop current session
            if self.current_session:
                self.stop_session()
            
            # Stop data flow
            if self.data_flow:
                self.data_flow.stop_processing()
            
            # Stop background saver
            if self.background_saver:
                self.background_saver.stop_background_thread()
            
            # Stop archive scheduler
            if self.archive_scheduler:
                self.archive_scheduler.stop_scheduler()
            
            # Final memory cleanup
            self.cleanup_memory()
            
            self.is_running = False
            self.logger.info("[STOP][SESSION] Unified Session Manager shutdown complete")
            
        except Exception as e:
            self.logger.error(f"[ERROR] Shutdown error: {e}")


class TriplePriorityDataFlow:
    """
    Data flow dengan 3 prioritas:
    1. CRITICAL: Arduino triggers (real-time)
    2. HIGH: Live events (1-2 detik delay)
    3. NORMAL: Statistics & analytics (5-10 detik delay)
    """
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
        
        # Priority Queues
        self.critical_queue = deque()  # Arduino triggers
        self.high_queue = deque()      # Live events
        self.normal_queue = deque()    # Statistics
        
        # Processing state
        self.is_processing = False
        self.process_thread = None
        self.lock = threading.Lock()
        
        # Performance metrics
        self.processed_counts = {'critical': 0, 'high': 0, 'normal': 0}
        self.last_processed_time = {'critical': 0, 'high': 0, 'normal': 0}
    
    def add_critical(self, data):
        """Add critical priority data (Arduino triggers)"""
        with self.lock:
            self.critical_queue.append({
                'data': data,
                'timestamp': time.time(),
                'priority': 'critical'
            })
    
    def add_high(self, data):
        """Add high priority data (Live events)"""
        with self.lock:
            self.high_queue.append({
                'data': data,
                'timestamp': time.time(),
                'priority': 'high'
            })
    
    def add_normal(self, data):
        """Add normal priority data (Statistics)"""
        with self.lock:
            self.normal_queue.append({
                'data': data,
                'timestamp': time.time(),
                'priority': 'normal'
            })
    
    def start_processing(self):
        """Start the triple priority processing"""
        if self.is_processing:
            return
        
        self.is_processing = True
        self.process_thread = threading.Thread(target=self._process_loop, daemon=True)
        self.process_thread.start()
        
        # Start background saver
        if hasattr(self, 'background_saver'):
            self.background_saver.start_background_thread()
        
        self.logger.info("[SYSTEM] Triple priority data flow started")
    
    def stop_processing(self):
        """Stop the processing"""
        self.is_processing = False
        if self.process_thread and self.process_thread.is_alive():
            self.process_thread.join(timeout=2)
        self.logger.info("[STOP][DATAFLOW] Triple priority data flow stopped")
    
    def _process_loop(self):
        """Main processing loop dengan priority handling"""
        while self.is_processing:
            try:
                # Process critical queue first (Arduino triggers)
                if self.critical_queue:
                    self._process_critical()
                
                # Process high priority queue (Live events)
                elif self.high_queue:
                    self._process_high()
                
                # Process normal priority queue (Statistics)
                elif self.normal_queue:
                    self._process_normal()
                
                else:
                    # No data to process, sleep briefly
                    time.sleep(0.1)
                    
            except Exception as e:
                self.logger.error(f"[ERROR] Data flow processing error: {e}")
                time.sleep(0.5)
    
    def _process_critical(self):
        """Process critical priority data"""
        try:
            with self.lock:
                if not self.critical_queue:
                    return
                item = self.critical_queue.popleft()
            
            # Process Arduino trigger immediately
            self._handle_arduino_trigger(item['data'])
            
            # Update metrics
            self.processed_counts['critical'] += 1
            self.last_processed_time['critical'] = time.time()
            
        except Exception as e:
            self.logger.error(f"[ERROR] Critical processing error: {e}")
    
    def _process_high(self):
        """Process high priority data"""
        try:
            with self.lock:
                if not self.high_queue:
                    return
                item = self.high_queue.popleft()
            
            # Process live event
            self._handle_live_event(item['data'])
            
            # Update metrics
            self.processed_counts['high'] += 1
            self.last_processed_time['high'] = time.time()
            
            # Small delay for high priority
            time.sleep(0.05)
            
        except Exception as e:
            self.logger.error(f"[ERROR] High priority processing error: {e}")
    
    def _process_normal(self):
        """Process normal priority data"""
        try:
            with self.lock:
                if not self.normal_queue:
                    return
                item = self.normal_queue.popleft()
            
            # Process statistics
            self._handle_statistics(item['data'])
            
            # Update metrics
            self.processed_counts['normal'] += 1
            self.last_processed_time['normal'] = time.time()
            
            # Longer delay for normal priority
            time.sleep(0.2)
            
        except Exception as e:
            self.logger.error(f"[ERROR] Normal priority processing error: {e}")
    
    def _handle_arduino_trigger(self, data):
        """Handle Arduino trigger data"""
        try:
            event_type = data.get('type')
            if event_type == 'gift':
                gift_name = data.get('gift_name', '')
                action = data.get('action', '')
                self.logger.debug(f"[GIFT][TRIGGER] Gift: {gift_name} → {action}")
                
                # Send to Arduino immediately
                # arduino_controller.trigger_action(action)
                
            elif event_type == 'comment':
                comment = data.get('comment', '')
                self.logger.debug(f"[COMMENT][TRIGGER] Comment: {comment}")
                
        except Exception as e:
            self.logger.error(f"[ERROR] Arduino trigger handling error: {e}")
    
    def _handle_live_event(self, data):
        """Handle live event data"""
        try:
            # Save to database with high priority
            self._save_live_event(data)
            
        except Exception as e:
            self.logger.error(f"[ERROR] Live event handling error: {e}")
    
    def _handle_statistics(self, data):
        """Handle statistics data"""
        try:
            # Update statistics in database
            self._update_statistics(data)
            
        except Exception as e:
            self.logger.error(f"[ERROR] Statistics handling error: {e}")
    
    def _save_live_event(self, data):
        """Save live event to database"""
        # Implementation for saving live events
        pass
    
    def _update_statistics(self, data):
        """Update statistics in database"""
        # Implementation for updating statistics
        pass


class BackgroundSaver:
    """
    Background saver dengan smart batching
    """
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
        
        # Save queues
        self.save_queue = deque()
        self.batch_size = 50
        self.save_interval = 5  # seconds
        
        # Thread state
        self.is_running = False
        self.save_thread = None
        self.lock = threading.Lock()
    
    def start_background_thread(self):
        """Start background save thread"""
        if self.is_running:
            return
        
        self.is_running = True
        self.save_thread = threading.Thread(target=self._save_loop, daemon=True)
        self.save_thread.start()
        
        self.logger.info("[SAVE] Background save thread started")
    
    def stop_background_thread(self):
        """Stop background save thread"""
        self.is_running = False
        if self.save_thread and self.save_thread.is_alive():
            self.save_thread.join(timeout=3)
        self.logger.info("[SAVE] Background save thread stopped")
    
    def add_to_save_queue(self, data):
        """Add data to save queue"""
        with self.lock:
            self.save_queue.append({
                'data': data,
                'timestamp': time.time()
            })
    
    def _save_loop(self):
        """Background save loop"""
        while self.is_running:
            try:
                if len(self.save_queue) >= self.batch_size:
                    self._process_save_batch()
                else:
                    time.sleep(self.save_interval)
                    if self.save_queue:  # Save remaining items
                        self._process_save_batch()
                        
            except Exception as e:
                self.logger.error(f"[ERROR] Background save error: {e}")
                time.sleep(1)
    
    def _process_save_batch(self):
        """Process a batch of save operations"""
        try:
            with self.lock:
                if not self.save_queue:
                    return
                
                # Get batch items
                batch_items = []
                for _ in range(min(self.batch_size, len(self.save_queue))):
                    if self.save_queue:
                        batch_items.append(self.save_queue.popleft())
            
            if not batch_items:
                return
            
            # Save batch to database
            self._save_batch_to_db(batch_items)
            
        except Exception as e:
            self.logger.error(f"[ERROR] Save batch processing error: {e}")
    
    def _save_batch_to_db(self, batch_items):
        """Save batch items to database"""
        try:
            with self.db_manager.get_connection() as conn:
                for item in batch_items:
                    # Process each save item
                    data = item['data']
                    # Implementation for saving different types of data
                    pass
        except Exception as e:
            self.logger.error(f"[ERROR] Batch save to database error: {e}")


class AutoArchiveScheduler:
    """
    Auto-archive scheduler untuk 3-month retention
    """
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
        
        # Archive settings
        self.retention_days = 90  # 3 months
        self.check_interval = 24 * 60 * 60  # 24 hours
        
        # Thread state
        self.is_running = False
        self.archive_thread = None
        
    def start_scheduler(self):
        """Start archive scheduler"""
        if self.is_running:
            return
        
        self.is_running = True
        self.archive_thread = threading.Thread(target=self._archive_loop, daemon=True)
        self.archive_thread.start()
        
        self.logger.info("[ARCHIVE] Auto-archive scheduler started")
    
    def stop_scheduler(self):
        """Stop archive scheduler"""
        self.is_running = False
        if self.archive_thread and self.archive_thread.is_alive():
            self.archive_thread.join(timeout=2)
    
    def _archive_loop(self):
        """Archive loop that runs daily"""
        while self.is_running:
            try:
                # Check and archive old data
                self._check_and_archive()
                
                # Sleep for check interval (24 hours)
                time.sleep(self.check_interval)
                
            except Exception as e:
                self.logger.error(f"[ERROR] Archive scheduler error: {e}")
                time.sleep(3600)  # Sleep 1 hour on error
    
    def _check_and_archive(self):
        """Check for old data and archive it"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            
            # Find sessions older than retention period
            old_sessions = self._find_old_sessions(cutoff_date)
            
            if old_sessions:
                archive_filename = self._create_archive(old_sessions, cutoff_date)
                self._delete_old_data(old_sessions)
                self.logger.info(f"[OK] Archive complete: {archive_filename}")
            
        except Exception as e:
            self.logger.error(f"[ERROR] Archive check error: {e}")
    
    def _find_old_sessions(self, cutoff_date):
        """Find sessions older than cutoff date"""
        try:
            query = """
            SELECT session_id, account_username, start_time, end_time
            FROM sessions 
            WHERE start_time < ?
            ORDER BY start_time
            """
            
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute(query, (cutoff_date.isoformat(),))
                return cursor.fetchall()
                
        except Exception as e:
            self.logger.error(f"[ERROR] Finding old sessions error: {e}")
            return []
    
    def _create_archive(self, sessions, cutoff_date):
        """Create archive file for old sessions"""
        try:
            archive_dir = Path("archives")
            archive_dir.mkdir(exist_ok=True)
            
            archive_filename = f"archive_{cutoff_date.strftime('%Y%m%d')}.json"
            archive_path = archive_dir / archive_filename
            
            # Create archive data
            archive_data = {
                'archive_date': datetime.now().isoformat(),
                'cutoff_date': cutoff_date.isoformat(),
                'sessions': []
            }
            
            for session in sessions:
                session_data = self._get_session_archive_data(session[0])
                archive_data['sessions'].append(session_data)
            
            # Save archive
            with open(archive_path, 'w', encoding='utf-8') as f:
                json.dump(archive_data, f, indent=2, ensure_ascii=False)
            
            return archive_filename
            
        except Exception as e:
            self.logger.error(f"[ERROR] Creating archive error: {e}")
            return None
    
    def _get_session_archive_data(self, session_id):
        """Get complete session data for archiving"""
        try:
            with self.db_manager.get_connection() as conn:
                # Get session info
                session_query = "SELECT * FROM sessions WHERE session_id = ?"
                session_data = conn.execute(session_query, (session_id,)).fetchone()
                
                # Get live events
                events_query = "SELECT * FROM live_events WHERE session_id = ?"
                events_data = conn.execute(events_query, (session_id,)).fetchall()
                
                # Get statistics
                stats_query = "SELECT * FROM live_statistics WHERE session_id = ?"
                stats_data = conn.execute(stats_query, (session_id,)).fetchall()
                
                return {
                    'session': dict(session_data) if session_data else None,
                    'events': [dict(row) for row in events_data],
                    'statistics': [dict(row) for row in stats_data]
                }
                
        except Exception as e:
            self.logger.error(f"[ERROR] Getting session archive data error: {e}")
            return {}
    
    def _delete_old_data(self, sessions):
        """Delete old data from database"""
        try:
            session_ids = [session[0] for session in sessions]
            
            with self.db_manager.get_connection() as conn:
                # Delete in correct order due to foreign keys
                for session_id in session_ids:
                    conn.execute("DELETE FROM live_events WHERE session_id = ?", (session_id,))
                    conn.execute("DELETE FROM live_statistics WHERE session_id = ?", (session_id,))
                    conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"[ERROR] Deleting old data error: {e}")


class SmartSessionContinuation:
    """
    Smart session continuation berdasarkan Room ID detection
    """
    
    def __init__(self, unified_manager):
        self.unified_manager = unified_manager
        self.logger = logging.getLogger(__name__)
        
        # Room ID tracking
        self.room_id_pattern = r'room_id["\']?\s*:\s*["\']?(\d+)'
        self.last_room_ids = deque(maxlen=10)  # Track last 10 room IDs
        
    def detect_room_id(self, live_data):
        """Detect room ID from live data"""
        try:
            if isinstance(live_data, dict):
                # Direct room_id field
                if 'room_id' in live_data:
                    return str(live_data['room_id'])
                
                # Nested in live_room or similar
                if 'live_room' in live_data and 'room_id' in live_data['live_room']:
                    return str(live_data['live_room']['room_id'])
            
            # String pattern matching
            if isinstance(live_data, str):
                import re
                match = re.search(self.room_id_pattern, live_data)
                if match:
                    return match.group(1)
            
            return None
            
        except Exception as e:
            self.logger.error(f"[ERROR] Room ID detection error: {e}")
            return None
    
    def should_continue_session(self, room_id):
        """Check if we should continue existing session for this room ID"""
        try:
            if not room_id:
                return False
            
            # Check if we have an active session for this room ID
            if room_id in self.unified_manager.room_id_sessions:
                session_info = self.unified_manager.room_id_sessions[room_id]
                
                # Check if session is still recent (within last 30 minutes)
                if session_info.get('last_activity'):
                    last_activity = datetime.fromisoformat(session_info['last_activity'])
                    if datetime.now() - last_activity < timedelta(minutes=30):
                        return True
            
            # Check if this room ID was recently seen
            if room_id in self.last_room_ids:
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"[ERROR] Session continuation check error: {e}")
            return False
    
    def continue_session(self, room_id):
        """Continue existing session for room ID"""
        try:
            if room_id not in self.unified_manager.room_id_sessions:
                return False
            
            session_info = self.unified_manager.room_id_sessions[room_id]
            session_id = session_info['session_id']
            
            # Update session as current
            self.unified_manager.current_session = self.unified_manager.sessions.get(session_id)
            
            # Update last activity
            session_info['last_activity'] = datetime.now().isoformat()
            
            self.logger.info(f"[RELOAD] Auto-connect: CONTINUATION {session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"[ERROR] Session continuation error: {e}")
            return False


class SessionData:
    """
    Session data container dengan optimasi memory
    """
    
    def __init__(self, session_id, account_username, room_id=None):
        self.session_id = session_id
        self.account_username = account_username
        self.room_id = room_id
        
        # Timestamps
        self.start_time = datetime.now()
        self.end_time = None
        self.last_activity = datetime.now()
        
        # State
        self.is_active = True
        self.is_connected = False
        
        # Data containers (with size limits for memory optimization)
        self.live_events = deque(maxlen=1000)  # Keep last 1000 events
        self.recent_stats = deque(maxlen=100)  # Keep last 100 stat updates
        
        # Summary data
        self.summary_stats = {
            'total_viewers': 0,
            'max_viewers': 0,
            'total_gifts': 0,
            'total_comments': 0,
            'total_likes': 0,
            'session_duration': 0
        }
    
    def add_event(self, event_data):
        """Add event with memory optimization"""
        try:
            event_data['timestamp'] = datetime.now().isoformat()
            self.live_events.append(event_data)
            self.last_activity = datetime.now()
            
            # Update summary stats
            self._update_summary_stats(event_data)
            
        except Exception as e:
            logging.getLogger(__name__).error(f"[ERROR] Adding event error: {e}")
    
    def _update_summary_stats(self, event_data):
        """Update summary statistics"""
        try:
            event_type = event_data.get('type', '')
            
            if event_type == 'viewer_count':
                viewer_count = event_data.get('viewer_count', 0)
                self.summary_stats['total_viewers'] = viewer_count
                self.summary_stats['max_viewers'] = max(
                    self.summary_stats['max_viewers'], 
                    viewer_count
                )
            
            elif event_type == 'gift':
                self.summary_stats['total_gifts'] += 1
            
            elif event_type == 'comment':
                self.summary_stats['total_comments'] += 1
            
            elif event_type == 'like':
                self.summary_stats['total_likes'] += 1
            
            # Update session duration
            if self.start_time:
                duration = datetime.now() - self.start_time
                self.summary_stats['session_duration'] = duration.total_seconds()
                
        except Exception as e:
            logging.getLogger(__name__).error(f"[ERROR] Updating summary stats error: {e}")
    
    def get_summary(self):
        """Get session summary"""
        return {
            'session_id': self.session_id,
            'account_username': self.account_username,
            'room_id': self.room_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'is_active': self.is_active,
            'is_connected': self.is_connected,
            'stats': self.summary_stats.copy(),
            'event_count': len(self.live_events)
        }
