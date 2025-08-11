"""
App Package - Application Components
===================================

Extracted components from main.py for better maintainability and testing.

Components:
- MenuManager: Handles menu bar and menu actions
- TabCoordinator: Manages tab creation and coordination  
- AccountCoordinator: Handles account selection and management
"""

from .menu_manager import MenuManager
from .tab_coordinator import TabCoordinator
from .account_coordinator import AccountCoordinator

__all__ = [
    'MenuManager',
    'TabCoordinator', 
    'AccountCoordinator'
]
