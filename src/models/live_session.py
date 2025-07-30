"""
Live Session Model untuk TikTok Live Games
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any

@dataclass
class LiveSession:
    id: Optional[int] = None
    account_id: int = 0
    session_name: str = ""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    total_coins: int = 0
    total_gifts: int = 0
    total_comments: int = 0
    current_likes: int = 0
    status: str = "active"  # active, completed, error
    
    def __post_init__(self):
        if self.start_time is None:
            self.start_time = datetime.now()
        
        if not self.session_name:
            self.session_name = f"Live Session {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'account_id': self.account_id,
            'session_name': self.session_name,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'total_coins': self.total_coins,
            'total_gifts': self.total_gifts,
            'total_comments': self.total_comments,
            'current_likes': self.current_likes,
            'status': self.status
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LiveSession':
        """Create from dictionary"""
        session = cls()
        session.id = data.get('id')
        session.account_id = data.get('account_id', 0)
        session.session_name = data.get('session_name', '')
        session.total_coins = data.get('total_coins', 0)
        session.total_gifts = data.get('total_gifts', 0)
        session.total_comments = data.get('total_comments', 0)
        session.current_likes = data.get('current_likes', 0)
        session.status = data.get('status', 'active')
        
        # Parse dates
        if data.get('start_time'):
            try:
                session.start_time = datetime.fromisoformat(data['start_time'])
            except:
                session.start_time = datetime.now()
        
        if data.get('end_time'):
            try:
                session.end_time = datetime.fromisoformat(data['end_time'])
            except:
                pass
        
        return session
    
    def get_duration(self) -> str:
        """Get session duration as string"""
        if not self.start_time:
            return "Unknown"
        
        end_time = self.end_time or datetime.now()
        duration = end_time - self.start_time
        
        hours = duration.seconds // 3600
        minutes = (duration.seconds % 3600) // 60
        seconds = duration.seconds % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    
    def is_active(self) -> bool:
        """Check if session is active"""
        return self.status == 'active'
    
    def end_session(self):
        """End the session"""
        self.end_time = datetime.now()
        self.status = 'completed'
