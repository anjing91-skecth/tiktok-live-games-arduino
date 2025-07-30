#!/usr/bin/env python3
"""
Launcher untuk GUI Unified Session Manager
==========================================
Test GUI yang sudah terintegrasi dengan UnifiedSessionManager
"""

import os
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def main():
    """Launch unified GUI"""
    print("🚀 LAUNCHING UNIFIED TIKTOK LIVE GAMES CONTROLLER")
    print("=" * 60)
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/gui_unified.log'),
            logging.StreamHandler()
        ]
    )
    
    try:
        # Create logs directory
        Path("logs").mkdir(exist_ok=True)
        
        # Import and run unified GUI
        from gui.main_window_unified import TikTokLiveGamesAppUnified
        
        print("✅ Unified GUI modules loaded")
        print("🎯 Starting application with UnifiedSessionManager...")
        
        app = TikTokLiveGamesAppUnified()
        app.run()
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("\n💡 Possible solutions:")
        print("1. Ensure all core modules are available")
        print("2. Check Python path configuration")
        print("3. Install missing dependencies")
        
    except Exception as e:
        print(f"❌ Application error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
