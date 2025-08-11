"""
Application Initializer Component
================================

Handles application setup, logging configuration, and dependency checks.
Extracted from main.py for better maintainability.
"""

import sys
import logging
from pathlib import Path
from datetime import datetime


class AppInitializer:
    """Handles application initialization and setup"""
    
    def __init__(self):
        """Initialize app initializer"""
        self.current_dir = Path(__file__).parent.parent.parent.parent
        self.setup_paths()
    
    def setup_paths(self):
        """Setup Python path for imports"""
        paths_to_add = [
            str(self.current_dir),
            str(self.current_dir / "src"),
            str(self.current_dir / "src" / "gui"),
            str(self.current_dir / "src" / "tracker"),
            str(self.current_dir / "src" / "app")
        ]
        
        for path in paths_to_add:
            if path not in sys.path:
                sys.path.insert(0, path)
    
    def setup_logging(self):
        """Setup lightweight logging with UTF-8 encoding"""
        log_dir = self.current_dir / "logs"
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"tiktok_lite_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        return logging.getLogger(__name__)
    
    def check_dependencies(self):
        """Check required dependencies"""
        try:
            import tkinter
            from TikTokLive import TikTokLiveClient
            print("✅ All required dependencies available")
            return True
        except ImportError as e:
            print(f"❌ Missing dependency: {e}")
            print("Please install: pip install TikTokLive")
            return False
    
    def initialize(self):
        """Full initialization process"""
        logger = self.setup_logging()
        
        if not self.check_dependencies():
            sys.exit(1)
        
        logger.info("🚀 Application initialization completed")
        return logger
