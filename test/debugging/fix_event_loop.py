"""
Fix untuk masalah event loop - test koneksi dan events
"""

import asyncio
import logging
import time
import threading
from src.core.tiktok_connector import TikTokConnector

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class EventCounter:
    def __init__(self):
        self.comments = 0
        self.gifts = 0
        self.likes = 0
        
    def on_comment(self, comment_data):
        self.comments += 1
        username = comment_data.get('username', 'Unknown')
        comment = comment_data.get('comment', '')
        print(f"💬 Comment #{self.comments}: @{username}: {comment}")
        
    def on_gift(self, gift_data):
        self.gifts += 1
        username = gift_data.get('username', 'Unknown')
        gift_name = gift_data.get('gift_name', 'Unknown')
        print(f"🎁 Gift #{self.gifts}: {gift_name} from @{username}")
        
    def on_like(self, like_data):
        self.likes += 1
        like_count = like_data.get('like_count', 0)
        print(f"👍 Like #{self.likes}: {like_count}")
        
    def on_connection_status(self, status_data):
        connected = status_data.get('connected', False)
        username = status_data.get('username', '')
        print(f"🔗 Connection: {'✅ Connected' if connected else '❌ Disconnected'} to @{username}")

def main():
    username = input("Enter username to test (default: rhianladiku19): ").strip() or "rhianladiku19"
    
    print(f"🔍 Testing event loop fix for @{username}")
    
    # Create event counter
    counter = EventCounter()
    
    # Create TikTok connector
    connector = TikTokConnector(username)
    
    # Set event handlers
    connector.set_event_handlers(
        on_comment=counter.on_comment,
        on_gift=counter.on_gift,
        on_like=counter.on_like,
        on_connection_status=counter.on_connection_status
    )
    
    print("🚀 Starting connection test...")
    
    # Test connection
    success = connector.connect()
    if success:
        print("✅ Connection successful!")
        print("📊 Monitoring events for 30 seconds...")
        time.sleep(30)
        
        print(f"\n📈 Event Summary:")
        print(f"   Comments: {counter.comments}")
        print(f"   Gifts: {counter.gifts}")
        print(f"   Likes: {counter.likes}")
        
        # Disconnect
        try:
            connector.disconnect()
            print("✅ Disconnected successfully")
        except:
            print("⚠️ Disconnect warning (normal for async operations)")
            
    else:
        print("❌ Connection failed")

if __name__ == "__main__":
    main()
