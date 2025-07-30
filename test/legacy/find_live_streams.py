#!/usr/bin/env python3
"""
Live Stream Discovery Tool
Mencari TikTok live streams yang aktif dan membantu koneksi
"""

import sys
import os
import time
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.core.live_stream_finder import LiveStreamFinder, LiveStreamManager
from src.core.unicode_logger import SafeEmojiFormatter

def print_header():
    """Print header untuk tool"""
    print(SafeEmojiFormatter.safe_format("""
{signal}============================================{signal}
{star}    TikTok Live Stream Discovery Tool    {star}
{signal}============================================{signal}

{game} Mencari live stream TikTok yang aktif...
{time} Started at: {timestamp}
""", signal='signal', star='star', game='game', time='time', timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

def test_specific_usernames():
    """Test username-username spesifik"""
    print(SafeEmojiFormatter.safe_format(
        "\n{info} Testing specific usernames...",
        info='info'
    ))
    
    # Username untuk ditest (anda bisa tambahkan di sini)
    test_usernames = [
        'ayhiefachri',  # Username yang anda sebutkan sebelumnya
        'charlidamelio',
        'addisonre',
        'zachking',
        'therock',
        'willsmith'
    ]
    
    finder = LiveStreamFinder()
    
    print(SafeEmojiFormatter.safe_format(
        "{loading} Checking {count} usernames for live streams...",
        loading='loading',
        count=len(test_usernames)
    ))
    
    results = finder.find_live_streams(test_usernames)
    
    # Show results
    live_streams = [r for r in results if r['is_live']]
    
    if live_streams:
        print(SafeEmojiFormatter.safe_format(
            "\n{ok} FOUND {count} LIVE STREAMS!",
            ok='ok',
            count=len(live_streams)
        ))
        
        for i, stream in enumerate(live_streams, 1):
            print(SafeEmojiFormatter.safe_format(
                "{star} {num}. @{username} - {viewers} viewers",
                star='star',
                num=i,
                username=stream['username'],
                viewers=stream['viewer_count']
            ))
            
        # Show connection instructions for first live stream
        if live_streams:
            target_username = live_streams[0]['username']
            manager = LiveStreamManager()
            instructions = manager.get_connection_instructions(target_username)
            print(instructions)
            
    else:
        print(SafeEmojiFormatter.safe_format(
            "\n{warning} No live streams found in tested usernames",
            warning='warning'
        ))
        
        # Show failed attempts
        print(SafeEmojiFormatter.safe_format(
            "\n{info} Checked usernames:",
            info='info'
        ))
        for result in results:
            status = "[OFFLINE]" if not result['is_live'] else "[LIVE]"
            error_msg = f" - {result['error']}" if result['error'] else ""
            print(f"   {status} @{result['username']}{error_msg}")

def discover_popular_streams():
    """Discover popular live streams"""
    print(SafeEmojiFormatter.safe_format(
        "\n{signal} Discovering popular live streams...",
        signal='signal'
    ))
    
    manager = LiveStreamManager()
    discovery_results = manager.discover_and_connect()
    
    live_streams = discovery_results['live_streams']
    
    if live_streams:
        print(SafeEmojiFormatter.safe_format(
            "\n{dashboard} DISCOVERY RESULTS:",
            dashboard='dashboard'
        ))
        print(f"   Scan Duration: {discovery_results['scan_duration']:.1f}s")
        print(f"   Total Checked: {discovery_results['total_checked']}")
        print(f"   Live Found: {discovery_results['live_found']}")
        
        print(SafeEmojiFormatter.safe_format(
            "\n{star} LIVE STREAMS FOUND:",
            star='star'
        ))
        
        for i, stream in enumerate(live_streams, 1):
            print(SafeEmojiFormatter.safe_format(
                "   {num}. @{username} - {viewers} viewers",
                num=i,
                username=stream['username'],
                viewers=stream['viewer_count']
            ))
            
        return live_streams[0]['username'] if live_streams else None
    else:
        print(SafeEmojiFormatter.safe_format(
            "\n{warning} No popular live streams found at this time",
            warning='warning'
        ))
        return None

def interactive_connection():
    """Interactive mode untuk koneksi manual"""
    print(SafeEmojiFormatter.safe_format(
        "\n{game} Interactive Connection Mode",
        game='game'
    ))
    
    print("\nPilihan:")
    print("1. Test username spesifik")
    print("2. Scan popular accounts")
    print("3. Manual input username")
    print("4. Exit")
    
    try:
        choice = input("\nMasukkan pilihan (1-4): ").strip()
        
        if choice == "1":
            test_specific_usernames()
        elif choice == "2":
            target_username = discover_popular_streams()
            if target_username:
                print(SafeEmojiFormatter.safe_format(
                    "\n{ok} Ready to connect to @{username}!",
                    ok='ok',
                    username=target_username
                ))
                print("Gunakan dashboard http://localhost:5000 untuk memulai session")
        elif choice == "3":
            username = input("Masukkan TikTok username (tanpa @): ").strip()
            if username:
                finder = LiveStreamFinder()
                result = finder.validate_live_stream(username)
                if result['is_live']:
                    print(SafeEmojiFormatter.safe_format(
                        "\n{ok} @{username} is LIVE! Ready to connect.",
                        ok='ok',
                        username=username
                    ))
                    manager = LiveStreamManager()
                    instructions = manager.get_connection_instructions(username)
                    print(instructions)
                else:
                    print(SafeEmojiFormatter.safe_format(
                        "\n{warning} @{username} is not currently live",
                        warning='warning',
                        username=username
                    ))
                    if result['error']:
                        print(f"Error: {result['error']}")
        elif choice == "4":
            print(SafeEmojiFormatter.safe_format(
                "\n{info} Exiting discovery tool...",
                info='info'
            ))
            return
        else:
            print(SafeEmojiFormatter.safe_format(
                "\n{warning} Invalid choice",
                warning='warning'
            ))
            
    except KeyboardInterrupt:
        print(SafeEmojiFormatter.safe_format(
            "\n\n{info} Discovery tool stopped by user",
            info='info'
        ))

def main():
    """Main function"""
    print_header()
    
    # Check if server is running
    import requests
    try:
        response = requests.get('http://localhost:5000/api/accounts', timeout=3)
        if response.status_code == 200:
            print(SafeEmojiFormatter.safe_format(
                "{ok} TikTok Live Tracker server is running at http://localhost:5000",
                ok='ok'
            ))
        else:
            print(SafeEmojiFormatter.safe_format(
                "{warning} Server is running but may have issues",
                warning='warning'
            ))
    except:
        print(SafeEmojiFormatter.safe_format(
            "{fail} TikTok Live Tracker server is NOT running!",
            fail='fail'
        ))
        print("Please start the server first with: python main.py")
        return
    
    # Start interactive mode
    while True:
        try:
            interactive_connection()
            
            # Ask if user wants to continue
            continue_choice = input("\nLanjutkan pencarian? (y/n): ").strip().lower()
            if continue_choice != 'y':
                break
                
        except KeyboardInterrupt:
            print(SafeEmojiFormatter.safe_format(
                "\n\n{info} Discovery tool stopped by user",
                info='info'
            ))
            break
    
    print(SafeEmojiFormatter.safe_format(
        "\n{star} Live stream discovery completed!",
        star='star'
    ))

if __name__ == "__main__":
    main()
