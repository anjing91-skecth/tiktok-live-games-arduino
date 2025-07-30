"""
Account Model untuk TikTok Live Games
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Account:
    id: Optional[int] = None
    username: str = ""
    display_name: str = ""
    arduino_port: str = ""
    status: str = "inactive"  # inactive, active, error
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'display_name': self.display_name,
            'arduino_port': self.arduino_port,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Account':
        """Create from dictionary"""
        account = cls()
        account.id = data.get('id')
        account.username = data.get('username', '')
        account.display_name = data.get('display_name', '')
        account.arduino_port = data.get('arduino_port', '')
        account.status = data.get('status', 'inactive')
        
        if data.get('created_at'):
            try:
                account.created_at = datetime.fromisoformat(data['created_at'])
            except:
                account.created_at = datetime.now()
        
        return account
    
    def is_active(self) -> bool:
        """Check if account is active"""
        return self.status == 'active'
    
    def has_arduino(self) -> bool:
        """Check if account has Arduino port configured"""
        return bool(self.arduino_port and self.arduino_port.strip())
