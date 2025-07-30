#!/usr/bin/env python3
"""
TikTok Live Games - Main Entry Point
Now launches the desktop application instead of web server
"""

import os
import sys

def main():
    """Main entry point - redirect to desktop launcher"""
    print("🎮 TikTok Live Games v2.0")
    print("Launching Desktop Application...")
    print()
    
    # Import and run desktop launcher
    try:
        from desktop_launcher import main as desktop_main
        desktop_main()
    except ImportError:
        # Fallback: run desktop launcher directly
        os.system("python desktop_launcher.py")

if __name__ == "__main__":
    main()
