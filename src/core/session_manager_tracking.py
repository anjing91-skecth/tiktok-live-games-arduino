"""
Session Manager untuk TikTok Live Tracking System
Mengelola live sessions dengan fokus pada tracking (Arduino optional)
"""

import threading
import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from src.core.database_manager import DatabaseManager
from src.core.arduino_controller import ArduinoController
from src.core.tiktok_connector import TikTokConnector
from src.core.unicode_logger import get_safe_emoji_logger, SafeEmojiFormatter

class SessionManager:
    def __init__(self, database_manager: DatabaseManager, arduino_enabled: bool = True):
        self.logger = get_safe_emoji_logger(__name__)
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
        
        # Start monitoring thread
        self.is_running = True
        self.monitor_thread = threading.Thread(target=self._monitor_sessions, daemon=True)
        self.monitor_thread.start()
        
        self.logger.info("Session manager initialized successfully")
        return True
    
    def start_account_session(self, account_id: int, username: str, arduino_port: Optional[str] = None) -> bool:
        """Start live session for specific account"""
        try:
            account_key = f"acc_{account_id}"
            
            if account_key in self.active_sessions:
                self.logger.warning(f"Session already active for account {account_id}")
                return False
            
            self.logger.info(f"Starting session for account {account_id} ({username})")
            
            # Connect TikTok Live with robust error handling
            tiktok_connector = None
            tiktok_connection_successful = False
            
            try:
                self.logger.info(f"Attempting TikTok Live connection for {username}...")
                tiktok_connector = TikTokConnector(username)
                
                # Set up enhanced event handlers with real-time processing
                tiktok_connector.set_event_handlers(
                    on_gift=lambda gift: self._handle_gift_realtime(account_id, gift),
                    on_comment=lambda comment: self._handle_comment_realtime(account_id, comment),
                    on_like=lambda likes: self._handle_like_realtime(account_id, likes),
                    on_connection_status=lambda status: self._handle_connection_status(account_id, status)
                )
                
                # Try to connect with timeout and error handling
                tiktok_connection_successful = tiktok_connector.connect()
                
                if tiktok_connection_successful:
                    self.logger.info(f"✅ Successfully connected to TikTok Live for {username}")
                else:
                    self.logger.warning(f"⚠️ Failed to connect to TikTok Live for {username} - continuing in tracking mode")
                    tiktok_connector = None
                    
            except Exception as e:
                self.logger.warning(f"⚠️ TikTok Live connection error for {username}: {str(e)[:100]}... - continuing in tracking mode")
                tiktok_connector = None
                tiktok_connection_successful = False
            
            # Connect Arduino if enabled and port provided
            arduino_connected = False
            if self.arduino_enabled and self.arduino_controller and arduino_port:
                arduino_connected = self.arduino_controller.connect_arduino(
                    arduino_port, account_key
                )
                if not arduino_connected:
                    self.logger.warning(f"Failed to connect Arduino for account {account_id}")
            
            # Create live session in database
            session_name = f"Live Session {username} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            session_id = self.db_manager.create_live_session(
                account_id, session_name
            )
            
            # Store session data
            self.active_sessions[account_key] = {
                'account_id': account_id,
                'session_id': session_id,
                'username': username,
                'tiktok_connector': tiktok_connector,
                'tiktok_connected': tiktok_connection_successful,
                'start_time': time.time(),
                'arduino_port': arduino_port,
                'arduino_connected': arduino_connected,
                'total_gifts': 0,
                'total_comments': 0,
                'total_likes': 0
            }
            
            # Store TikTok connector if successfully connected
            if tiktok_connector and tiktok_connection_successful:
                self.tiktok_connectors[account_key] = tiktok_connector
            
            # Log session start status
            connection_status = []
            if tiktok_connection_successful:
                connection_status.append("TikTok Live ✅")
            else:
                connection_status.append("TikTok Live ❌ (tracking mode)")
            
            if arduino_connected:
                connection_status.append("Arduino ✅")
            else:
                connection_status.append("Arduino ❌")
            
            self.logger.info(f"Session started for account {account_id} - {' | '.join(connection_status)}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting session for account {account_id}: {e}")
            return False
    
    def stop_account_session(self, account_id: int) -> bool:
        """Stop live session for specific account"""
        try:
            account_key = f"acc_{account_id}"
            
            if account_key not in self.active_sessions:
                self.logger.warning(f"No active session found for account {account_id}")
                return False
            
            self.logger.info(f"Stopping session for account {account_id}")
            
            session_data = self.active_sessions[account_key]
            
            # Disconnect TikTok
            if account_key in self.tiktok_connectors:
                self.tiktok_connectors[account_key].disconnect()
                del self.tiktok_connectors[account_key]
            
            # Disconnect Arduino if connected
            if (self.arduino_enabled and self.arduino_controller and 
                session_data.get('arduino_connected', False)):
                self.arduino_controller.disconnect_arduino(account_key)
            
            # Update database session end time
            self.db_manager.update_live_session(
                session_data['session_id'],
                end_time=datetime.now(),
                total_gifts=session_data['total_gifts'],
                total_comments=session_data['total_comments'],
                total_likes=session_data['total_likes']
            )
            
            # Remove from active sessions
            del self.active_sessions[account_key]
            
            self.logger.info(f"Session stopped successfully for account {account_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping session for account {account_id}: {e}")
            return False
    
    def _handle_gift(self, account_id: int, gift_data: Dict[str, Any]):
        """Handle incoming gift event"""
        try:
            account_key = f"acc_{account_id}"
            session_data = self.active_sessions.get(account_key)
            
            if not session_data:
                return
            
            session_id = session_data['session_id']
            username = gift_data.get('username', 'Unknown')
            gift_name = gift_data.get('gift_name', 'Unknown')
            gift_value = gift_data.get('gift_value', 0)
            repeat_count = gift_data.get('repeat_count', 1)
            
            # Update session totals
            session_data['total_gifts'] += repeat_count
            
            # Get gift action configuration
            gift_config = self.db_manager.get_gift_action(account_id, gift_name)
            
            action_triggered = None
            if gift_config and gift_config.get('is_active', False):
                action_type = gift_config.get('action_type', '')
                device_target = gift_config.get('device_target', '')
                
                # Execute Arduino action if enabled
                if (self.arduino_enabled and self.arduino_controller and 
                    session_data.get('arduino_connected', False)):
                    self.arduino_controller.send_command(
                        account_key, action_type, device_target
                    )
                    action_triggered = f"{action_type}:{device_target}"
                else:
                    # Log action that would be triggered (tracking mode)
                    action_triggered = f"TRACK:{action_type}:{device_target}"
                    self.logger.info(f"Gift action tracked: {action_triggered} for {gift_name}")
            
            # Log gift to database
            self.db_manager.log_gift(
                session_id, username, gift_name, gift_value, 
                action_triggered or ""
            )
            
            self.logger.info(f"Gift processed: {username} sent {gift_name} x{repeat_count}")
            
        except Exception as e:
            self.logger.error(f"Error handling gift: {e}")
    
    def _handle_comment(self, account_id: int, comment_data: Dict[str, Any]):
        """Handle incoming comment event"""
        try:
            account_key = f"acc_{account_id}"
            session_data = self.active_sessions.get(account_key)
            
            if not session_data:
                return
            
            session_id = session_data['session_id']
            username = comment_data.get('username', 'Unknown')
            comment_text = comment_data.get('comment', '')
            
            # Update session totals
            session_data['total_comments'] += 1
            
            # Check for keyword matches
            keyword_matched = None
            action_triggered = None
            
            keyword_actions = self.db_manager.get_keyword_actions(account_id)
            for keyword_action in keyword_actions:
                if not keyword_action.get('is_active', False):
                    continue
                
                keyword = keyword_action.get('keyword', '').lower()
                match_type = keyword_action.get('match_type', 'contains')
                comment_lower = comment_text.lower()
                
                matched = False
                if match_type == 'exact':
                    matched = comment_lower == keyword
                elif match_type == 'contains':
                    matched = keyword in comment_lower
                
                if matched:
                    keyword_matched = keyword
                    
                    # Check cooldown
                    cooldown_key = f"{account_id}_{keyword}"
                    current_time = time.time()
                    cooldown_seconds = keyword_action.get('cooldown_seconds', 30)
                    
                    if (cooldown_key not in self.keyword_cooldowns or
                        current_time - self.keyword_cooldowns[cooldown_key] >= cooldown_seconds):
                        
                        # Execute action
                        action_type = keyword_action.get('action_type', '')
                        device_target = keyword_action.get('device_target', '')
                        
                        if (self.arduino_enabled and self.arduino_controller and 
                            session_data.get('arduino_connected', False)):
                            self.arduino_controller.send_command(
                                account_key, action_type, device_target
                            )
                            action_triggered = f"{action_type}:{device_target}"
                        else:
                            # Log action that would be triggered (tracking mode)
                            action_triggered = f"TRACK:{action_type}:{device_target}"
                            self.logger.info(f"Keyword action tracked: {action_triggered} for '{keyword}'")
                        
                        # Update cooldown
                        self.keyword_cooldowns[cooldown_key] = current_time
                    
                    break  # Use first matching keyword
            
            # Log comment to database
            self.db_manager.log_comment(
                session_id, username, comment_text, 
                keyword_matched or "", action_triggered or ""
            )
            
            self.logger.debug(f"Comment processed: {username}: {comment_text}")
            
        except Exception as e:
            self.logger.error(f"Error handling comment: {e}")
    
    def _handle_like(self, account_id: int, like_data: Dict[str, Any]):
        """Handle incoming like event"""
        try:
            account_key = f"acc_{account_id}"
            session_data = self.active_sessions.get(account_key)
            
            if not session_data:
                return
            
            # Update session totals
            like_count = like_data.get('like_count', 1)
            session_data['total_likes'] += like_count
            
            # Log like threshold achievements if configured
            # This could trigger automation scripts in the future
            
            self.logger.debug(f"Likes updated: +{like_count} (Total: {session_data['total_likes']})")
            
        except Exception as e:
            self.logger.error(f"Error handling like: {e}")
    
    # Enhanced Real-time Event Handlers
    def _handle_gift_realtime(self, account_id: int, gift_data: Dict[str, Any]):
        """Enhanced real-time gift handler with immediate processing"""
        try:
            # Call original handler
            self._handle_gift(account_id, gift_data)
            
            # Real-time enhancements
            account_key = f"acc_{account_id}"
            session_data = self.active_sessions.get(account_key)
            
            if session_data:
                # Enhanced gift data for real-time dashboard
                enhanced_gift = {
                    **gift_data,
                    'account_id': account_id,
                    'session_id': session_data['session_id'],
                    'value_tier': gift_data.get('value_tier', 'common'),
                    'gift_category': gift_data.get('gift_category', 'standard'),
                    'total_session_gifts': session_data['total_gifts']
                }
                
                # Emit to frontend via SocketIO
                if hasattr(self, 'socketio'):
                    self.socketio.emit('realtime_gift', enhanced_gift)
                
                # Log real-time stats
                self.logger.info(f"🎁 REAL-TIME: {enhanced_gift['username']} → {enhanced_gift['gift_name']} " +
                               f"(💎{enhanced_gift.get('total_value', 0)}) | Session Total: {session_data['total_gifts']}")
                
        except Exception as e:
            self.logger.error(f"Error in real-time gift handler: {e}")
    
    def _handle_comment_realtime(self, account_id: int, comment_data: Dict[str, Any]):
        """Enhanced real-time comment handler with immediate processing"""
        try:
            # Call original handler
            self._handle_comment(account_id, comment_data)
            
            # Real-time enhancements
            account_key = f"acc_{account_id}"
            session_data = self.active_sessions.get(account_key)
            
            if session_data:
                # Enhanced comment data
                enhanced_comment = {
                    **comment_data,
                    'account_id': account_id,
                    'session_id': session_data['session_id'],
                    'total_session_comments': session_data['total_comments'],
                    'comment_length': len(comment_data.get('comment', '')),
                    'contains_keywords': self._detect_keywords(comment_data.get('comment', ''))
                }
                
                # Emit to frontend
                if hasattr(self, 'socketio'):
                    self.socketio.emit('realtime_comment', enhanced_comment)
                
                # Log real-time stats
                comment_preview = comment_data.get('comment', '')[:30]
                self.logger.info(f"💬 REAL-TIME: {enhanced_comment['username']} → \"{comment_preview}...\" " +
                               f"| Session Total: {session_data['total_comments']}")
                
        except Exception as e:
            self.logger.error(f"Error in real-time comment handler: {e}")
    
    def _handle_like_realtime(self, account_id: int, like_data: Dict[str, Any]):
        """Enhanced real-time like handler with immediate processing"""
        try:
            # Call original handler
            self._handle_like(account_id, like_data)
            
            # Real-time enhancements
            account_key = f"acc_{account_id}"
            session_data = self.active_sessions.get(account_key)
            
            if session_data:
                # Enhanced like data
                enhanced_like = {
                    **like_data,
                    'account_id': account_id,
                    'session_id': session_data['session_id'],
                    'total_session_likes': session_data['total_likes']
                }
                
                # Emit to frontend
                if hasattr(self, 'socketio'):
                    self.socketio.emit('realtime_like', enhanced_like)
                
                # Batch log likes (less verbose)
                if session_data['total_likes'] % 10 == 0:  # Log every 10 likes
                    self.logger.info(f"❤️ REAL-TIME: Session likes milestone reached: {session_data['total_likes']}")
                
        except Exception as e:
            self.logger.error(f"Error in real-time like handler: {e}")
    
    def _handle_connection_status(self, account_id: int, status_data: Dict[str, Any]):
        """Handle TikTok Live connection status changes"""
        try:
            account_key = f"acc_{account_id}"
            session_data = self.active_sessions.get(account_key)
            
            if session_data:
                # Update connection status
                session_data['connection_status'] = status_data
                
                # Enhanced status data
                enhanced_status = {
                    **status_data,
                    'account_id': account_id,
                    'session_id': session_data['session_id']
                }
                
                # Emit to frontend
                if hasattr(self, 'socketio'):
                    self.socketio.emit('connection_status', enhanced_status)
                
                # Log connection changes
                status_emoji = "✅" if status_data.get('connected') else "❌"
                quality = status_data.get('quality', 'unknown')
                self.logger.info(f"{status_emoji} CONNECTION: @{status_data.get('username')} - {quality}")
                
        except Exception as e:
            self.logger.error(f"Error handling connection status: {e}")
    
    def _detect_keywords(self, comment: str) -> List[str]:
        """Detect keywords in comments for enhanced tracking"""
        try:
            keywords = ['jump', 'dance', 'light', 'music', 'game', 'play', 'start', 'stop']
            found_keywords = []
            comment_lower = comment.lower()
            
            for keyword in keywords:
                if keyword in comment_lower:
                    found_keywords.append(keyword)
            
            return found_keywords
        except:
            return []
    
    def set_socketio(self, socketio):
        """Set SocketIO instance for real-time communication"""
        self.socketio = socketio
        self.logger.info("SocketIO configured for real-time events")
    
    def get_active_sessions(self) -> Dict[str, Dict]:
        """Get all active sessions (JSON serializable)"""
        serializable_sessions = {}
        for account_key, session_data in self.active_sessions.items():
            # Create JSON-serializable version
            serializable_sessions[account_key] = {
                'account_id': session_data['account_id'],
                'username': session_data['username'],
                'session_id': session_data['session_id'],
                'start_time': session_data['start_time'],
                'duration': time.time() - session_data['start_time'],
                'total_gifts': session_data['total_gifts'],
                'total_comments': session_data['total_comments'],
                'total_likes': session_data['total_likes'],
                'arduino_connected': session_data.get('arduino_connected', False),
                'tiktok_connected': session_data.get('tiktok_connected', False)
            }
        return serializable_sessions
    
    def get_session_stats(self, account_id: int) -> Optional[Dict[str, Any]]:
        """Get current session statistics for account"""
        account_key = f"acc_{account_id}"
        session_data = self.active_sessions.get(account_key)
        
        if not session_data:
            return None
        
        return {
            'account_id': account_id,
            'username': session_data['username'],
            'session_id': session_data['session_id'],
            'duration': time.time() - session_data['start_time'],
            'total_gifts': session_data['total_gifts'],
            'total_comments': session_data['total_comments'],
            'total_likes': session_data['total_likes'],
            'arduino_connected': session_data.get('arduino_connected', False)
        }
    
    def _monitor_sessions(self):
        """Monitor active sessions and update database periodically"""
        while self.is_running:
            try:
                for account_key, session_data in self.active_sessions.items():
                    # Update session statistics in database
                    self.db_manager.update_live_session(
                        session_data['session_id'],
                        total_gifts=session_data['total_gifts'],
                        total_comments=session_data['total_comments'],
                        total_likes=session_data['total_likes']
                    )
                
                time.sleep(10)  # Update every 10 seconds
                
            except Exception as e:
                self.logger.error(f"Error in session monitor: {e}")
                time.sleep(5)
    
    def cleanup(self):
        """Cleanup session manager"""
        self.logger.info("Cleaning up session manager...")
        
        # Stop monitoring
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        # Stop all active sessions
        for account_id in list(self.active_sessions.keys()):
            if account_id.startswith('acc_'):
                try:
                    acc_id = int(account_id.split('_')[1])
                    self.stop_account_session(acc_id)
                except:
                    pass
        
        # Cleanup Arduino controller if enabled
        if self.arduino_enabled and self.arduino_controller:
            self.arduino_controller.cleanup()
        
        self.logger.info("Session manager cleanup complete")
