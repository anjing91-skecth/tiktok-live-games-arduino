#!/usr/bin/env python3
"""
Launcher untuk menjalankan program utama dengan UnifiedSessionManager
"""

import sys
import os
import logging

def main():
    """Launch main program dengan unified system"""
    print("🎮 TikTok Live Games v2.0 - Unified System")
    print("=" * 50)
    print("✅ UnifiedSessionManager: INTEGRATED")
    print("⚡ Arduino Real-time Triggers: ENABLED")
    print("🎯 Smart Session Management: ENABLED") 
    print("💾 Background Data Saving: ENABLED")
    print("📊 Live Memory Updates: ENABLED")
    print("📦 Auto-archive (3 months): ENABLED")
    print("=" * 50)
    
    # Import dan jalankan main program
    try:
        from main import main as main_program
        main_program()
    except ImportError:
        # Fallback ke desktop launcher
        from desktop_launcher import main as desktop_main
        desktop_main()

if __name__ == "__main__":
    main()
