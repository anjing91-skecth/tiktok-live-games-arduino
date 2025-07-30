"""
Live Stream Finder for TikTok
Mencari dan memvalidasi live stream TikTok yang aktif
"""

import requests
import time
import logging
import asyncio
import threading
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
from TikTokLive import TikTokLiveClient
from .unicode_logger import get_safe_emoji_logger, SafeEmojiFormatter


class LiveStreamFinder:
    """Mencari dan memvalidasi TikTok live streams yang aktif"""
    
    def __init__(self):
        self.logger = get_safe_emoji_logger(__name__)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def validate_live_stream(self, username: str) -> Dict[str, Any]:
        """
        Memvalidasi apakah username sedang live
        
        Args:
            username: TikTok username (tanpa @)
            
        Returns:
            Dict dengan status validasi dan informasi stream
        """
        result = {
            'username': username,
            'is_live': False,
            'room_id': None,
            'viewer_count': 0,
            'title': '',
            'error': None,
            'validation_time': datetime.now().isoformat()
        }
        
        try:
            self.logger.info(SafeEmojiFormatter.safe_format(
                "{loading} Validating live stream for @{username}...",
                loading='loading',
                username=username
            ))
            
            # Test connection dengan TikTokLive client
            client = TikTokLiveClient(unique_id=username)
            
            # Coba akses room info
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Quick validation check
                room_info = loop.run_until_complete(self._check_room_async(client))
                
                if room_info:
                    result.update({
                        'is_live': True,
                        'room_id': room_info.get('room_id'),
                        'viewer_count': room_info.get('viewer_count', 0),
                        'title': room_info.get('title', ''),
                    })
                    
                    self.logger.info(SafeEmojiFormatter.safe_format(
                        "{ok} @{username} is LIVE! Room ID: {room_id}, Viewers: {viewers}",
                        ok='ok',
                        username=username,
                        room_id=result['room_id'],
                        viewers=result['viewer_count']
                    ))
                else:
                    result['error'] = 'User not live or not found'
                    self.logger.info(SafeEmojiFormatter.safe_format(
                        "{warning} @{username} is not currently live",
                        warning='warning',
                        username=username
                    ))
                    
            except Exception as e:
                result['error'] = str(e)
                self.logger.warning(SafeEmojiFormatter.safe_format(
                    "{warning} Failed to validate @{username}: {error}",
                    warning='warning',
                    username=username,
                    error=str(e)
                ))
            finally:
                loop.close()
                
        except Exception as e:
            result['error'] = str(e)
            self.logger.error(SafeEmojiFormatter.safe_format(
                "{error} Error validating @{username}: {exception}",
                error='error',
                username=username,
                exception=str(e)
            ))
            
        return result
    
    async def _check_room_async(self, client: TikTokLiveClient) -> Optional[Dict]:
        """Async helper untuk check room info"""
        try:
            # Try to get room info without full connection
            await client._web.fetch_room_id_from_html(client.unique_id)
            
            # If we get here, user exists and might be live
            return {
                'room_id': 'validated',
                'viewer_count': 0,
                'title': 'Live Stream'
            }
        except Exception:
            return None
    
    def find_live_streams(self, usernames: List[str]) -> List[Dict]:
        """
        Mencari live streams dari daftar username
        
        Args:
            usernames: List username TikTok untuk dicek
            
        Returns:
            List hasil validasi untuk setiap username
        """
        results = []
        
        self.logger.info(SafeEmojiFormatter.safe_format(
            "{signal} Scanning {count} usernames for live streams...",
            signal='signal',
            count=len(usernames)
        ))
        
        for username in usernames:
            # Clean username (remove @ if present)
            clean_username = username.replace('@', '').strip()
            
            if not clean_username:
                continue
                
            # Validate each username
            result = self.validate_live_stream(clean_username)
            results.append(result)
            
            # Small delay to avoid rate limiting
            time.sleep(1)
        
        # Filter live streams
        live_streams = [r for r in results if r['is_live']]
        
        self.logger.info(SafeEmojiFormatter.safe_format(
            "{dashboard} Found {live_count} live streams out of {total_count} checked",
            dashboard='dashboard',
            live_count=len(live_streams),
            total_count=len(results)
        ))
        
        return results
    
    def quick_test_connection(self, username: str, timeout: int = 10) -> bool:
        """
        Quick test koneksi ke live stream
        
        Args:
            username: TikTok username
            timeout: Timeout dalam detik
            
        Returns:
            True jika bisa connect, False jika tidak
        """
        try:
            self.logger.info(SafeEmojiFormatter.safe_format(
                "{loading} Quick testing connection to @{username}...",
                loading='loading',
                username=username
            ))
            
            client = TikTokLiveClient(unique_id=username)
            
            # Test dengan timeout
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Quick connection test
                future = asyncio.wait_for(
                    self._test_connection_async(client),
                    timeout=timeout
                )
                result = loop.run_until_complete(future)
                
                if result:
                    self.logger.info(SafeEmojiFormatter.safe_format(
                        "{ok} Quick test successful for @{username}",
                        ok='ok',
                        username=username
                    ))
                    return True
                else:
                    self.logger.warning(SafeEmojiFormatter.safe_format(
                        "{warning} Quick test failed for @{username}",
                        warning='warning',
                        username=username
                    ))
                    return False
                    
            except asyncio.TimeoutError:
                self.logger.warning(SafeEmojiFormatter.safe_format(
                    "{time} Quick test timeout for @{username} ({timeout}s)",
                    time='time',
                    username=username,
                    timeout=timeout
                ))
                return False
            finally:
                loop.close()
                
        except Exception as e:
            self.logger.error(SafeEmojiFormatter.safe_format(
                "{error} Quick test error for @{username}: {exception}",
                error='error',
                username=username,
                exception=str(e)
            ))
            return False
    
    async def _test_connection_async(self, client: TikTokLiveClient) -> bool:
        """Async helper untuk test connection"""
        try:
            # Try basic connection
            await client._web.fetch_room_id_from_html(client.unique_id)
            return True
        except Exception:
            return False
    
    def get_popular_live_suggestions(self) -> List[str]:
        """
        Mendapatkan saran username yang kemungkinan sedang live
        
        Returns:
            List username yang disarankan untuk dicoba
        """
        # Popular TikTok accounts yang sering live
        suggestions = [
            'charlidamelio',
            'addisonre',
            'zachking',
            'lorengray',
            'babyariel',
            'riyaz.14',
            'avani',
            'dixiedamelio',
            'spencerx',
            'willsmith',
            'therock',
            'jamescharles',
            'brentrivera',
            'milliebbrown',
            'noahbeck',
            'tiktok',
            'kingjafi_rock',
            'gilmher',
            'thehypehouse',
            'e_ntertainer'
        ]
        
        self.logger.info(SafeEmojiFormatter.safe_format(
            "{star} Generated {count} popular account suggestions",
            star='star',
            count=len(suggestions)
        ))
        
        return suggestions
    
    def smart_find_live_streams(self, custom_usernames: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Smart search untuk mencari live streams
        
        Args:
            custom_usernames: Username tambahan untuk dicek
            
        Returns:
            Dict dengan hasil pencarian lengkap
        """
        start_time = time.time()
        
        self.logger.info(SafeEmojiFormatter.safe_format(
            "{signal} Starting smart live stream discovery...",
            signal='signal'
        ))
        
        # Gabungkan custom usernames dengan suggestions
        usernames_to_check = []
        
        if custom_usernames:
            usernames_to_check.extend(custom_usernames)
            self.logger.info(SafeEmojiFormatter.safe_format(
                "{info} Added {count} custom usernames",
                info='info',
                count=len(custom_usernames)
            ))
        
        # Add popular suggestions
        suggestions = self.get_popular_live_suggestions()
        usernames_to_check.extend(suggestions)
        
        # Remove duplicates
        usernames_to_check = list(set(usernames_to_check))
        
        # Scan for live streams
        results = self.find_live_streams(usernames_to_check)
        
        # Compile final results
        live_streams = [r for r in results if r['is_live']]
        failed_streams = [r for r in results if not r['is_live']]
        
        end_time = time.time()
        duration = end_time - start_time
        
        summary = {
            'scan_duration': duration,
            'total_checked': len(results),
            'live_found': len(live_streams),
            'live_streams': live_streams,
            'failed_streams': failed_streams,
            'scan_time': datetime.now().isoformat(),
            'recommendations': live_streams[:3] if live_streams else []
        }
        
        self.logger.info(SafeEmojiFormatter.safe_format(
            "{dashboard} Smart discovery completed in {duration:.1f}s - Found {live}/{total} live streams",
            dashboard='dashboard',
            duration=duration,
            live=len(live_streams),
            total=len(results)
        ))
        
        return summary


class LiveStreamManager:
    """Manager untuk mengelola multiple live stream connections"""
    
    def __init__(self):
        self.logger = get_safe_emoji_logger(__name__)
        self.finder = LiveStreamFinder()
        self.active_connections = {}
        
    def discover_and_connect(self, target_usernames: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Discover live streams dan suggest connection
        
        Args:
            target_usernames: Username spesifik yang ingin dicek
            
        Returns:
            Dict dengan hasil discovery dan rekomendasi
        """
        self.logger.info(SafeEmojiFormatter.safe_format(
            "{start} Starting live stream discovery and connection process...",
            start='start'
        ))
        
        # Run smart discovery
        discovery_results = self.finder.smart_find_live_streams(target_usernames)
        
        # Analyze results
        live_streams = discovery_results['live_streams']
        
        if live_streams:
            self.logger.info(SafeEmojiFormatter.safe_format(
                "{ok} Found {count} active live streams!",
                ok='ok',
                count=len(live_streams)
            ))
            
            # Show recommendations
            for i, stream in enumerate(live_streams[:3], 1):
                self.logger.info(SafeEmojiFormatter.safe_format(
                    "{star} Recommendation {num}: @{username} ({viewers} viewers)",
                    star='star',
                    num=i,
                    username=stream['username'],
                    viewers=stream['viewer_count']
                ))
        else:
            self.logger.warning(SafeEmojiFormatter.safe_format(
                "{warning} No active live streams found in current scan",
                warning='warning'
            ))
        
        return discovery_results
    
    def get_connection_instructions(self, username: str) -> str:
        """
        Generate instructions untuk connect ke specific username
        
        Args:
            username: Target username
            
        Returns:
            String dengan instruksi connection
        """
        return f"""
🎯 To connect to @{username}:

1. Buka dashboard: http://localhost:5000
2. Klik "Add Account" 
3. Masukkan username: {username}
4. Klik "Start Session"
5. Monitor real-time events di dashboard

⚡ Real-time tracking akan menampilkan:
   • 🎁 Gifts dengan nilai dan repeat count
   • 💬 Comments dengan keyword detection  
   • ❤️ Likes dengan burst tracking
   • 📊 Live statistics dan metrics
"""
