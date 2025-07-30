#!/usr/bin/env python3
"""
Quick Status Check
"""

import requests
import json

def check_status():
    try:
        print("🎯 TikTok Live Integration Status")
        print("=" * 50)
        
        # Check sessions
        response = requests.get("http://localhost:5000/api/sessions/active", timeout=5)
        data = response.json()
        
        sessions = data.get('sessions', {})
        if not sessions:
            print("❌ No active sessions found")
            return
            
        # Count connected sessions
        connected_count = sum(1 for s in sessions.values() if s['tiktok_connected'])
        total_count = len(sessions)
        print(f"📊 Sessions: {connected_count}/{total_count} connected")
            
        for key, session in sessions.items():
            username = session['username']
            tiktok_connected = session['tiktok_connected']
            status = "✅ CONNECTED" if tiktok_connected else "⚠️ TRACKING MODE"
            
            print(f"\n📺 {username.upper()}")
            print(f"   Status: {status}")
            print(f"   Session ID: {session['session_id']}")
            
            if tiktok_connected:
                print(f"   💬 Comments: {session['total_comments']}")
                print(f"   🎁 Gifts: {session['total_gifts']}")
                print(f"   👍 Likes: {session['total_likes']}")
            else:
                print("   📡 Ready for live data when connection succeeds")
                
        print(f"\n💡 Dashboard: http://localhost:5000")
        print("🔄 Sessions are active and monitoring")
        
        # Suggest next actions
        if connected_count == 0:
            print("\n🚀 NEXT STEPS:")
            print("   1. Start ayhiefachri session")
            print("   2. Test live connections") 
            print("   3. Trigger gifts/comments in live streams")
        elif connected_count < total_count:
            print("\n🎯 ACTION NEEDED:")
            print("   • Some sessions not connected")
            print("   • Try starting remaining sessions")
        else:
            print("\n🎉 ALL SYSTEMS GO!")
            print("   • Ready for live data testing")
            print("   • Trigger gifts/comments to see real-time data")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_status()
