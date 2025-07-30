#!/usr/bin/env python3
"""
Direct Live Session Starter
Langsung start session untuk account yang sudah ada
"""

import requests
import json

def get_accounts():
    """Get all accounts"""
    response = requests.get('http://localhost:5000/api/accounts')
    if response.status_code == 200:
        return response.json()['accounts']
    return []

def start_session(account_id):
    """Start session for account"""
    response = requests.post(f'http://localhost:5000/api/sessions/start/{account_id}')
    return response

def main():
    print("🎮 Direct Live Session Starter")
    print("===============================\n")
    
    # Get accounts
    accounts = get_accounts()
    
    if not accounts:
        print("❌ No accounts found")
        return
    
    print("📋 Available accounts:")
    for acc in accounts:
        print(f"   ID: {acc['id']} | Username: @{acc['username']} | Status: {acc['status']}")
    
    # Find target accounts
    target_usernames = ['rhianladiku19', 'ayhiefachri']
    target_accounts = []
    
    for acc in accounts:
        if acc['username'] in target_usernames:
            target_accounts.append(acc)
    
    if not target_accounts:
        print(f"\n❌ Target accounts not found: {target_usernames}")
        print("💡 Available accounts:")
        for acc in accounts:
            print(f"   • @{acc['username']}")
        return
    
    print(f"\n🎯 Found target accounts:")
    for acc in target_accounts:
        print(f"   • @{acc['username']} (ID: {acc['id']})")
    
    # Start sessions
    print(f"\n🚀 Starting live tracking sessions...")
    
    successful_starts = []
    
    for acc in target_accounts:
        print(f"\n📡 Starting session for @{acc['username']} (ID: {acc['id']})...")
        
        response = start_session(acc['id'])
        
        if response.status_code == 200:
            print(f"✅ Session started successfully for @{acc['username']}!")
            successful_starts.append(acc['username'])
        else:
            print(f"⚠️ Failed to start session for @{acc['username']}: {response.status_code}")
            print(f"Response: {response.text}")
    
    # Summary
    print(f"\n📊 SESSION START RESULTS:")
    print(f"   Total attempted: {len(target_accounts)}")
    print(f"   Successful: {len(successful_starts)}")
    
    if successful_starts:
        print(f"\n🎉 ACTIVE LIVE TRACKING:")
        for username in successful_starts:
            print(f"   • @{username}")
        
        print(f"\n🌐 Monitor live events at: http://localhost:5000")
        print(f"📡 Real-time gift, comment, and like tracking is now active!")
        print(f"📊 Check server logs for live events")
        
    else:
        print(f"\n❌ No sessions started successfully")
        print(f"💡 This may be because the accounts are not currently live")
    
    print(f"\n🎮 Direct session starter completed!")

if __name__ == "__main__":
    main()
