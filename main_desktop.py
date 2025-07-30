#!/usr/bin/env python3
"""
TikTok Live Games Desktop Application
Entry point untuk aplikasi desktop berbasis Tkinter
"""

import sys
import os
import logging
from pathlib import Path

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import GUI components
from gui.main_window import TikTokLiveGamesApp

def setup_logging():
    """Setup logging configuration"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "tiktok_desktop.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """Main entry point for desktop application"""
    try:
        setup_logging()
        logger = logging.getLogger(__name__)
        logger.info("Starting TikTok Live Games Desktop Application")
        
        # Create and run the application
        app = TikTokLiveGamesApp()
        app.run()
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
