#!/usr/bin/env python3
"""
Auto Live Stream Connector
Otomatis mencari dan connect ke live stream TikTok
"""

import sys
import os
import time
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.core.live_stream_finder import LiveStreamFinder, LiveStreamManager
from src.core.unicode_logger import SafeEmojiFormatter

def main():
    """Main function untuk auto discovery"""
    print(SafeEmojiFormatter.safe_format("""
{signal}============================================{signal}
{star}    Auto TikTok Live Stream Connector    {star}
{signal}============================================{signal}

{game} Target usernames: rhianladiku19, ayhiefachri
{time} Started at: {timestamp}
""", signal='signal', star='star', game='game', time='time', timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

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
    except Exception as e:
        print(SafeEmojiFormatter.safe_format(
            "{fail} TikTok Live Tracker server is NOT running!",
            fail='fail'
        ))
        print("Please start the server first with: python main.py")
        print(f"Error: {e}")
        return

    # Target usernames yang akan dicek
    target_usernames = ['rhianladiku19', 'ayhiefachri']
    
    print(SafeEmojiFormatter.safe_format(
        "\n{loading} Testing specific target usernames...",
        loading='loading'
    ))
    
    finder = LiveStreamFinder()
    results = []
    
    # Test setiap username
    for username in target_usernames:
        print(SafeEmojiFormatter.safe_format(
            "\n{signal} Checking @{username}...",
            signal='signal',
            username=username
        ))
        
        result = finder.validate_live_stream(username)
        results.append(result)
        
        if result['is_live']:
            print(SafeEmojiFormatter.safe_format(
                "{ok} @{username} is LIVE! Ready to connect.",
                ok='ok',
                username=username
            ))
        else:
            print(SafeEmojiFormatter.safe_format(
                "{warning} @{username} is not currently live",
                warning='warning',
                username=username
            ))
            if result['error']:
                print(f"   Error: {result['error']}")
    
    # Show summary
    live_streams = [r for r in results if r['is_live']]
    
    print(SafeEmojiFormatter.safe_format(
        "\n{dashboard} DISCOVERY RESULTS:",
        dashboard='dashboard'
    ))
    print(f"   Total Checked: {len(results)}")
    print(f"   Live Found: {len(live_streams)}")
    
    if live_streams:
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
        
        # Auto connect to first live stream
        target_username = live_streams[0]['username']
        print(SafeEmojiFormatter.safe_format(
            "\n{start} AUTO-CONNECTING to @{username}...",
            start='start',
            username=target_username
        ))
        
        # Add account to system
        try:
            import requests
            
            # Add account
            add_data = {
                'username': target_username,
                'description': f'Auto-discovered live stream: @{target_username}'
            }
            
            add_response = requests.post('http://localhost:5000/api/accounts', json=add_data)
            
            if add_response.status_code == 200:
                account_data = add_response.json()
                account_id = account_data['account']['id']
                
                print(SafeEmojiFormatter.safe_format(
                    "{ok} Account @{username} added (ID: {id})",
                    ok='ok',
                    username=target_username,
                    id=account_id
                ))
                
                # Start session
                print(SafeEmojiFormatter.safe_format(
                    "{loading} Starting live tracking session...",
                    loading='loading'
                ))
                
                start_response = requests.post(f'http://localhost:5000/api/sessions/start/{account_id}')
                
                if start_response.status_code == 200:
                    print(SafeEmojiFormatter.safe_format(
                        "{ok} Live tracking session started successfully!",
                        ok='ok'
                    ))
                    
                    print(SafeEmojiFormatter.safe_format(
                        "\n{dashboard} LIVE TRACKING ACTIVE:",
                        dashboard='dashboard'
                    ))
                    print(f"   Username: @{target_username}")
                    print(f"   Dashboard: http://localhost:5000")
                    print(f"   Account ID: {account_id}")
                    
                    print(SafeEmojiFormatter.safe_format(
                        "\n{star} Real-time events will be displayed in:",
                        star='star'
                    ))
                    print("   • Dashboard web interface")
                    print("   • Server console logs") 
                    print("   • Real-time statistics")
                    
                    print(SafeEmojiFormatter.safe_format(
                        "\n{info} Monitor the server terminal for live events!",
                        info='info'
                    ))
                    
                else:
                    print(SafeEmojiFormatter.safe_format(
                        "{warning} Failed to start session: {status}",
                        warning='warning',
                        status=start_response.status_code
                    ))
                    print(f"Response: {start_response.text}")
                    
            else:
                print(SafeEmojiFormatter.safe_format(
                    "{warning} Failed to add account: {status}",
                    warning='warning',
                    status=add_response.status_code
                ))
                print(f"Response: {add_response.text}")
                
        except Exception as e:
            print(SafeEmojiFormatter.safe_format(
                "{error} Error during auto-connection: {exception}",
                error='error',
                exception=str(e)
            ))
            
    else:
        print(SafeEmojiFormatter.safe_format(
            "\n{warning} No live streams found for target usernames",
            warning='warning'
        ))
        
        print(SafeEmojiFormatter.safe_format(
            "\n{info} Trying broader search with popular accounts...",
            info='info'
        ))
        
        # Try popular accounts as backup
        manager = LiveStreamManager()
        discovery_results = manager.discover_and_connect(target_usernames)
        
        backup_live_streams = discovery_results['live_streams']
        
        if backup_live_streams:
            print(SafeEmojiFormatter.safe_format(
                "\n{star} BACKUP DISCOVERY FOUND {count} LIVE STREAMS:",
                star='star',
                count=len(backup_live_streams)
            ))
            
            for i, stream in enumerate(backup_live_streams[:3], 1):
                print(SafeEmojiFormatter.safe_format(
                    "   {num}. @{username} - {viewers} viewers",
                    num=i,
                    username=stream['username'],
                    viewers=stream['viewer_count']
                ))
                
            print(SafeEmojiFormatter.safe_format(
                "\n{info} Use dashboard to connect to any of these streams",
                info='info'
            ))
        else:
            print(SafeEmojiFormatter.safe_format(
                "\n{fail} No live streams found in extended search",
                fail='fail'
            ))
    
    print(SafeEmojiFormatter.safe_format(
        "\n{star} Auto discovery completed! Check dashboard: http://localhost:5000",
        star='star'
    ))

if __name__ == "__main__":
    main()
