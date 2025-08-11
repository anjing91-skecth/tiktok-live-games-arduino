"""
Database Manager untuk TikTok Live Games
Mengelola semua operasi database SQLite
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

class DatabaseManager:
    def __init__(self, db_path: str = "data/tiktok_live_lite.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
        # Ensure database directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
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
            
            # Create gift_registry table for TikTok Live gifts
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS gift_registry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    gift_id TEXT UNIQUE,
                    gift_name TEXT NOT NULL,
                    diamond_count INTEGER DEFAULT 0,
                    usd_value REAL DEFAULT 0.0,
                    is_streakable BOOLEAN DEFAULT 0,
                    category TEXT DEFAULT 'general',
                    first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                    usage_count INTEGER DEFAULT 1
                )
            ''')
            
            conn.commit()
            self.logger.info("Database tables created successfully")
    
    # Account Management
    def create_account(self, username: str, display_name: Optional[str] = None, arduino_port: Optional[str] = None) -> Optional[int]:
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
            
            # Delete sessions
            cursor.execute('DELETE FROM live_sessions WHERE account_id = ?', (account_id,))
            
            # Delete account-related data
            cursor.execute('DELETE FROM arduino_devices WHERE account_id = ?', (account_id,))
            
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
    def create_live_session(self, account_id: int, session_name: Optional[str] = None) -> Optional[int]:
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

    # Arduino-specific methods
    def add_account(self, username: str, display_name: Optional[str] = None) -> Optional[int]:
        """Add account (alias for create_account)"""
        return self.create_account(username, display_name)
    
    def update_account_arduino_port(self, account_id: int, port: str):
        """Update Arduino port for account"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE accounts SET arduino_port = ? WHERE id = ?
            ''', (port, account_id))
            conn.commit()
    
    def get_arduino_stage_settings(self, account_id: int) -> List[Dict]:
        """Get Arduino stage settings for account"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM arduino_stage_settings WHERE account_id = ?
            ''', (account_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def save_arduino_stage_setting(self, account_id: int, stage_name: str, settings: Dict):
        """Save Arduino stage settings"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO arduino_stage_settings 
                (account_id, stage_name, settings, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (account_id, stage_name, json.dumps(settings)))
            conn.commit()
    
    def get_arduino_rules(self, account_id: int) -> List[Dict]:
        """Get Arduino rules for account"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM arduino_rules WHERE account_id = ?
            ''', (account_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def save_arduino_rule(self, account_id: int, rule_name: str, rule_data: Dict):
        """Save Arduino rule"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO arduino_rules 
                (account_id, rule_name, rule_data, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (account_id, rule_name, json.dumps(rule_data)))
            conn.commit()
    
    # Gift Registry Management
    def register_gift(self, gift_id: str, gift_name: str, diamond_count: int = 0, 
                     is_streakable: bool = False, category: str = 'general') -> Optional[int]:
        """Register or update gift in registry"""
        usd_value = diamond_count * 0.005  # TikTok conversion rate
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if gift already exists
            cursor.execute('SELECT id, usage_count FROM gift_registry WHERE gift_id = ? OR gift_name = ?', 
                          (gift_id, gift_name))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing gift
                cursor.execute('''
                    UPDATE gift_registry 
                    SET gift_name = ?, diamond_count = ?, usd_value = ?, is_streakable = ?, 
                        category = ?, last_seen = CURRENT_TIMESTAMP, usage_count = usage_count + 1
                    WHERE id = ?
                ''', (gift_name, diamond_count, usd_value, is_streakable, category, existing['id']))
                return existing['id']
            else:
                # Insert new gift
                cursor.execute('''
                    INSERT INTO gift_registry 
                    (gift_id, gift_name, diamond_count, usd_value, is_streakable, category)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (gift_id, gift_name, diamond_count, usd_value, is_streakable, category))
                conn.commit()
                return cursor.lastrowid
    
    def get_gift_by_name(self, gift_name: str) -> Optional[Dict]:
        """Get gift info by name"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM gift_registry WHERE gift_name = ?', (gift_name,))
            result = cursor.fetchone()
            return dict(result) if result else None
    
    def get_gift_by_id(self, gift_id: str) -> Optional[Dict]:
        """Get gift info by TikTok gift ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM gift_registry WHERE gift_id = ?', (gift_id,))
            result = cursor.fetchone()
            return dict(result) if result else None
    
    def get_all_gifts(self) -> List[Dict]:
        """Get all registered gifts"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM gift_registry ORDER BY usage_count DESC')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_popular_gifts(self, limit: int = 20) -> List[Dict]:
        """Get most popular gifts by usage count"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM gift_registry ORDER BY usage_count DESC LIMIT ?', (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def delete_arduino_rule(self, account_id: int, rule_name: str):
        """Delete Arduino rule"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM arduino_rules WHERE account_id = ? AND rule_name = ?
            ''', (account_id, rule_name))
            conn.commit()
