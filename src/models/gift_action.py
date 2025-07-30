"""
Gift Action Model untuk TikTok Live Games
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List

@dataclass
class GiftLog:
    id: Optional[int] = None
    session_id: int = 0
    username: str = ""
    gift_name: str = ""
    gift_value: int = 0
    repeat_count: int = 1
    total_value: int = 0
    timestamp: Optional[datetime] = None
    action_triggered: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        
        if self.total_value == 0:
            self.total_value = self.gift_value * self.repeat_count
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'username': self.username,
            'gift_name': self.gift_name,
            'gift_value': self.gift_value,
            'repeat_count': self.repeat_count,
            'total_value': self.total_value,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'action_triggered': self.action_triggered
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GiftLog':
        """Create from dictionary"""
        gift = cls()
        gift.id = data.get('id')
        gift.session_id = data.get('session_id', 0)
        gift.username = data.get('username', '')
        gift.gift_name = data.get('gift_name', '')
        gift.gift_value = data.get('gift_value', 0)
        gift.repeat_count = data.get('repeat_count', 1)
        gift.total_value = data.get('total_value', 0)
        gift.action_triggered = data.get('action_triggered')
        
        if data.get('timestamp'):
            try:
                gift.timestamp = datetime.fromisoformat(data['timestamp'])
            except:
                gift.timestamp = datetime.now()
        
        return gift

@dataclass
class CommentLog:
    id: Optional[int] = None
    session_id: int = 0
    username: str = ""
    comment_text: str = ""
    keyword_matched: Optional[str] = None
    timestamp: Optional[datetime] = None
    action_triggered: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'username': self.username,
            'comment_text': self.comment_text,
            'keyword_matched': self.keyword_matched,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'action_triggered': self.action_triggered
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CommentLog':
        """Create from dictionary"""
        comment = cls()
        comment.id = data.get('id')
        comment.session_id = data.get('session_id', 0)
        comment.username = data.get('username', '')
        comment.comment_text = data.get('comment_text', '')
        comment.keyword_matched = data.get('keyword_matched')
        comment.action_triggered = data.get('action_triggered')
        
        if data.get('timestamp'):
            try:
                comment.timestamp = datetime.fromisoformat(data['timestamp'])
            except:
                comment.timestamp = datetime.now()
        
        return comment

@dataclass
class LeaderboardEntry:
    id: Optional[int] = None
    session_id: int = 0
    username: str = ""
    total_coins: int = 0
    gift_count: int = 0
    rank_position: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'username': self.username,
            'total_coins': self.total_coins,
            'gift_count': self.gift_count,
            'rank_position': self.rank_position
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LeaderboardEntry':
        """Create from dictionary"""
        entry = cls()
        entry.id = data.get('id')
        entry.session_id = data.get('session_id', 0)
        entry.username = data.get('username', '')
        entry.total_coins = data.get('total_coins', 0)
        entry.gift_count = data.get('gift_count', 0)
        entry.rank_position = data.get('rank_position', 0)
        return entry

@dataclass
class KeywordAction:
    id: Optional[int] = None
    account_id: int = 0
    keyword: str = ""
    match_type: str = "contains"  # exact, contains
    action_type: str = ""
    device_target: str = ""
    cooldown_seconds: int = 30
    is_active: bool = True
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'account_id': self.account_id,
            'keyword': self.keyword,
            'match_type': self.match_type,
            'action_type': self.action_type,
            'device_target': self.device_target,
            'cooldown_seconds': self.cooldown_seconds,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KeywordAction':
        """Create from dictionary"""
        action = cls()
        action.id = data.get('id')
        action.account_id = data.get('account_id', 0)
        action.keyword = data.get('keyword', '')
        action.match_type = data.get('match_type', 'contains')
        action.action_type = data.get('action_type', '')
        action.device_target = data.get('device_target', '')
        action.cooldown_seconds = data.get('cooldown_seconds', 30)
        action.is_active = data.get('is_active', True)
        
        if data.get('created_at'):
            try:
                action.created_at = datetime.fromisoformat(data['created_at'])
            except:
                action.created_at = datetime.now()
        
        return action
