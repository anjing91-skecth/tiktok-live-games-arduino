"""
Demo Live Data - Simulasi data untuk testing dashboard
"""

import sqlite3
import time
from datetime import datetime, timedelta
import random

def insert_demo_data():
    """Insert demo data for testing dashboard"""
    
    # Connect to database
    conn = sqlite3.connect('database/live_games.db')
    cursor = conn.cursor()
    
    # Get current active session
    cursor.execute("SELECT id FROM live_sessions WHERE end_time IS NULL ORDER BY id DESC LIMIT 1")
    session_result = cursor.fetchone()
    
    if not session_result:
        print("❌ No active session found. Start a session first!")
        conn.close()
        return
    
    session_id = session_result[0]
    print(f"✅ Found active session ID: {session_id}")
    
    # Clear existing demo data for this session first
    cursor.execute("DELETE FROM gift_logs WHERE session_id = ? AND username LIKE 'user_demo_%'", (session_id,))
    cursor.execute("DELETE FROM comment_logs WHERE session_id = ? AND username LIKE 'viewer_%'", (session_id,))
    cursor.execute("DELETE FROM like_tracking WHERE session_id = ?", (session_id,))
    print("🧹 Cleared existing demo data")
    
    # Demo gifts data
    gifts = [
        {"name": "Rose", "value": 1, "user": "user_demo_1"},
        {"name": "Heart", "value": 5, "user": "user_demo_2"},
        {"name": "Diamond", "value": 100, "user": "user_demo_3"},
        {"name": "Crown", "value": 500, "user": "user_demo_4"},
        {"name": "Galaxy", "value": 1000, "user": "user_demo_5"},
    ]
    
    # Demo comments
    comments = [
        {"user": "viewer_1", "message": "Hello everyone! 👋"},
        {"user": "viewer_2", "message": "Great live stream! 🔥"},
        {"user": "viewer_3", "message": "Love your content ❤️"},
        {"user": "viewer_4", "message": "Keep going! 💪"},
        {"user": "viewer_5", "message": "Amazing performance! 🎉"},
    ]
    
    # Insert demo gifts
    print("🎁 Inserting demo gifts...")
    for i, gift in enumerate(gifts):
        cursor.execute("""
            INSERT INTO gift_logs (session_id, gift_name, gift_value, username, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (
            session_id, 
            gift['name'], 
            gift['value'], 
            gift['user'],
            datetime.now() - timedelta(minutes=i*2)
        ))
        print(f"  • {gift['name']} (${gift['value']}) from @{gift['user']}")
    
    # Insert demo comments
    print("💬 Inserting demo comments...")
    for i, comment in enumerate(comments):
        cursor.execute("""
            INSERT INTO comment_logs (session_id, username, comment_text, timestamp)
            VALUES (?, ?, ?, ?)
        """, (
            session_id,
            comment['user'],
            comment['message'],
            datetime.now() - timedelta(minutes=i*3)
        ))
        print(f"  • @{comment['user']}: {comment['message']}")
    
    # Insert demo likes
    print("👍 Inserting demo likes...")
    for i in range(3):
        like_count = random.randint(50, 500)
        cursor.execute("""
            INSERT INTO like_tracking (session_id, current_like_count, timestamp)
            VALUES (?, ?, ?)
        """, (
            session_id,
            like_count,
            datetime.now() - timedelta(minutes=i*5)
        ))
        print(f"  • {like_count} likes")
    
    # Update session totals
    cursor.execute("""
        UPDATE live_sessions 
        SET total_gifts = (SELECT COUNT(*) FROM gift_logs WHERE session_id = ?),
            total_comments = (SELECT COUNT(*) FROM comment_logs WHERE session_id = ?),
            total_likes = (SELECT MAX(current_like_count) FROM like_tracking WHERE session_id = ?)
        WHERE id = ?
    """, (session_id, session_id, session_id, session_id))
    
    conn.commit()
    conn.close()
    
    print("🎉 Demo data inserted successfully!")
    print("🌐 Refresh your dashboard to see the data!")

if __name__ == "__main__":
    insert_demo_data()
