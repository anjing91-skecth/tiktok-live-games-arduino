#!/usr/bin/env python3
"""
Demo Analytics System - Live TikTok Analytics Demo
==================================================
Demo komprehensif untuk menunjukkan semua fitur analytics:
1. Real-time session tracking
2. Gift leaderboard dengan nilai akurat
3. Viewer correlation analysis
4. Export Excel dengan multiple sheets
5. Performance monitoring otomatis
6. Data retention management
"""

import asyncio
import time
import random
from datetime import datetime, timedelta
import sys
import os
from pathlib import Path

# Add src path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.analytics_manager import AnalyticsManager

class AnalyticsDemo:
    """Demo class untuk menunjukkan fitur analytics lengkap"""
    
    def __init__(self):
        print("🚀 Initializing TikTok Live Analytics Demo...")
        
        # Create analytics manager
        self.analytics_manager = AnalyticsManager("database/demo_analytics.db")
        
        # Demo data
        self.demo_session_id = f"demo_session_{int(time.time())}"
        self.demo_username = "demo_streamer"
        
        # Realistic TikTok Live data
        self.realistic_gifts = [
            # Standard gifts (most common)
            ("Rose", 1, 0.4),           # 40% probability
            ("Like", 1, 0.3),           # 30% probability  
            ("Heart", 1, 0.2),          # 20% probability
            
            # Medium value gifts
            ("Swan", 5, 0.05),          # 5% probability
            ("Love Bang", 25, 0.03),    # 3% probability
            ("Dancing Love", 25, 0.02), # 2% probability
            
            # High value gifts (rare)
            ("Castle", 50, 0.008),      # 0.8% probability
            ("Rocket", 100, 0.005),     # 0.5% probability
            ("Sports Car", 100, 0.003), # 0.3% probability
            ("Planet", 500, 0.001),     # 0.1% probability
            ("Universe", 1000, 0.0005), # 0.05% probability
        ]
        
        # Realistic user profiles for leaderboard
        self.realistic_users = [
            # Big spenders (rare but high value)
            ("richdaddy88", "Rich Daddy 💰", "whale", 1000),
            ("goldenlady", "Golden Lady ✨", "whale", 800),
            ("kingofgifts", "King of Gifts 👑", "whale", 1200),
            
            # Medium spenders (moderate frequency and value)
            ("gamerboy123", "Gamer Boy 🎮", "dolphin", 200),
            ("cutegirl456", "Cute Girl 💖", "dolphin", 150),
            ("streamfan777", "Stream Fan 🔥", "dolphin", 300),
            ("musiclover", "Music Lover 🎵", "dolphin", 180),
            ("happyviewer", "Happy Viewer 😊", "dolphin", 120),
            
            # Regular supporters (frequent but low value)
            ("supporterA", "Supporter A", "regular", 50),
            ("fanboy99", "Fan Boy", "regular", 30),
            ("viewer123", "Viewer 123", "regular", 25),
            ("follower456", "Follower 456", "regular", 40),
            ("chatmember", "Chat Member", "regular", 35),
            ("regularuser", "Regular User", "regular", 20),
            ("dailywatcher", "Daily Watcher", "regular", 45),
            
            # Casual viewers (occasional small gifts)
            ("casual1", "Casual 1", "casual", 5),
            ("casual2", "Casual 2", "casual", 8),
            ("casual3", "Casual 3", "casual", 3),
            ("newbie123", "Newbie", "casual", 2),
        ]
        
        print("✅ Analytics Demo initialized!")
    
    def print_section(self, title: str, emoji: str = "📊"):
        """Print formatted section header"""
        print(f"\n{emoji} {title}")
        print("=" * (len(title) + 3))
    
    def simulate_realistic_viewer_growth(self) -> int:
        """Simulate realistic viewer count with organic growth patterns"""
        base_viewers = 150
        time_factor = time.time() % 3600  # Hour cycle
        
        # Simulate viewer growth/decline patterns
        if time_factor < 900:  # First 15 minutes - rapid growth
            growth_factor = 1 + (time_factor / 900) * 0.8  # Up to 80% growth
        elif time_factor < 2700:  # Next 30 minutes - plateau with fluctuations
            growth_factor = 1.8 + random.uniform(-0.2, 0.3)  # ±20% to +30% variation
        else:  # Last 15 minutes - gradual decline
            decline_factor = (3600 - time_factor) / 900
            growth_factor = 1.8 * decline_factor + random.uniform(-0.1, 0.1)
        
        # Add random fluctuations
        noise = random.uniform(0.9, 1.1)
        
        return int(base_viewers * growth_factor * noise)
    
    def get_weighted_random_gift(self):
        """Get random gift based on realistic probabilities"""
        rand = random.random()
        cumulative_prob = 0
        
        for gift_name, value, probability in self.realistic_gifts:
            cumulative_prob += probability
            if rand <= cumulative_prob:
                return gift_name, value
        
        # Fallback to most common gift
        return "Rose", 1
    
    def get_realistic_user(self):
        """Get random user based on spending behavior"""
        # Weight selection based on user type
        user_type_weights = {
            "whale": 0.02,      # 2% - big spenders
            "dolphin": 0.15,    # 15% - medium spenders  
            "regular": 0.35,    # 35% - regular supporters
            "casual": 0.48      # 48% - casual viewers
        }
        
        rand = random.random()
        cumulative_weight = 0
        
        for user_type, weight in user_type_weights.items():
            cumulative_weight += weight
            if rand <= cumulative_weight:
                # Filter users by type
                type_users = [u for u in self.realistic_users if u[2] == user_type]
                if type_users:
                    return random.choice(type_users)
        
        # Fallback
        return random.choice(self.realistic_users)
    
    def simulate_gift_with_realistic_streaks(self, username: str, user_type: str, max_budget: int):
        """Simulate gift with realistic streak patterns"""
        gift_name, base_value = self.get_weighted_random_gift()
        
        # Determine repeat count based on user type and gift value
        if user_type == "whale":
            # Whales can afford big streaks
            if base_value <= 5:
                repeat_count = random.randint(5, 50)  # Many small gifts
            elif base_value <= 100:
                repeat_count = random.randint(2, 10)  # Some medium gifts
            else:
                repeat_count = random.randint(1, 3)   # Few expensive gifts
        elif user_type == "dolphin":
            # Dolphins moderate streaks
            if base_value <= 5:
                repeat_count = random.randint(2, 15)
            elif base_value <= 50:
                repeat_count = random.randint(1, 5)
            else:
                repeat_count = 1  # Single expensive gift
        elif user_type == "regular":
            # Regular users small streaks
            if base_value <= 5:
                repeat_count = random.randint(1, 8)
            else:
                repeat_count = 1
        else:  # casual
            # Casual users mostly single gifts
            repeat_count = 1 if base_value > 1 else random.randint(1, 3)
        
        # Ensure we don't exceed user's budget
        total_cost = base_value * repeat_count
        if total_cost > max_budget:
            repeat_count = max(1, max_budget // base_value)
        
        return gift_name, base_value, repeat_count
    
    async def run_realistic_demo(self, duration_minutes: int = 5):
        """Run realistic TikTok Live session simulation"""
        self.print_section("🎬 Starting Realistic TikTok Live Session Simulation", "🚀")
        
        print(f"⏱️ Simulation Duration: {duration_minutes} minutes")
        print(f"📺 Session ID: {self.demo_session_id}")
        print(f"👤 Streamer: @{self.demo_username}")
        
        # Start analytics session
        success = self.analytics_manager.start_session(self.demo_session_id, self.demo_username)
        if not success:
            print("❌ Failed to start analytics session")
            return
        
        print("✅ Analytics session started")
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        # Simulation stats
        total_events = 0
        total_gifts = 0
        total_gift_value = 0
        user_budgets = {user[0]: user[3] for user in self.realistic_users}  # Track remaining budgets
        
        print(f"\n🎯 Simulating live events...")
        
        while time.time() < end_time:
            current_time = time.time()
            elapsed = current_time - start_time
            
            # Update viewer count every 10-30 seconds
            if random.random() < 0.3:  # 30% chance each iteration
                viewer_count = self.simulate_realistic_viewer_growth()
                self.analytics_manager.track_event("viewer_update", {"count": viewer_count})
                
                if total_events % 20 == 0:  # Log occasionally
                    print(f"📊 {elapsed:.0f}s | Viewers: {viewer_count:,}")
            
            # Generate comments (frequent)
            if random.random() < 0.7:  # 70% chance
                user = random.choice(self.realistic_users)
                username, nickname, user_type, budget = user
                
                comments = [
                    "Hello! 👋", "Nice stream! 🔥", "Keep going! 💪", "Love it! ❤️",
                    "Amazing! 🎉", "So cool! 😎", "Great job! 👏", "Awesome! ⭐",
                    "Hi everyone! 😊", "Let's go! 🚀", "Perfect! 💯", "Incredible! 🤩"
                ]
                
                self.analytics_manager.track_event("comment", {
                    "username": username,
                    "nickname": nickname,
                    "comment": random.choice(comments)
                })
                total_events += 1
            
            # Generate likes (very frequent)
            if random.random() < 0.8:  # 80% chance
                user = random.choice(self.realistic_users)
                username, nickname, user_type, budget = user
                
                like_count = random.randint(1, 5) if user_type in ["whale", "dolphin"] else 1
                
                self.analytics_manager.track_event("like", {
                    "username": username,
                    "nickname": nickname,
                    "count": like_count
                })
                total_events += 1
            
            # Generate gifts (less frequent but more valuable)
            if random.random() < 0.3:  # 30% chance
                user = self.get_realistic_user()
                username, nickname, user_type, max_budget = user
                
                # Check if user still has budget
                if user_budgets[username] > 0:
                    gift_name, base_value, repeat_count = self.simulate_gift_with_realistic_streaks(
                        username, user_type, user_budgets[username]
                    )
                    
                    gift_value = base_value * repeat_count
                    user_budgets[username] -= gift_value
                    
                    self.analytics_manager.track_event("gift", {
                        "username": username,
                        "nickname": nickname,
                        "user_id": f"uid_{username}",
                        "gift_name": gift_name,
                        "repeat_count": repeat_count,
                        "estimated_value": gift_value
                    })
                    
                    total_gifts += repeat_count
                    total_gift_value += gift_value
                    total_events += 1
                    
                    # Log significant gifts
                    if gift_value >= 50:
                        print(f"🎁 BIG GIFT: {nickname} sent {repeat_count}x {gift_name} (💰 {gift_value} coins)")
            
            # Generate follows (rare)
            if random.random() < 0.05:  # 5% chance
                user = random.choice(self.realistic_users)
                username, nickname, user_type, budget = user
                
                self.analytics_manager.track_event("follow", {
                    "username": username,
                    "nickname": nickname
                })
                total_events += 1
                print(f"➕ NEW FOLLOWER: {nickname}")
            
            # Generate shares (very rare)
            if random.random() < 0.02:  # 2% chance
                user = random.choice(self.realistic_users)
                username, nickname, user_type, budget = user
                
                self.analytics_manager.track_event("share", {
                    "username": username,
                    "nickname": nickname
                })
                total_events += 1
                print(f"📤 SHARED: {nickname} shared the stream")
            
            # Small delay to simulate real-time
            await asyncio.sleep(0.1)
        
        print(f"\n📊 Simulation completed!")
        print(f"⏱️ Duration: {duration_minutes} minutes")
        print(f"📝 Total Events: {total_events:,}")
        print(f"🎁 Total Gifts: {total_gifts:,}")
        print(f"💰 Total Gift Value: {total_gift_value:,} coins")
        
        # Stop analytics session
        self.analytics_manager.stop_session()
        print("✅ Analytics session stopped")
    
    def show_session_leaderboard(self):
        """Show session gift leaderboard"""
        self.print_section("🏆 Session Gift Leaderboard")
        
        leaderboard = self.analytics_manager.get_session_leaderboard(self.demo_session_id, limit=10)
        
        if not leaderboard:
            print("No gift data available for leaderboard")
            return
        
        print(f"{'Rank':<5} {'Nickname':<20} {'Gifts':<8} {'Value':<12} {'Top Gift':<15}")
        print("-" * 65)
        
        for i, contributor in enumerate(leaderboard, 1):
            # Find most valuable gift type
            top_gift = max(contributor.gift_types.items(), key=lambda x: x[1]) if contributor.gift_types else ("None", 0)
            
            print(f"{i:<5} {contributor.nickname:<20} {contributor.total_gifts:<8} {contributor.total_value:<12.1f} {top_gift[0]:<15}")
        
        # Summary
        total_value = sum(c.total_value for c in leaderboard)
        total_gifts = sum(c.total_gifts for c in leaderboard)
        
        print(f"\n📊 Top {len(leaderboard)} Contributors Summary:")
        print(f"   💰 Total Value: {total_value:,.1f} coins")
        print(f"   🎁 Total Gifts: {total_gifts:,}")
        print(f"   👑 Top Contributor: {leaderboard[0].nickname} ({leaderboard[0].total_value:.1f} coins)")
    
    def show_global_leaderboard(self):
        """Show global gift leaderboard"""
        self.print_section("🌍 Global Gift Leaderboard (Last 30 Days)")
        
        global_leaderboard = self.analytics_manager.get_global_leaderboard(days=30, limit=10)
        
        if not global_leaderboard:
            print("No global leaderboard data available")
            return
        
        print(f"{'Rank':<5} {'Nickname':<20} {'Gifts':<8} {'Value':<12} {'Sessions':<10}")
        print("-" * 60)
        
        for entry in global_leaderboard:
            print(f"{entry['rank']:<5} {entry['nickname']:<20} {entry['total_gifts']:<8} {entry['total_value']:<12.1f} {entry['sessions_participated']:<10}")
    
    def export_analytics_data(self):
        """Export analytics data to Excel"""
        self.print_section("📤 Exporting Analytics Data to Excel")
        
        export_path = f"demo_analytics_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        print(f"📄 Exporting to: {export_path}")
        
        success = self.analytics_manager.export_to_excel(export_path)
        
        if success:
            print(f"✅ Export successful: {export_path}")
            
            # Show file info
            export_file = Path(export_path)
            if export_file.exists():
                file_size = export_file.stat().st_size
                print(f"📊 File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
                
                print(f"\n📋 Excel file contains:")
                print(f"   • Sessions sheet - session overview")
                print(f"   • Analytics_5min sheet - interval analytics")  
                print(f"   • Gift_Contributions sheet - leaderboard data")
                print(f"   • Viewer_Correlations sheet - correlation analysis")
                print(f"   • Global_Leaderboard sheet - cross-session leaderboard")
                print(f"   • Summary sheet - aggregated statistics")
            
        else:
            print("❌ Export failed")
        
        return success
    
    def show_system_performance(self):
        """Show system performance metrics"""
        self.print_section("⚡ System Performance Monitoring")
        
        perf = self.analytics_manager.performance_monitor.get_system_performance()
        
        print(f"🖥️ CPU Usage: {perf['cpu_percent']:.1f}%")
        print(f"💾 Memory Usage: {perf['memory_percent']:.1f}%")
        print(f"💿 Disk Usage: {perf['disk_percent']:.1f}%")
        
        # Recommendations
        if self.analytics_manager.performance_monitor.should_reduce_frequency():
            print("⚠️ High system load detected")
        else:
            print("✅ System performance is optimal")
        
        recommended_interval = self.analytics_manager.performance_monitor.get_recommended_interval()
        print(f"⏱️ Recommended Analytics Interval: {recommended_interval//60} minutes")
        
        # Database size
        if self.analytics_manager.db_path.exists():
            db_size = self.analytics_manager.db_path.stat().st_size
            print(f"🗄️ Database Size: {db_size:,} bytes ({db_size/1024/1024:.1f} MB)")
    
    def demonstrate_correlation_analysis(self):
        """Demonstrate viewer correlation analysis"""
        self.print_section("🔍 Viewer Behavior Correlation Analysis")
        
        print("Analyzing correlation between activities and viewer changes...")
        
        # Get correlation data from database
        import sqlite3
        with sqlite3.connect(self.analytics_manager.db_path) as conn:
            cursor = conn.execute("""
                SELECT viewer_change, comments_spike, likes_spike, gifts_spike, 
                       follows_spike, shares_spike, correlation_score
                FROM viewer_correlations 
                WHERE session_id = ?
                ORDER BY timestamp DESC
                LIMIT 10
            """, (self.demo_session_id,))
            
            correlations = cursor.fetchall()
        
        if correlations:
            print(f"\n📊 Recent Correlation Analysis (Last 10 intervals):")
            print(f"{'Viewer Δ':<10} {'Comments':<10} {'Likes':<8} {'Gifts':<8} {'Score':<8}")
            print("-" * 50)
            
            for corr in correlations:
                viewer_change, comments, likes, gifts, follows, shares, score = corr
                
                # Format spikes as indicators
                comment_ind = "📈" if comments else "📉"
                like_ind = "📈" if likes else "📉"
                gift_ind = "📈" if gifts else "📉"
                
                print(f"{viewer_change:<10} {comment_ind:<10} {like_ind:<8} {gift_ind:<8} {score:<8.2f}")
            
            # Analysis summary
            avg_score = sum(c[6] for c in correlations) / len(correlations)
            positive_correlations = sum(1 for c in correlations if c[6] > 0.5)
            
            print(f"\n🎯 Analysis Summary:")
            print(f"   📊 Average Correlation Score: {avg_score:.2f}")
            print(f"   📈 Strong Positive Correlations: {positive_correlations}/{len(correlations)}")
            
            if avg_score > 0.6:
                print(f"   ✅ Strong correlation between activities and viewer growth")
            elif avg_score > 0.3:
                print(f"   ⚠️ Moderate correlation detected")
            else:
                print(f"   ❌ Weak correlation - viewers may be influenced by external factors")
                
        else:
            print("No correlation data available for analysis")
    
    async def run_full_demo(self):
        """Run complete analytics system demonstration"""
        print("🎉 Welcome to TikTok Live Analytics System Demo!")
        print("=" * 60)
        print("This demo will showcase all analytics features:")
        print("• Real-time session tracking with realistic data")
        print("• Gift leaderboard with accurate value estimation") 
        print("• Viewer correlation analysis")
        print("• Excel export with multiple data sheets")
        print("• System performance monitoring")
        print("• Data management capabilities")
        
        input("\n⏸️ Press Enter to start the demo...")
        
        # 1. Run realistic simulation
        await self.run_realistic_demo(duration_minutes=2)  # 2 minutes for demo
        
        input("\n⏸️ Press Enter to view the results...")
        
        # 2. Show leaderboards
        self.show_session_leaderboard()
        
        input("\n⏸️ Press Enter to continue...")
        
        self.show_global_leaderboard()
        
        input("\n⏸️ Press Enter to continue...")
        
        # 3. Correlation analysis
        self.demonstrate_correlation_analysis()
        
        input("\n⏸️ Press Enter to continue...")
        
        # 4. System performance
        self.show_system_performance()
        
        input("\n⏸️ Press Enter to continue...")
        
        # 5. Export data
        export_success = self.export_analytics_data()
        
        # Final summary
        self.print_section("🎉 Demo Complete!", "🏁")
        
        print("📊 Analytics System Features Demonstrated:")
        print("✅ Real-time event tracking and aggregation")
        print("✅ Gift value estimation with realistic economics")
        print("✅ Leaderboard generation (session & global)")
        print("✅ Viewer correlation analysis")
        print("✅ Performance monitoring and optimization")
        print(f"{'✅' if export_success else '❌'} Excel export with comprehensive data")
        
        print(f"\n🚀 System Ready for Production Use!")
        print(f"   • Database: {self.analytics_manager.db_path}")
        print(f"   • Session ID: {self.demo_session_id}")
        print(f"   • Export File: {'Available' if export_success else 'Failed'}")
        
        print(f"\n💡 Integration Tips:")
        print(f"   1. Enable analytics in TikTok connector: connector.enable_analytics(analytics_manager)")
        print(f"   2. Use Statistics tab in GUI for real-time monitoring")
        print(f"   3. Set up automatic data cleanup for long-term use")
        print(f"   4. Monitor system performance for optimal intervals")

if __name__ == "__main__":
    demo = AnalyticsDemo()
    asyncio.run(demo.run_full_demo())
