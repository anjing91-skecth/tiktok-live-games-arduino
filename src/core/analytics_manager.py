#!/usr/bin/env python3
"""
Analytics Manager - Comprehensive TikTok Live Analytics System
==============================================================
Sistem analytics lengkap untuk tracking:
1. Session analytics dengan interval 5 menit
2. Leaderboard top gift contributors 
3. Viewer correlation analysis
4. Data compression dan aggregation
5. Export ke Excel dengan multiple sheets
6. Auto-cleanup dan retention management
"""

import asyncio
import sqlite3
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import logging
from pathlib import Path
import psutil
import threading
import time
import time

@dataclass
class SessionMetrics:
    """Data class untuk session metrics"""
    timestamp: datetime
    session_id: str
    account_username: str
    viewers: int
    comments_count: int
    likes_count: int
    gifts_count: int
    gifts_value: float
    follows_count: int
    shares_count: int
    top_gifter: Optional[str] = None
    viewer_change: int = 0
    activity_score: float = 0.0

@dataclass
class GiftContribution:
    """Data class untuk gift contributions"""
    user_id: str
    username: str
    nickname: str
    total_gifts: int
    total_value: float
    gift_types: Dict[str, int]
    last_gift_time: datetime
    session_id: str

@dataclass
class ViewerCorrelation:
    """Data class untuk viewer correlation analysis"""
    timestamp: datetime
    session_id: str
    viewer_change: int
    comments_spike: bool
    likes_spike: bool
    gifts_spike: bool
    follows_spike: bool
    shares_spike: bool
    correlation_score: float

class PerformanceMonitor:
    """Monitor performa sistem untuk auto-adjustment"""
    
    def __init__(self):
        self.cpu_threshold = 80.0  # CPU usage threshold
        self.memory_threshold = 85.0  # Memory usage threshold
        self.disk_threshold = 90.0  # Disk usage threshold
        
    def get_system_performance(self) -> Dict[str, float]:
        """Get current system performance metrics"""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent if hasattr(psutil.disk_usage('/'), 'percent') else 0
        }
    
    def should_reduce_frequency(self) -> bool:
        """Check if we should reduce analytics frequency due to performance"""
        perf = self.get_system_performance()
        return (perf['cpu_percent'] > self.cpu_threshold or 
                perf['memory_percent'] > self.memory_threshold)
    
    def get_recommended_interval(self) -> int:
        """Get recommended analytics interval based on performance"""
        if self.should_reduce_frequency():
            return 600  # 10 minutes for low-end systems
        return 300  # 5 minutes for normal systems

