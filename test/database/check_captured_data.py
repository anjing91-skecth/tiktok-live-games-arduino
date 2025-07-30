#!/usr/bin/env python3
"""
Check Captured Data
Quick script to view captured gift, comment, and like data
"""

import sqlite3
from datetime import datetime

def check_captured_data():
    """Check all captured data"""
    print("📊 DATA CAPTURE RESULTS")
    print("="*40)
    
    try:
        conn = sqlite3.connect('database/live_games.db')
        cursor = conn.cursor()
        
        # Check gifts
        print("\n🎁 GIFTS CAPTURED:")
        cursor.execute('''
            SELECT session_id, username, gift_name, gift_value, timestamp 
            FROM gift_logs 
            ORDER BY timestamp DESC 
            LIMIT 10
        ''')
        gifts = cursor.fetchall()
        
        if gifts:
            for row in gifts:
                print(f"  Session {row[0]}: {row[1]} sent {row[2]} (${row[3]}) at {row[4]}")
        else:
            print("  No gifts found")
        
        # Check comments
        print("\n💬 COMMENTS CAPTURED:")
        cursor.execute('''
            SELECT session_id, username, comment_text, timestamp 
            FROM comment_logs 
            ORDER BY timestamp DESC 
            LIMIT 10
        ''')
        comments = cursor.fetchall()
        
        if comments:
            for row in comments:
                print(f"  Session {row[0]}: {row[1]}: {row[2]} at {row[3]}")
        else:
            print("  No comments found")
        
        # Check like tracking
        print("\n👍 LIKE TRACKING:")
        cursor.execute('''
            SELECT session_id, current_like_count, timestamp 
            FROM like_tracking 
            ORDER BY timestamp DESC 
            LIMIT 10
        ''')
        likes = cursor.fetchall()
        
        if likes:
            for row in likes:
                print(f"  Session {row[0]}: {row[1]} likes at {row[2]}")
        else:
            print("  No like tracking found")
        
        # Check sessions
        print("\n📈 SESSIONS:")
        cursor.execute('''
            SELECT id, account_id, session_name, status, start_time 
            FROM live_sessions 
            ORDER BY start_time DESC 
            LIMIT 5
        ''')
        sessions = cursor.fetchall()
        
        if sessions:
            for row in sessions:
                print(f"  Session {row[0]}: Account {row[1]} - {row[2]} ({row[3]}) at {row[4]}")
        else:
            print("  No sessions found")
        
        # Summary counts
        print("\n📊 SUMMARY:")
        cursor.execute("SELECT COUNT(*) FROM gift_logs")
        gift_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM comment_logs")
        comment_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM like_tracking")
        like_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM live_sessions")
        session_count = cursor.fetchone()[0]
        
        print(f"  Total Gifts: {gift_count}")
        print(f"  Total Comments: {comment_count}")
        print(f"  Total Like Updates: {like_count}")
        print(f"  Total Sessions: {session_count}")
        
        conn.close()
        print("\n✅ Data check completed!")
        
    except Exception as e:
        print(f"❌ Error checking data: {str(e)}")

if __name__ == "__main__":
    check_captured_data()
