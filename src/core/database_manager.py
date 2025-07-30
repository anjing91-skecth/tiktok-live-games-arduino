"""
Database Manager untuk TikTok Live Games
Mengelola semua operasi database SQLite
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

class DatabaseManager:
    def __init__(self, db_path: str = "database/live_games.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        return conn
    
    def initialize_database(self):
        """Initialize database and create all tables"""
        self.logger.info("Initializing database...")
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create accounts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    display_name TEXT,
                    arduino_port TEXT,
                    status TEXT DEFAULT 'inactive',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create arduino_devices table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS arduino_devices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id INTEGER,
                    device_name TEXT NOT NULL,
                    device_type TEXT NOT NULL,
                    pin_number INTEGER,
                    trigger_duration INTEGER DEFAULT 1000,
                    status TEXT DEFAULT 'active',
                    FOREIGN KEY (account_id) REFERENCES accounts (id)
                )
            ''')
            
            # Create live_sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS live_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id INTEGER,
                    session_name TEXT,
                    start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    end_time DATETIME,
                    total_coins INTEGER DEFAULT 0,
                    total_gifts INTEGER DEFAULT 0,
                    total_comments INTEGER DEFAULT 0,
                    total_likes INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'active',
                    FOREIGN KEY (account_id) REFERENCES accounts (id)
                )
            ''')
            
            # Create gift_logs table with enhanced columns
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS gift_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER,
                    username TEXT NOT NULL,
                    gift_name TEXT NOT NULL,
                    gift_value INTEGER NOT NULL,
                    repeat_count INTEGER DEFAULT 1,
                    total_value INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    action_triggered TEXT,
                    FOREIGN KEY (session_id) REFERENCES live_sessions (id)
                )
            ''')
            
            # Add new columns to existing gift_logs table if they don't exist
            try:
                cursor.execute('ALTER TABLE gift_logs ADD COLUMN repeat_count INTEGER DEFAULT 1')
            except sqlite3.OperationalError:
                pass  # Column already exists
                
            try:
                cursor.execute('ALTER TABLE gift_logs ADD COLUMN total_value INTEGER')
            except sqlite3.OperationalError:
                pass  # Column already exists
                
            # Update existing records to calculate total_value
            cursor.execute('''
                UPDATE gift_logs 
                SET total_value = gift_value * COALESCE(repeat_count, 1)
                WHERE total_value IS NULL
            ''')
            
            # Create user_leaderboard table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_leaderboard (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER,
                    username TEXT NOT NULL,
                    total_coins INTEGER DEFAULT 0,
                    gift_count INTEGER DEFAULT 0,
                    rank_position INTEGER,
                    FOREIGN KEY (session_id) REFERENCES live_sessions (id)
                )
            ''')
            
            # Create comment_logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS comment_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER,
                    username TEXT NOT NULL,
                    comment_text TEXT NOT NULL,
                    keyword_matched TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    action_triggered TEXT,
                    FOREIGN KEY (session_id) REFERENCES live_sessions (id)
                )
            ''')
            
            # Create like_tracking table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS like_tracking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER,
                    current_like_count INTEGER DEFAULT 0,
                    like_threshold INTEGER DEFAULT 100,
                    last_trigger_count INTEGER DEFAULT 0,
                    next_threshold INTEGER DEFAULT 100,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES live_sessions (id)
                )
            ''')
            
            # Create keyword_actions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS keyword_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id INTEGER,
                    keyword TEXT NOT NULL,
                    match_type TEXT DEFAULT 'contains',
                    action_type TEXT NOT NULL,
                    device_target TEXT NOT NULL,
                    cooldown_seconds INTEGER DEFAULT 30,
                    is_active BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (account_id) REFERENCES accounts (id)
                )
            ''')
            
            # Create gift_actions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS gift_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id INTEGER,
                    gift_name TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    device_target TEXT NOT NULL,
                    trigger_value INTEGER DEFAULT 1,
                    is_active BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (account_id) REFERENCES accounts (id)
                )
            ''')
            
            # Create automation_scripts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS automation_scripts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id INTEGER,
                    script_name TEXT NOT NULL,
                    trigger_type TEXT NOT NULL,
                    trigger_condition TEXT NOT NULL,
                    trigger_value TEXT NOT NULL,
                    action_sequence TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (account_id) REFERENCES accounts (id)
                )
            ''')
            
            # Create sessions table for unified session manager
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    account_username TEXT NOT NULL,
                    room_id TEXT,
                    start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    end_time DATETIME,
                    is_active BOOLEAN DEFAULT 1,
                    last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
                    total_viewers INTEGER DEFAULT 0,
                    max_viewers INTEGER DEFAULT 0,
                    total_gifts INTEGER DEFAULT 0,
                    total_comments INTEGER DEFAULT 0,
                    total_likes INTEGER DEFAULT 0,
                    session_data TEXT
                )
            ''')
            
            # Create live_events table for unified session manager
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS live_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    username TEXT,
                    data TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions (session_id)
                )
            ''')
            
            conn.commit()
            self.logger.info("Database tables created successfully")
    
    # Account Management
    def create_account(self, username: str, display_name: str = None, arduino_port: str = None) -> int:
        """Create new TikTok account"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO accounts (username, display_name, arduino_port)
                VALUES (?, ?, ?)
            ''', (username, display_name, arduino_port))
            conn.commit()
            return cursor.lastrowid
    
    def get_accounts(self) -> List[Dict]:
        """Get all accounts"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM accounts ORDER BY created_at DESC')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_all_accounts(self) -> List[Dict]:
        """Alias for get_accounts - Get all accounts"""
        return self.get_accounts()
    
    def update_account(self, account_id: int, username: str, display_name: str, arduino_port: str, status: str = 'active'):
        """Update existing account"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE accounts 
                SET username = ?, display_name = ?, arduino_port = ?, status = ?
                WHERE id = ?
            ''', (username, display_name, arduino_port, status, account_id))
            conn.commit()
    
    def delete_account(self, account_id: int):
        """Delete account and all associated data"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get sessions to delete associated data
            cursor.execute('SELECT id FROM live_sessions WHERE account_id = ?', (account_id,))
            sessions = cursor.fetchall()
            
            # Delete session-related data
            for session in sessions:
                session_id = session[0]
                cursor.execute('DELETE FROM gift_logs WHERE session_id = ?', (session_id,))
                cursor.execute('DELETE FROM comment_logs WHERE session_id = ?', (session_id,))
                cursor.execute('DELETE FROM like_tracking WHERE session_id = ?', (session_id,))
                cursor.execute('DELETE FROM user_leaderboard WHERE session_id = ?', (session_id,))
            
            # Delete sessions
            cursor.execute('DELETE FROM live_sessions WHERE account_id = ?', (account_id,))
            
            # Delete account-related data
            cursor.execute('DELETE FROM arduino_devices WHERE account_id = ?', (account_id,))
            cursor.execute('DELETE FROM keyword_actions WHERE account_id = ?', (account_id,))
            cursor.execute('DELETE FROM gift_actions WHERE account_id = ?', (account_id,))
            cursor.execute('DELETE FROM automation_scripts WHERE account_id = ?', (account_id,))
            
            # Finally delete account
            cursor.execute('DELETE FROM accounts WHERE id = ?', (account_id,))
            
            conn.commit()
    
    def get_account(self, account_id: int) -> Optional[Dict]:
        """Get single account by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM accounts WHERE id = ?', (account_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_account_by_username(self, username: str) -> Optional[Dict]:
        """Get single account by username"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM accounts WHERE username = ?', (username,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_account_status(self, account_id: int, status: str):
        """Update account status"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE accounts SET status = ? WHERE id = ?
            ''', (status, account_id))
            conn.commit()
    
    # Session Management
    def create_live_session(self, account_id: int, session_name: str = None) -> int:
        """Create new live session"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO live_sessions (account_id, session_name)
                VALUES (?, ?)
            ''', (account_id, session_name))
            conn.commit()
            return cursor.lastrowid
    
    def end_live_session(self, session_id: int):
        """End live session"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE live_sessions 
                SET end_time = CURRENT_TIMESTAMP, status = 'completed'
                WHERE id = ?
            ''', (session_id,))
            conn.commit()
    
    def get_active_sessions(self) -> List[Dict]:
        """Get all active sessions"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT s.*, a.username, a.display_name 
                FROM live_sessions s
                JOIN accounts a ON s.account_id = a.id
                WHERE s.status = 'active'
                ORDER BY s.start_time DESC
            ''')
            return [dict(row) for row in cursor.fetchall()]
    
    # Gift Logging
    def log_gift(self, session_id: int, username: str, gift_name: str, gift_value: int, repeat_count: int = 1, action_triggered: str = None):
        """Log received gift with enhanced data support"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Calculate total value
            total_value = gift_value * repeat_count
            
            # Insert gift log with repeat count
            cursor.execute('''
                INSERT INTO gift_logs (session_id, username, gift_name, gift_value, repeat_count, total_value, action_triggered)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (session_id, username, gift_name, gift_value, repeat_count, total_value, action_triggered))
            
            # Update session totals using total value
            cursor.execute('''
                UPDATE live_sessions 
                SET total_coins = total_coins + ?, total_gifts = total_gifts + ?
                WHERE id = ?
            ''', (total_value, repeat_count, session_id))
            
            conn.commit()
            return cursor.lastrowid
    
    # Comment Logging
    def log_comment(self, session_id: int, username: str, comment_text: str, keyword_matched: str = None, action_triggered: str = None):
        """Log received comment"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO comment_logs (session_id, username, comment_text, keyword_matched, action_triggered)
                VALUES (?, ?, ?, ?, ?)
            ''', (session_id, username, comment_text, keyword_matched, action_triggered))
            conn.commit()
            return cursor.lastrowid
    
    # Like Tracking
    def update_like_tracking(self, session_id: int, current_count: int):
        """Update like tracking for session"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if like tracking record exists
            cursor.execute('''
                SELECT id, like_threshold, last_trigger_count FROM like_tracking
                WHERE session_id = ?
                ORDER BY timestamp DESC
                LIMIT 1
            ''', (session_id,))
            
            result = cursor.fetchone()
            
            if result:
                # Update existing record
                cursor.execute('''
                    UPDATE like_tracking 
                    SET current_like_count = ?, timestamp = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (current_count, result[0]))
            else:
                # Create new record
                cursor.execute('''
                    INSERT INTO like_tracking (session_id, current_like_count)
                    VALUES (?, ?)
                ''', (session_id, current_count))
            
            conn.commit()
    
    def get_like_tracking(self, session_id: int) -> Optional[Dict]:
        """Get current like tracking for session"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM like_tracking
                WHERE session_id = ?
                ORDER BY timestamp DESC
                LIMIT 1
            ''', (session_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    # Leaderboard Management
    def update_leaderboard(self, session_id: int, username: str, gift_value: int):
        """Update user leaderboard"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if user exists in leaderboard
            cursor.execute('''
                SELECT id, total_coins, gift_count FROM user_leaderboard
                WHERE session_id = ? AND username = ?
            ''', (session_id, username))
            
            result = cursor.fetchone()
            
            if result:
                # Update existing record
                cursor.execute('''
                    UPDATE user_leaderboard 
                    SET total_coins = total_coins + ?, gift_count = gift_count + 1
                    WHERE id = ?
                ''', (gift_value, result['id']))
            else:
                # Create new record
                cursor.execute('''
                    INSERT INTO user_leaderboard (session_id, username, total_coins, gift_count)
                    VALUES (?, ?, ?, 1)
                ''', (session_id, username, gift_value))
            
            conn.commit()
            
            # Update rankings
            self._update_rankings(session_id)
    
    def _update_rankings(self, session_id: int):
        """Update ranking positions for leaderboard"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id FROM user_leaderboard
                WHERE session_id = ?
                ORDER BY total_coins DESC, gift_count DESC
            ''', (session_id,))
            
            for rank, row in enumerate(cursor.fetchall(), 1):
                cursor.execute('''
                    UPDATE user_leaderboard SET rank_position = ? WHERE id = ?
                ''', (rank, row['id']))
            
            conn.commit()
    
    def get_leaderboard(self, session_id: int, limit: int = 20) -> List[Dict]:
        """Get leaderboard for session"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM user_leaderboard
                WHERE session_id = ?
                ORDER BY rank_position ASC
                LIMIT ?
            ''', (session_id, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    # Keyword Actions Management
    def add_keyword_action(self, account_id: int, keyword: str, match_type: str, action_type: str, device_target: str, cooldown_seconds: int = 30):
        """Add keyword action mapping"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO keyword_actions (account_id, keyword, match_type, action_type, device_target, cooldown_seconds)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (account_id, keyword, match_type, action_type, device_target, cooldown_seconds))
            conn.commit()
    
    def get_keyword_actions(self, account_id: int) -> List[Dict]:
        """Get keyword actions for account"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM keyword_actions
                WHERE account_id = ? AND is_active = 1
                ORDER BY keyword
            ''', (account_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    # Automation Scripts Management
    def add_automation_script(self, account_id: int, script_name: str, trigger_type: str, trigger_condition: str, trigger_value: str, action_sequence: Dict):
        """Add automation script"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO automation_scripts (account_id, script_name, trigger_type, trigger_condition, trigger_value, action_sequence)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (account_id, script_name, trigger_type, trigger_condition, trigger_value, json.dumps(action_sequence)))
            conn.commit()
    
    def get_automation_scripts(self, account_id: int) -> List[Dict]:
        """Get automation scripts for account"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM automation_scripts
                WHERE account_id = ? AND is_active = 1
                ORDER BY script_name
            ''', (account_id,))
            
            scripts = []
            for row in cursor.fetchall():
                script = dict(row)
                script['action_sequence'] = json.loads(script['action_sequence'])
                scripts.append(script)
            
            return scripts

    # Additional methods for dashboard API
    def get_session_gifts(self, session_id: int) -> List[Dict]:
        """Get all gifts for a session"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM gift_logs 
                WHERE session_id = ? 
                ORDER BY timestamp DESC
            ''', (session_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_session_comments(self, session_id: int) -> List[Dict]:
        """Get all comments for a session"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM comment_logs 
                WHERE session_id = ? 
                ORDER BY timestamp DESC
            ''', (session_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_session_leaderboard(self, session_id: int, limit: int = 20) -> List[Dict]:
        """Get leaderboard for a session"""
        return self.get_leaderboard(session_id, limit)
    
    def update_live_session(self, session_id: int, end_time=None, total_gifts=None, total_comments=None, total_likes=None):
        """Update live session data"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            updates = []
            params = []
            
            if end_time is not None:
                updates.append("end_time = ?")
                params.append(end_time.isoformat() if hasattr(end_time, 'isoformat') else end_time)
            
            if total_gifts is not None:
                updates.append("total_gifts = ?")
                params.append(total_gifts)
                
            if total_comments is not None:
                updates.append("total_comments = ?")
                params.append(total_comments)
                
            if total_likes is not None:
                updates.append("total_likes = ?")
                params.append(total_likes)
            
            if updates:
                query = f"UPDATE live_sessions SET {', '.join(updates)} WHERE id = ?"
                params.append(session_id)
                cursor.execute(query, params)
                conn.commit()
    
    def get_gift_action(self, account_id: int, gift_name: str) -> Optional[Dict]:
        """Get gift action configuration for specific gift"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM gift_actions 
                WHERE account_id = ? AND gift_name = ? AND is_active = 1
                ORDER BY created_at DESC
                LIMIT 1
            ''', (account_id, gift_name))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    # NEW: Methods for UnifiedSessionManager integration
    def save_events_batch(self, batch: List[Dict[str, Any]]):
        """Save batch of events to database (for UnifiedSessionManager)"""
        if not batch:
            return
            
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                for item in batch:
                    event_type = item['event_type']
                    event_data = item['event_data']
                    session_id = item['session_id']
                    timestamp = item['timestamp']
                    
                    if event_type == 'gift':
                        # Save gift event
                        cursor.execute('''
                            INSERT INTO gifts (session_id, username, gift_name, gift_value, 
                                             repeat_count, timestamp)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (
                            session_id,
                            event_data.get('username', 'Unknown'),
                            event_data.get('gift_name', 'Unknown'), 
                            event_data.get('estimated_value', 0),
                            event_data.get('repeat_count', 1),
                            timestamp
                        ))
                        
                    elif event_type == 'comment':
                        # Save comment event
                        cursor.execute('''
                            INSERT INTO comments (session_id, username, comment, timestamp)
                            VALUES (?, ?, ?, ?)
                        ''', (
                            session_id,
                            event_data.get('username', 'Unknown'),
                            event_data.get('comment', ''),
                            timestamp
                        ))
                        
                    elif event_type == 'like':
                        # Save like event (to comments table with special marker)
                        cursor.execute('''
                            INSERT INTO comments (session_id, username, comment, timestamp)
                            VALUES (?, ?, ?, ?)
                        ''', (
                            session_id,
                            event_data.get('username', 'Unknown'),
                            f"[LIKE] {event_data.get('count', 1)} likes",
                            timestamp
                        ))
                
                conn.commit()
                self.logger.debug(f"Saved batch of {len(batch)} events to database")
                
        except Exception as e:
            self.logger.error(f"Failed to save events batch: {e}")
    
    def get_sessions_before_date(self, cutoff_date) -> List[Dict[str, Any]]:
        """Get sessions before cutoff date (for archiving)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM live_sessions 
                    WHERE created_at < ?
                    ORDER BY created_at DESC
                ''', (cutoff_date,))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"Failed to get old sessions: {e}")
            return []
    
    def get_events_for_sessions(self, session_ids: List[str]) -> List[Dict[str, Any]]:
        """Get all events for given session IDs"""
        if not session_ids:
            return []
            
        try:
            placeholders = ','.join(['?' for _ in session_ids])
            events = []
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get gifts
                cursor.execute(f'''
                    SELECT session_id, username, gift_name, gift_value, 
                           repeat_count, timestamp, 'gift' as event_type
                    FROM gifts WHERE session_id IN ({placeholders})
                ''', session_ids)
                events.extend([dict(row) for row in cursor.fetchall()])
                
                # Get comments
                cursor.execute(f'''
                    SELECT session_id, username, comment, timestamp, 'comment' as event_type
                    FROM comments WHERE session_id IN ({placeholders})
                ''', session_ids)
                events.extend([dict(row) for row in cursor.fetchall()])
                
            return events
            
        except Exception as e:
            self.logger.error(f"Failed to get events for sessions: {e}")
            return []
    
    def delete_sessions_before_date(self, cutoff_date):
        """Delete sessions and related data before cutoff date"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get session IDs to delete
                cursor.execute('''
                    SELECT id FROM live_sessions WHERE created_at < ?
                ''', (cutoff_date,))
                session_ids = [str(row[0]) for row in cursor.fetchall()]
                
                if session_ids:
                    placeholders = ','.join(['?' for _ in session_ids])
                    
                    # Delete related data
                    cursor.execute(f'DELETE FROM gifts WHERE session_id IN ({placeholders})', session_ids)
                    cursor.execute(f'DELETE FROM comments WHERE session_id IN ({placeholders})', session_ids)
                    cursor.execute(f'DELETE FROM live_sessions WHERE id IN ({placeholders})', session_ids)
                    
                    conn.commit()
                    self.logger.info(f"Deleted {len(session_ids)} old sessions")
                
        except Exception as e:
            self.logger.error(f"Failed to delete old sessions: {e}")