class AnalyticsManager:
    """Main Analytics Manager class"""
    
    def __init__(self, db_path: str = "database/analytics.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        self.performance_monitor = PerformanceMonitor()
        
        # Analytics settings
        self.analytics_interval = 300  # 5 minutes default
        self.retention_days = 90  # 3 months
        self.leaderboard_size = 10  # Top 10 contributors
        
        # Real-time tracking
        self.current_session_id: Optional[str] = None
        self.session_start_time: Optional[datetime] = None
        self.is_tracking = False
        self.analytics_running = False  # For thread-based analytics loop
        
        # Temporary data storage for current interval
        self.current_metrics = {
            'viewers': [],
            'comments': 0,
            'likes': 0,
            'gifts': 0,
            'gifts_value': 0.0,
            'follows': 0,
            'shares': 0,
            'gift_contributors': {},
            'activities': []
        }
        
        # Initialize database
        self.init_database()
        
        # Background task
        self.analytics_task: Optional[asyncio.Task] = None
        
    def init_database(self):
        """Initialize analytics database with all required tables"""
        with sqlite3.connect(self.db_path) as conn:
            # Sessions table - basic session info
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    account_username TEXT NOT NULL,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    total_duration INTEGER,
                    peak_viewers INTEGER DEFAULT 0,
                    total_comments INTEGER DEFAULT 0,
                    total_likes INTEGER DEFAULT 0,
                    total_gifts INTEGER DEFAULT 0,
                    total_gifts_value REAL DEFAULT 0.0,
                    total_follows INTEGER DEFAULT 0,
                    total_shares INTEGER DEFAULT 0,
                    avg_viewers REAL DEFAULT 0.0,
                    session_notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Session analytics - interval data (5 menit)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS session_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    viewers INTEGER NOT NULL,
                    comments_count INTEGER DEFAULT 0,
                    likes_count INTEGER DEFAULT 0,
                    gifts_count INTEGER DEFAULT 0,
                    gifts_value REAL DEFAULT 0.0,
                    follows_count INTEGER DEFAULT 0,
                    shares_count INTEGER DEFAULT 0,
                    viewer_change INTEGER DEFAULT 0,
                    activity_score REAL DEFAULT 0.0,
                    top_gifter TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions (session_id)
                )
            """)
            
            # Gift contributions - leaderboard data
            conn.execute("""
                CREATE TABLE IF NOT EXISTS gift_contributions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    username TEXT NOT NULL,
                    nickname TEXT NOT NULL,
                    total_gifts INTEGER DEFAULT 0,
                    total_value REAL DEFAULT 0.0,
                    gift_types TEXT,  -- JSON string
                    last_gift_time TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions (session_id),
                    UNIQUE(session_id, user_id)
                )
            """)
            
            # Viewer correlation analysis
            conn.execute("""
                CREATE TABLE IF NOT EXISTS viewer_correlations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    viewer_change INTEGER NOT NULL,
                    comments_spike BOOLEAN DEFAULT 0,
                    likes_spike BOOLEAN DEFAULT 0,
                    gifts_spike BOOLEAN DEFAULT 0,
                    follows_spike BOOLEAN DEFAULT 0,
                    shares_spike BOOLEAN DEFAULT 0,
                    correlation_score REAL DEFAULT 0.0,
                    analysis_notes TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions (session_id)
                )
            """)
            
            # Gift values reference table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS gift_values (
                    gift_id TEXT PRIMARY KEY,
                    gift_name TEXT NOT NULL,
                    diamond_value INTEGER NOT NULL,
                    coin_value REAL NOT NULL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Performance logs
            conn.execute("""
                CREATE TABLE IF NOT EXISTS performance_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    cpu_percent REAL,
                    memory_percent REAL,
                    disk_percent REAL,
                    analytics_interval INTEGER,
                    data_size_mb REAL
                )
            """)
            
            # Create indexes for better performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_session_analytics_timestamp ON session_analytics(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_session_analytics_session ON session_analytics(session_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_gift_contributions_session ON gift_contributions(session_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_gift_contributions_value ON gift_contributions(total_value DESC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_viewer_correlations_session ON viewer_correlations(session_id)")
            
            conn.commit()
    
    def start_session(self, session_id: str, account_username: str) -> bool:
        """Start new analytics session"""
        try:
            self.current_session_id = session_id
            self.session_start_time = datetime.now()
            self.is_tracking = True
            
            # Reset current metrics
            self.current_metrics = {
                'viewers': [],
                'comments': 0,
                'likes': 0,
                'gifts': 0,
                'gifts_value': 0.0,
                'follows': 0,
                'shares': 0,
                'gift_contributors': {},
                'activities': []
            }
            
            # Insert session record
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO sessions (session_id, account_username, start_time)
                    VALUES (?, ?, ?)
                """, (session_id, account_username, self.session_start_time))
                conn.commit()
            
            # Start background analytics task in a thread instead of asyncio
            self.analytics_running = True
            analytics_thread = threading.Thread(target=self._analytics_thread_loop, daemon=True)
            analytics_thread.start()
            
            self.logger.info(f"Analytics session started: {session_id} for @{account_username}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting analytics session: {e}")
            return False
    
    def stop_session(self) -> bool:
        """Stop current analytics session"""
        try:
            if not self.current_session_id:
                return True
                
            # Stop analytics thread
            self.analytics_running = False
            self.is_tracking = False
                
            # Cancel background task if it exists
            if hasattr(self, 'analytics_task') and self.analytics_task and not self.analytics_task.done():
                self.analytics_task.cancel()
            
            # Final metrics save
            self._save_interval_metrics()
            
            # Update session end time and stats
            end_time = datetime.now()
            if self.session_start_time:
                duration = int((end_time - self.session_start_time).total_seconds())
            else:
                duration = 0
            
            with sqlite3.connect(self.db_path) as conn:
                # Calculate session statistics
                stats = self._calculate_session_stats(self.current_session_id)
                
                conn.execute("""
                    UPDATE sessions SET
                        end_time = ?,
                        total_duration = ?,
                        peak_viewers = ?,
                        total_comments = ?,
                        total_likes = ?,
                        total_gifts = ?,
                        total_gifts_value = ?,
                        total_follows = ?,
                        total_shares = ?,
                        avg_viewers = ?
                    WHERE session_id = ?
                """, (
                    end_time,
                    duration,
                    stats['peak_viewers'],
                    stats['total_comments'],
                    stats['total_likes'],
                    stats['total_gifts'],
                    stats['total_gifts_value'],
                    stats['total_follows'],
                    stats['total_shares'],
                    stats['avg_viewers'],
                    self.current_session_id
                ))
                conn.commit()
            
            self.logger.info(f"Analytics session stopped: {self.current_session_id}")
            
            # Reset tracking state
            self.current_session_id = None
            self.session_start_time = None
            self.is_tracking = False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping analytics session: {e}")
            return False
    
    def track_event(self, event_type: str, event_data: Dict[str, Any]):
        """Track real-time events for analytics"""
        if not self.is_tracking:
            return
            
        try:
            timestamp = datetime.now()
            
            if event_type == "viewer_update":
                self.current_metrics['viewers'].append({
                    'timestamp': timestamp,
                    'count': event_data.get('count', 0)
                })
                
            elif event_type == "comment":
                self.current_metrics['comments'] += 1
                self.current_metrics['activities'].append({
                    'type': 'comment',
                    'timestamp': timestamp,
                    'user': event_data.get('username', 'Unknown')
                })
                
            elif event_type == "like":
                like_count = event_data.get('count', 1)
                self.current_metrics['likes'] += like_count
                self.current_metrics['activities'].append({
                    'type': 'like',
                    'timestamp': timestamp,
                    'count': like_count,
                    'user': event_data.get('username', 'Unknown')
                })
                
            elif event_type == "gift":
                gift_name = event_data.get('gift_name', 'Unknown')
                gift_value = self._get_gift_value(gift_name)
                repeat_count = event_data.get('repeat_count', 1)
                total_value = gift_value * repeat_count
                
                self.current_metrics['gifts'] += repeat_count
                self.current_metrics['gifts_value'] += total_value
                
                # Track gift contributor
                user_id = event_data.get('user_id', '')
                username = event_data.get('username', 'Unknown')
                nickname = event_data.get('nickname', username)
                
                if user_id not in self.current_metrics['gift_contributors']:
                    self.current_metrics['gift_contributors'][user_id] = {
                        'username': username,
                        'nickname': nickname,
                        'total_gifts': 0,
                        'total_value': 0.0,
                        'gift_types': {},
                        'last_gift_time': timestamp
                    }
                
                contributor = self.current_metrics['gift_contributors'][user_id]
                contributor['total_gifts'] += repeat_count
                contributor['total_value'] += total_value
                contributor['gift_types'][gift_name] = contributor['gift_types'].get(gift_name, 0) + repeat_count
                contributor['last_gift_time'] = timestamp
                
                self.current_metrics['activities'].append({
                    'type': 'gift',
                    'timestamp': timestamp,
                    'gift_name': gift_name,
                    'value': total_value,
                    'count': repeat_count,
                    'user': username
                })
                
            elif event_type == "follow":
                self.current_metrics['follows'] += 1
                self.current_metrics['activities'].append({
                    'type': 'follow',
                    'timestamp': timestamp,
                    'user': event_data.get('username', 'Unknown')
                })
                
            elif event_type == "share":
                self.current_metrics['shares'] += 1
                self.current_metrics['activities'].append({
                    'type': 'share',
                    'timestamp': timestamp,
                    'user': event_data.get('username', 'Unknown')
                })
                
        except Exception as e:
            self.logger.error(f"Error tracking event {event_type}: {e}")
    
    def _get_gift_value(self, gift_name: str) -> float:
        """Get gift value in coins from database or estimate"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT coin_value FROM gift_values WHERE gift_name = ?",
                    (gift_name,)
                )
                result = cursor.fetchone()
                if result:
                    return result[0]
        except Exception:
            pass
        
        # Default values for common gifts (estimate)
        gift_values = {
            'Rose': 1.0,
            'Like': 0.1,
            'Heart': 0.5,
            'TikTok': 1.0,
            'Swan': 5.0,
            'Love Bang': 25.0,
            'Castle': 50.0,
            'Rocket': 100.0,
            'Planet': 500.0,
            'Universe': 1000.0
        }
        
        return gift_values.get(gift_name, 1.0)  # Default 1 coin
    
    def _analytics_thread_loop(self):
        """Background analytics loop using threading instead of asyncio"""
        try:
            while self.analytics_running and self.is_tracking:
                # Adjust interval based on system performance
                current_interval = self.performance_monitor.get_recommended_interval()
                
                time.sleep(current_interval)
                
                if self.is_tracking:
                    self._save_interval_metrics()
                    self._analyze_viewer_correlation()
                    self._update_gift_leaderboard()
                    self._log_performance()
                    
        except Exception as e:
            self.logger.error(f"Error in analytics loop: {e}")
    
    async def _analytics_loop(self):
        """Background analytics loop"""
        try:
            while self.is_tracking:
                # Adjust interval based on system performance
                current_interval = self.performance_monitor.get_recommended_interval()
                
                await asyncio.sleep(current_interval)
                
                if self.is_tracking:
                    self._save_interval_metrics()
                    self._analyze_viewer_correlation()
                    self._update_gift_leaderboard()
                    self._log_performance()
                    
        except asyncio.CancelledError:
            self.logger.info("Analytics loop cancelled")
        except Exception as e:
            self.logger.error(f"Error in analytics loop: {e}")
    
    def _save_interval_metrics(self):
        """Save current interval metrics to database"""
        if not self.current_session_id:
            return
            
        try:
            timestamp = datetime.now()
            
            # Calculate metrics for this interval
            current_viewers = self.current_metrics['viewers'][-1]['count'] if self.current_metrics['viewers'] else 0
            viewer_change = 0
            
            if len(self.current_metrics['viewers']) > 1:
                viewer_change = current_viewers - self.current_metrics['viewers'][-2]['count']
            
            # Calculate activity score
            activity_score = self._calculate_activity_score()
            
            # Get top gifter for this interval
            top_gifter = self._get_top_gifter()
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO session_analytics (
                        session_id, timestamp, viewers, comments_count, likes_count,
                        gifts_count, gifts_value, follows_count, shares_count,
                        viewer_change, activity_score, top_gifter
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.current_session_id,
                    timestamp,
                    current_viewers,
                    self.current_metrics['comments'],
                    self.current_metrics['likes'],
                    self.current_metrics['gifts'],
                    self.current_metrics['gifts_value'],
                    self.current_metrics['follows'],
                    self.current_metrics['shares'],
                    viewer_change,
                    activity_score,
                    top_gifter
                ))
                conn.commit()
            
            # Reset interval counters (keep cumulative data)
            self._reset_interval_counters()
            
        except Exception as e:
            self.logger.error(f"Error saving interval metrics: {e}")
    
    def _calculate_activity_score(self) -> float:
        """Calculate activity score based on all activities"""
        try:
            # Weight different activities
            weights = {
                'comment': 1.0,
                'like': 0.1,
                'gift': 5.0,
                'follow': 3.0,
                'share': 2.0
            }
            
            total_score = 0.0
            total_score += self.current_metrics['comments'] * weights['comment']
            total_score += self.current_metrics['likes'] * weights['like']
            total_score += self.current_metrics['gifts'] * weights['gift']
            total_score += self.current_metrics['follows'] * weights['follow']
            total_score += self.current_metrics['shares'] * weights['share']
            
            return total_score
            
        except Exception:
            return 0.0
    
    def _get_top_gifter(self) -> Optional[str]:
        """Get top gifter for current interval"""
        try:
            if not self.current_metrics['gift_contributors']:
                return None
            
            top_contributor = max(
                self.current_metrics['gift_contributors'].values(),
                key=lambda x: x['total_value']
            )
            
            return top_contributor['nickname']
            
        except Exception:
            return None
    
    def _analyze_viewer_correlation(self):
        """Analyze correlation between viewer changes and activities"""
        if not self.current_session_id or len(self.current_metrics['viewers']) < 2:
            return
            
        try:
            timestamp = datetime.now()
            current_viewers = self.current_metrics['viewers'][-1]['count']
            previous_viewers = self.current_metrics['viewers'][-2]['count']
            viewer_change = current_viewers - previous_viewers
            
            # Check for activity spikes (above average)
            interval_seconds = self.performance_monitor.get_recommended_interval()
            
            # Define spike thresholds based on interval
            comment_threshold = max(1, (self.current_metrics['comments'] * 60) // interval_seconds)
            like_threshold = max(5, (self.current_metrics['likes'] * 60) // interval_seconds)
            gift_threshold = max(1, (self.current_metrics['gifts'] * 60) // interval_seconds)
            
            comments_spike = self.current_metrics['comments'] > comment_threshold
            likes_spike = self.current_metrics['likes'] > like_threshold
            gifts_spike = self.current_metrics['gifts'] > gift_threshold
            follows_spike = self.current_metrics['follows'] > 0
            shares_spike = self.current_metrics['shares'] > 0
            
            # Calculate correlation score
            correlation_score = self._calculate_correlation_score(
                viewer_change, comments_spike, likes_spike, gifts_spike, follows_spike, shares_spike
            )
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO viewer_correlations (
                        session_id, timestamp, viewer_change, comments_spike,
                        likes_spike, gifts_spike, follows_spike, shares_spike,
                        correlation_score
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.current_session_id,
                    timestamp,
                    viewer_change,
                    comments_spike,
                    likes_spike,
                    gifts_spike,
                    follows_spike,
                    shares_spike,
                    correlation_score
                ))
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error analyzing viewer correlation: {e}")
    
    def _calculate_correlation_score(self, viewer_change: int, comments_spike: bool,
                                   likes_spike: bool, gifts_spike: bool,
                                   follows_spike: bool, shares_spike: bool) -> float:
        """Calculate correlation score between viewer change and activities"""
        try:
            if viewer_change == 0:
                return 0.0
            
            # Weight different activities for correlation
            spike_weights = {
                'comments': 0.3,
                'likes': 0.2,
                'gifts': 0.4,
                'follows': 0.05,
                'shares': 0.05
            }
            
            positive_correlation = 0.0
            if viewer_change > 0:
                # Positive viewer change correlation
                if comments_spike:
                    positive_correlation += spike_weights['comments']
                if likes_spike:
                    positive_correlation += spike_weights['likes']
                if gifts_spike:
                    positive_correlation += spike_weights['gifts']
                if follows_spike:
                    positive_correlation += spike_weights['follows']
                if shares_spike:
                    positive_correlation += spike_weights['shares']
                    
                return positive_correlation
            else:
                # Negative viewer change (inverse correlation)
                total_spikes = sum([comments_spike, likes_spike, gifts_spike, follows_spike, shares_spike])
                if total_spikes == 0:
                    return 1.0  # Strong correlation: no activity = viewer drop
                else:
                    return -0.5  # Unexpected: activity but viewer drop
                    
        except Exception:
            return 0.0
    
    def _update_gift_leaderboard(self):
        """Update gift contributions leaderboard"""
        if not self.current_session_id or not self.current_metrics['gift_contributors']:
            return
            
        try:
            with sqlite3.connect(self.db_path) as conn:
                for user_id, contributor in self.current_metrics['gift_contributors'].items():
                    gift_types_json = json.dumps(contributor['gift_types'])
                    
                    # Insert or update contributor
                    conn.execute("""
                        INSERT OR REPLACE INTO gift_contributions (
                            session_id, user_id, username, nickname, total_gifts,
                            total_value, gift_types, last_gift_time
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        self.current_session_id,
                        user_id,
                        contributor['username'],
                        contributor['nickname'],
                        contributor['total_gifts'],
                        contributor['total_value'],
                        gift_types_json,
                        contributor['last_gift_time']
                    ))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error updating gift leaderboard: {e}")
    
    def _reset_interval_counters(self):
        """Reset counters for next interval (keep cumulative data)"""
        # Don't reset cumulative data, only interval-specific counters
        # Keep viewers list but limit size for memory
        if len(self.current_metrics['viewers']) > 10:
            self.current_metrics['viewers'] = self.current_metrics['viewers'][-5:]
            
        # Keep activities list but limit size
        if len(self.current_metrics['activities']) > 100:
            self.current_metrics['activities'] = self.current_metrics['activities'][-50:]
    
    def _calculate_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Calculate session statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get analytics data
                cursor = conn.execute("""
                    SELECT MAX(viewers) as peak_viewers,
                           SUM(comments_count) as total_comments,
                           SUM(likes_count) as total_likes,
                           SUM(gifts_count) as total_gifts,
                           SUM(gifts_value) as total_gifts_value,
                           SUM(follows_count) as total_follows,
                           SUM(shares_count) as total_shares,
                           AVG(viewers) as avg_viewers
                    FROM session_analytics WHERE session_id = ?
                """, (session_id,))
                
                result = cursor.fetchone()
                if result:
                    return {
                        'peak_viewers': result[0] or 0,
                        'total_comments': result[1] or 0,
                        'total_likes': result[2] or 0,
                        'total_gifts': result[3] or 0,
                        'total_gifts_value': result[4] or 0.0,
                        'total_follows': result[5] or 0,
                        'total_shares': result[6] or 0,
                        'avg_viewers': result[7] or 0.0
                    }
                    
        except Exception as e:
            self.logger.error(f"Error calculating session stats: {e}")
            
        return {
            'peak_viewers': 0,
            'total_comments': 0,
            'total_likes': 0,
            'total_gifts': 0,
            'total_gifts_value': 0.0,
            'total_follows': 0,
            'total_shares': 0,
            'avg_viewers': 0.0
        }
    
    def _log_performance(self):
        """Log system performance metrics"""
        try:
            perf = self.performance_monitor.get_system_performance()
            current_interval = self.performance_monitor.get_recommended_interval()
            
            # Calculate database size
            db_size_mb = self.db_path.stat().st_size / (1024 * 1024) if self.db_path.exists() else 0
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO performance_logs (
                        cpu_percent, memory_percent, disk_percent,
                        analytics_interval, data_size_mb
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    perf['cpu_percent'],
                    perf['memory_percent'],
                    perf['disk_percent'],
                    current_interval,
                    db_size_mb
                ))
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error logging performance: {e}")
    
    def get_session_leaderboard(self, session_id: str, limit: int = 10) -> List[GiftContribution]:
        """Get gift leaderboard for specific session"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT user_id, username, nickname, total_gifts, total_value,
                           gift_types, last_gift_time, session_id
                    FROM gift_contributions
                    WHERE session_id = ?
                    ORDER BY total_value DESC
                    LIMIT ?
                """, (session_id, limit))
                
                leaderboard = []
                for row in cursor.fetchall():
                    gift_types = json.loads(row[5]) if row[5] else {}
                    leaderboard.append(GiftContribution(
                        user_id=row[0],
                        username=row[1],
                        nickname=row[2],
                        total_gifts=row[3],
                        total_value=row[4],
                        gift_types=gift_types,
                        last_gift_time=datetime.fromisoformat(row[6]) if row[6] else None,
                        session_id=row[7]
                    ))
                
                return leaderboard
                
        except Exception as e:
            self.logger.error(f"Error getting session leaderboard: {e}")
            return []
    
    def get_global_leaderboard(self, days: int = 30, limit: int = 10) -> List[Dict[str, Any]]:
        """Get global gift leaderboard across multiple sessions"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT gc.username, gc.nickname,
                           SUM(gc.total_gifts) as total_gifts,
                           SUM(gc.total_value) as total_value,
                           COUNT(DISTINCT gc.session_id) as sessions_participated,
                           MAX(gc.last_gift_time) as last_gift_time
                    FROM gift_contributions gc
                    JOIN sessions s ON gc.session_id = s.session_id
                    WHERE s.start_time >= ?
                    GROUP BY gc.username, gc.nickname
                    ORDER BY total_value DESC
                    LIMIT ?
                """, (cutoff_date, limit))
                
                global_leaderboard = []
                for i, row in enumerate(cursor.fetchall(), 1):
                    global_leaderboard.append({
                        'rank': i,
                        'username': row[0],
                        'nickname': row[1],
                        'total_gifts': row[2],
                        'total_value': row[3],
                        'sessions_participated': row[4],
                        'last_gift_time': row[5]
                    })
                
                return global_leaderboard
                
        except Exception as e:
            self.logger.error(f"Error getting global leaderboard: {e}")
            return []
    
    def export_to_excel(self, output_path: str, date_range: Optional[Tuple[datetime, datetime]] = None) -> bool:
        """Export analytics data to Excel with multiple sheets"""
        try:
            if date_range:
                start_date, end_date = date_range
            else:
                # Default: last 30 days
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
            
            with sqlite3.connect(self.db_path) as conn:
                # Sessions data
                sessions_df = pd.read_sql_query("""
                    SELECT * FROM sessions
                    WHERE start_time BETWEEN ? AND ?
                    ORDER BY start_time DESC
                """, conn, params=(start_date, end_date))
                
                # Analytics data
                analytics_df = pd.read_sql_query("""
                    SELECT sa.*, s.account_username
                    FROM session_analytics sa
                    JOIN sessions s ON sa.session_id = s.session_id
                    WHERE sa.timestamp BETWEEN ? AND ?
                    ORDER BY sa.timestamp DESC
                """, conn, params=(start_date, end_date))
                
                # Gift contributions
                contributions_df = pd.read_sql_query("""
                    SELECT gc.*, s.account_username, s.start_time as session_start
                    FROM gift_contributions gc
                    JOIN sessions s ON gc.session_id = s.session_id
                    WHERE s.start_time BETWEEN ? AND ?
                    ORDER BY gc.total_value DESC
                """, conn, params=(start_date, end_date))
                
                # Viewer correlations
                correlations_df = pd.read_sql_query("""
                    SELECT vc.*, s.account_username
                    FROM viewer_correlations vc
                    JOIN sessions s ON vc.session_id = s.session_id
                    WHERE vc.timestamp BETWEEN ? AND ?
                    ORDER BY vc.timestamp DESC
                """, conn, params=(start_date, end_date))
                
                # Global leaderboard
                global_leaderboard = self.get_global_leaderboard(days=30, limit=50)
                leaderboard_df = pd.DataFrame(global_leaderboard)
            
            # Write to Excel with multiple sheets
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                sessions_df.to_excel(writer, sheet_name='Sessions', index=False)
                analytics_df.to_excel(writer, sheet_name='Analytics_5min', index=False)
                contributions_df.to_excel(writer, sheet_name='Gift_Contributions', index=False)
                correlations_df.to_excel(writer, sheet_name='Viewer_Correlations', index=False)
                leaderboard_df.to_excel(writer, sheet_name='Global_Leaderboard', index=False)
                
                # Add summary sheet
                summary_data = self._generate_summary_stats(start_date, end_date)
                summary_df = pd.DataFrame([summary_data])
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            self.logger.info(f"Analytics data exported to: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting to Excel: {e}")
            return False
    
    def _generate_summary_stats(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate summary statistics for export"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT 
                        COUNT(*) as total_sessions,
                        SUM(total_duration) as total_streaming_time,
                        AVG(total_duration) as avg_session_duration,
                        MAX(peak_viewers) as max_viewers_ever,
                        AVG(peak_viewers) as avg_peak_viewers,
                        SUM(total_gifts) as total_gifts_received,
                        SUM(total_gifts_value) as total_gift_value,
                        SUM(total_comments) as total_comments,
                        SUM(total_likes) as total_likes,
                        SUM(total_follows) as total_follows
                    FROM sessions
                    WHERE start_time BETWEEN ? AND ?
                """, (start_date, end_date))
                
                result = cursor.fetchone()
                
                # Get top gifter
                cursor = conn.execute("""
                    SELECT username, nickname, SUM(total_value) as total_value
                    FROM gift_contributions gc
                    JOIN sessions s ON gc.session_id = s.session_id
                    WHERE s.start_time BETWEEN ? AND ?
                    GROUP BY username, nickname
                    ORDER BY total_value DESC
                    LIMIT 1
                """, (start_date, end_date))
                
                top_gifter = cursor.fetchone()
                
                return {
                    'period_start': start_date.strftime('%Y-%m-%d'),
                    'period_end': end_date.strftime('%Y-%m-%d'),
                    'total_sessions': result[0] or 0,
                    'total_streaming_hours': round((result[1] or 0) / 3600, 2),
                    'avg_session_minutes': round((result[2] or 0) / 60, 2),
                    'max_viewers_achieved': result[3] or 0,
                    'avg_peak_viewers': round(result[4] or 0, 2),
                    'total_gifts_received': result[5] or 0,
                    'total_gift_value_coins': round(result[6] or 0, 2),
                    'total_comments': result[7] or 0,
                    'total_likes': result[8] or 0,
                    'total_follows': result[9] or 0,
                    'top_gifter_username': top_gifter[0] if top_gifter else 'None',
                    'top_gifter_nickname': top_gifter[1] if top_gifter else 'None',
                    'top_gifter_value': round(top_gifter[2], 2) if top_gifter else 0
                }
                
        except Exception as e:
            self.logger.error(f"Error generating summary stats: {e}")
            return {}
    
    def cleanup_old_data(self, retention_days: int = None) -> bool:
        """Clean up old analytics data"""
        try:
            if retention_days is None:
                retention_days = self.retention_days
                
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            with sqlite3.connect(self.db_path) as conn:
                # Before deletion, auto-export old data
                old_sessions = conn.execute("""
                    SELECT session_id FROM sessions WHERE start_time < ?
                """, (cutoff_date,)).fetchall()
                
                if old_sessions:
                    # Export old data before deletion
                    export_start = cutoff_date - timedelta(days=retention_days)
                    export_path = f"exports/analytics_archive_{cutoff_date.strftime('%Y%m%d')}.xlsx"
                    Path(export_path).parent.mkdir(exist_ok=True)
                    
                    self.export_to_excel(export_path, (export_start, cutoff_date))
                
                # Delete old data
                conn.execute("DELETE FROM viewer_correlations WHERE timestamp < ?", (cutoff_date,))
                conn.execute("DELETE FROM session_analytics WHERE timestamp < ?", (cutoff_date,))
                conn.execute("""
                    DELETE FROM gift_contributions 
                    WHERE session_id IN (
                        SELECT session_id FROM sessions WHERE start_time < ?
                    )
                """, (cutoff_date,))
                conn.execute("DELETE FROM sessions WHERE start_time < ?", (cutoff_date,))
                conn.execute("DELETE FROM performance_logs WHERE timestamp < ?", (cutoff_date,))
                
                # Vacuum database to reclaim space
                conn.execute("VACUUM")
                conn.commit()
            
            self.logger.info(f"Cleaned up data older than {retention_days} days")
            return True
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old data: {e}")
            return False

# Factory function for easy usage
def create_analytics_manager(db_path: str = "database/analytics.db") -> AnalyticsManager:
    """Create and return analytics manager instance"""
    return AnalyticsManager(db_path)
