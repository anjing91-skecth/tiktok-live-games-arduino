"""
TikTok Live Games Desktop Application Launcher
Clean version without web dependencies
"""

import sys
import os
import logging
from pathlib import Path

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

def check_dependencies():
    """Check if all required dependencies are available"""
    try:
        import tkinter
        import sqlite3
        print("✅ All required dependencies available")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        return False

def main():
    """Main launcher for desktop application"""
    print("🎮 TikTok Live Games Desktop Application")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        print("Please install missing dependencies")
        sys.exit(1)
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Starting TikTok Live Games Desktop Application")
        
        # Add src to path
        sys.path.append('src')
        
        # Import and run application
        from gui.main_window import TikTokLiveGamesApp
        
        print("🚀 Launching desktop application...")
        app = TikTokLiveGamesApp()
        app.run()
        
        logger.info("Application closed normally")
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        print("\n👋 Application closed by user")
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
