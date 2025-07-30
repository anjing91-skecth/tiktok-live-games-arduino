"""
Session Manager untuk TikTok Live Games
Mengelola live sessions dan koordinasi antara TikTok Live dan Arduino
"""

import threading
import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from src.core.database_manager import DatabaseManager
from src.core.arduino_controller import ArduinoController
from src.core.tiktok_connector import TikTokConnector

class SessionManager:
    def __init__(self, database_manager: DatabaseManager, arduino_enabled: bool = True):
        self.logger = logging.getLogger(__name__)
        self.db_manager = database_manager
        self.arduino_enabled = arduino_enabled
        self.arduino_controller = ArduinoController() if arduino_enabled else None
        self.tiktok_connectors: Dict[str, TikTokConnector] = {}
        self.active_sessions: Dict[str, Dict] = {}
        self.is_running = False
        self.monitor_thread = None
        
        # Cooldown tracking for keywords
        self.keyword_cooldowns: Dict[str, Dict[str, float]] = {}
        
    def initialize(self):
        """Initialize session manager"""
        self.logger.info("Initializing session manager...")
        
        # Initialize Arduino controller only if enabled
        if self.arduino_enabled and self.arduino_controller:
            if not self.arduino_controller.initialize():
                self.logger.error("Failed to initialize Arduino controller")
                return False
            self.logger.info("Arduino controller initialized")
        else:
            self.logger.info("Arduino controller disabled - tracking mode only")
        
        # Database should already be initialized by caller
        
        # Start monitoring thread
        self.is_running = True
        self.monitor_thread = threading.Thread(target=self._monitor_sessions, daemon=True)
        self.monitor_thread.start()
        
        self.logger.info("Session manager initialized successfully")
        return True
    
    def start_account_session(self, account_id: int, username: str, arduino_port: str = None) -> bool:
        """Start live session for specific account"""
        try:
            account_key = str(account_id)
            
            if account_key in self.active_sessions:
                self.logger.warning(f"Session already active for account {account_id}")
                return False
            
            # Create database session
            session_id = self.db_manager.create_live_session(
                account_id, 
                f"Live Session {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            # Connect Arduino if port specified
            arduino_connected = False
            if arduino_port:
                arduino_connected = self.arduino_controller.connect_arduino(
                    arduino_port, account_key
                )
            
            # Initialize TikTok connector
            tiktok_connector = TikTokConnector(username)
            tiktok_connector.set_event_handlers(
                on_gift=lambda gift_data: self._handle_gift(account_key, session_id, gift_data),
                on_comment=lambda comment_data: self._handle_comment(account_key, session_id, comment_data),
                on_like=lambda like_data: self._handle_like(account_key, session_id, like_data)
            )
            
            # Start TikTok connection
            tiktok_connected = tiktok_connector.connect()
            
            if tiktok_connected:
                # Store session info
                self.active_sessions[account_key] = {
                    'account_id': account_id,
                    'session_id': session_id,
                    'username': username,
                    'arduino_port': arduino_port,
                    'arduino_connected': arduino_connected,
                    'tiktok_connected': True,
                    'start_time': datetime.now(),
                    'stats': {
                        'total_gifts': 0,
                        'total_coins': 0,
                        'total_comments': 0,
                        'current_likes': 0
                    }
                }
                
                self.tiktok_connectors[account_key] = tiktok_connector
                
                # Update account status
                self.db_manager.update_account_status(account_id, 'active')
                
                self.logger.info(f"Session started for account {username} (ID: {account_id})")
                return True
            else:
                self.logger.error(f"Failed to connect to TikTok for account {username}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error starting session for account {account_id}: {e}")
            return False
    
    def stop_account_session(self, account_id: int):
        """Stop live session for specific account"""
        try:
            account_key = str(account_id)
            
            if account_key not in self.active_sessions:
                self.logger.warning(f"No active session for account {account_id}")
                return
            
            session_info = self.active_sessions[account_key]
            
            # Stop TikTok connector
            if account_key in self.tiktok_connectors:
                self.tiktok_connectors[account_key].disconnect()
                del self.tiktok_connectors[account_key]
            
            # Disconnect Arduino
            self.arduino_controller.disconnect_arduino(account_key)
            
            # End database session
            self.db_manager.end_live_session(session_info['session_id'])
            
            # Update account status
            self.db_manager.update_account_status(account_id, 'inactive')
            
            # Remove from active sessions
            del self.active_sessions[account_key]
            
            self.logger.info(f"Session stopped for account {account_id}")
            
        except Exception as e:
            self.logger.error(f"Error stopping session for account {account_id}: {e}")
    
    def _handle_gift(self, account_key: str, session_id: int, gift_data: Dict[str, Any]):
        """Handle received gift"""
        try:
            username = gift_data.get('username', 'Unknown')
            gift_name = gift_data.get('gift_name', 'unknown')
            gift_value = gift_data.get('gift_value', 0)
            
            # Log gift to database
            action_triggered = self._process_gift_action(account_key, gift_name, gift_value)
            self.db_manager.log_gift(session_id, username, gift_name, gift_value, action_triggered)
            
            # Update leaderboard
            self.db_manager.update_leaderboard(session_id, username, gift_value)
            
            # Update session stats
            if account_key in self.active_sessions:
                self.active_sessions[account_key]['stats']['total_gifts'] += 1
                self.active_sessions[account_key]['stats']['total_coins'] += gift_value
            
            self.logger.info(f"Gift received: {gift_name} (value: {gift_value}) from {username}")
            
        except Exception as e:
            self.logger.error(f"Error handling gift: {e}")
    
    def _handle_comment(self, account_key: str, session_id: int, comment_data: Dict[str, Any]):
        """Handle received comment"""
        try:
            username = comment_data.get('username', 'Unknown')
            comment_text = comment_data.get('comment', '')
            
            # Process keyword detection
            keyword_matched, action_triggered = self._process_comment_keywords(
                account_key, comment_text
            )
            
            # Log comment to database
            self.db_manager.log_comment(
                session_id, username, comment_text, keyword_matched, action_triggered
            )
            
            # Update session stats
            if account_key in self.active_sessions:
                self.active_sessions[account_key]['stats']['total_comments'] += 1
            
            self.logger.debug(f"Comment received: '{comment_text}' from {username}")
            
        except Exception as e:
            self.logger.error(f"Error handling comment: {e}")
    
    def _handle_like(self, account_key: str, session_id: int, like_data: Dict[str, Any]):
        """Handle like count update"""
        try:
            like_count = like_data.get('like_count', 0)
            
            # Process like thresholds
            self._process_like_thresholds(account_key, session_id, like_count)
            
            # Update session stats
            if account_key in self.active_sessions:
                self.active_sessions[account_key]['stats']['current_likes'] = like_count
            
        except Exception as e:
            self.logger.error(f"Error handling like: {e}")
    
    def _process_gift_action(self, account_key: str, gift_name: str, gift_value: int) -> Optional[str]:
        """Process gift and trigger Arduino action if mapped"""
        try:
            # Load gift action mappings (simplified for now)
            gift_actions = {
                'rose': {'device': 'LED1', 'action': 'blink', 'duration': 1000},
                'love': {'device': 'SOL1', 'action': 'push', 'duration': 2000},
                'lion': {'device': 'MOT1', 'action': 'rotate', 'duration': 5000}
            }
            
            if gift_name.lower() in gift_actions:
                action_config = gift_actions[gift_name.lower()]
                
                self.arduino_controller.send_command(
                    account_key,
                    action_config['device'],
                    action_config['action'],
                    action_config['duration']
                )
                
                return f"{action_config['device']}:{action_config['action']}"
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error processing gift action: {e}")
            return None
    
    def _process_comment_keywords(self, account_key: str, comment_text: str) -> tuple[Optional[str], Optional[str]]:
        """Process comment for keyword matches"""
        try:
            # Load keyword mappings (simplified for now)
            keyword_actions = {
                '666': {'device': 'SOL1', 'action': 'push', 'duration': 3000, 'cooldown': 60, 'match_type': 'exact'},
                '777': {'device': 'LED1', 'action': 'flash', 'duration': 5000, 'cooldown': 90, 'match_type': 'exact'},
                'tembak': {'device': 'SOL1', 'action': 'push', 'duration': 1500, 'cooldown': 30, 'match_type': 'contains'},
                'ledak': {'device': 'SOL1', 'action': 'push', 'duration': 2000, 'cooldown': 45, 'match_type': 'contains'}
            }
            
            comment_lower = comment_text.lower().strip()
            
            for keyword, action_config in keyword_actions.items():
                keyword_matched = False
                
                if action_config['match_type'] == 'exact':
                    keyword_matched = comment_lower == keyword.lower()
                elif action_config['match_type'] == 'contains':
                    keyword_matched = keyword.lower() in comment_lower
                
                if keyword_matched:
                    # Check cooldown
                    if self._check_keyword_cooldown(account_key, keyword, action_config['cooldown']):
                        self.arduino_controller.send_command(
                            account_key,
                            action_config['device'],
                            action_config['action'],
                            action_config['duration']
                        )
                        
                        return keyword, f"{action_config['device']}:{action_config['action']}"
                    else:
                        self.logger.debug(f"Keyword '{keyword}' still in cooldown for account {account_key}")
                        return keyword, "COOLDOWN"
            
            return None, None
            
        except Exception as e:
            self.logger.error(f"Error processing comment keywords: {e}")
            return None, None
    
    def _check_keyword_cooldown(self, account_key: str, keyword: str, cooldown_seconds: int) -> bool:
        """Check if keyword is not in cooldown"""
        current_time = time.time()
        
        if account_key not in self.keyword_cooldowns:
            self.keyword_cooldowns[account_key] = {}
        
        last_trigger = self.keyword_cooldowns[account_key].get(keyword, 0)
        
        if current_time - last_trigger >= cooldown_seconds:
            self.keyword_cooldowns[account_key][keyword] = current_time
            return True
        
        return False
    
    def _process_like_thresholds(self, account_key: str, session_id: int, like_count: int):
        """Process like count thresholds"""
        try:
            # Define like thresholds
            thresholds = [100, 500, 1000, 2000, 5000]
            
            for threshold in thresholds:
                if like_count >= threshold:
                    # Check if this threshold was already triggered
                    # (This is simplified - in real implementation, track in database)
                    pass
                    
        except Exception as e:
            self.logger.error(f"Error processing like thresholds: {e}")
    
    def _monitor_sessions(self):
        """Monitor active sessions for health and statistics"""
        self.logger.info("Session monitor started")
        
        while self.is_running:
            try:
                # Monitor connection health
                for account_key, session_info in list(self.active_sessions.items()):
                    # Check TikTok connection
                    if account_key in self.tiktok_connectors:
                        connector = self.tiktok_connectors[account_key]
                        if not connector.is_connected():
                            self.logger.warning(f"TikTok connection lost for account {account_key}")
                            # Attempt reconnection
                            connector.reconnect()
                
                # Sleep for monitoring interval
                time.sleep(30)
                
            except Exception as e:
                self.logger.error(f"Error in session monitor: {e}")
                time.sleep(10)
        
        self.logger.info("Session monitor stopped")
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get current session statistics"""
        return {
            'active_sessions': len(self.active_sessions),
            'sessions': {
                account_key: {
                    'username': info['username'],
                    'arduino_connected': info['arduino_connected'],
                    'tiktok_connected': info['tiktok_connected'],
                    'uptime': str(datetime.now() - info['start_time']),
                    'stats': info['stats']
                }
                for account_key, info in self.active_sessions.items()
            }
        }
    
    def cleanup(self):
        """Cleanup session manager"""
        self.logger.info("Cleaning up session manager...")
        
        # Stop monitoring
        self.is_running = False
        
        # Stop all active sessions
        for account_id in list(self.active_sessions.keys()):
            self.stop_account_session(int(account_id))
        
        # Cleanup Arduino controller
        self.arduino_controller.cleanup()
        
        # Wait for monitor thread
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        
        self.logger.info("Session manager cleanup complete")
