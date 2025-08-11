"""
Sound Management System - Audio Integration
==========================================

Sistema untuk manajemen dan pemutaran sound effects TikTok events
"""

import os
import sys
import json
import pygame
import threading
import time
from pathlib import Path

# Add path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

class SoundManager:
    """Sistem manajemen audio effects"""
    
    def __init__(self, sounds_folder=None):
        """Initialize sound manager
        
        Args:
            sounds_folder: Path ke folder sounds
        """
        self.sounds_folder = sounds_folder or self._get_default_sounds_folder()
        self.sounds = {}
        self.sound_mapping = {}
        self.volume = 0.7
        self.enabled = True
        self.pygame_initialized = False
        
        # Default sound mapping untuk events
        self.default_mapping = {
            'like': 'like_sound.wav',
            'follow': 'follow_celebration.wav', 
            'gift': 'gift_received.wav',
            'gift_large': 'big_gift_spectacular.wav',
            'share': 'share_notification.wav',
            'comment': 'comment_ping.wav',
            'viewer_join': 'viewer_join.wav',
            'connection_success': 'connected.wav',
            'error': 'error_sound.wav'
        }
        
        self.initialize_audio()
        self.load_sound_config()
        self.scan_sound_files()
        
    def _get_default_sounds_folder(self):
        """Get default sounds folder path"""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        return os.path.join(project_root, 'sounds')
        
    def initialize_audio(self):
        """Initialize pygame audio system"""
        try:
            pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=1024)
            pygame.mixer.init()
            self.pygame_initialized = True
            print(f"🎵 Audio system initialized successfully")
            
        except Exception as e:
            print(f"❌ Audio initialization failed: {e}")
            self.pygame_initialized = False
            self.enabled = False
            
    def load_sound_config(self):
        """Load sound configuration from file"""
        config_path = os.path.join(self.sounds_folder, 'sound_config.json')
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                self.sound_mapping = config.get('sound_mapping', self.default_mapping)
                self.volume = config.get('volume', 0.7)
                self.enabled = config.get('enabled', True)
                
                print(f"✅ Sound config loaded from {config_path}")
            else:
                # Create default config
                self.sound_mapping = self.default_mapping.copy()
                self.save_sound_config()
                print(f"📝 Created default sound config")
                
        except Exception as e:
            print(f"❌ Error loading sound config: {e}")
            self.sound_mapping = self.default_mapping.copy()
            
    def save_sound_config(self):
        """Save current sound configuration"""
        config_path = os.path.join(self.sounds_folder, 'sound_config.json')
        
        try:
            # Ensure sounds directory exists
            os.makedirs(self.sounds_folder, exist_ok=True)
            
            config = {
                'sound_mapping': self.sound_mapping,
                'volume': self.volume,
                'enabled': self.enabled,
                'last_updated': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
                
            print(f"💾 Sound config saved to {config_path}")
            
        except Exception as e:
            print(f"❌ Error saving sound config: {e}")
            
    def scan_sound_files(self):
        """Scan dan load semua sound files yang tersedia"""
        if not os.path.exists(self.sounds_folder):
            print(f"📁 Creating sounds folder: {self.sounds_folder}")
            os.makedirs(self.sounds_folder, exist_ok=True)
            return
            
        supported_formats = ['.wav', '.mp3', '.ogg']
        found_files = []
        
        for file_path in Path(self.sounds_folder).iterdir():
            if file_path.is_file() and file_path.suffix.lower() in supported_formats:
                sound_name = file_path.stem
                
                try:
                    sound = pygame.mixer.Sound(str(file_path))
                    self.sounds[sound_name] = sound
                    found_files.append(file_path.name)
                    
                except Exception as e:
                    print(f"❌ Failed to load sound {file_path.name}: {e}")
                    
        if found_files:
            print(f"🎵 Loaded {len(found_files)} sound files:")
            for file in found_files:
                print(f"   - {file}")
        else:
            print(f"⚠️  No sound files found in {self.sounds_folder}")
            print(f"   Add .wav, .mp3, or .ogg files for sound effects")
            
        return found_files
        
    def play_sound(self, event_type, volume=None):
        """Play sound untuk event tertentu
        
        Args:
            event_type: Type of event (like, follow, gift, etc.)
            volume: Custom volume (0.0 to 1.0), uses default if None
        """
        if not self.enabled or not self.pygame_initialized:
            return False
            
        try:
            # Get mapped sound file
            sound_file = self.sound_mapping.get(event_type)
            if not sound_file:
                print(f"🔇 No sound mapping for event: {event_type}")
                return False
                
            # Get sound name (without extension)
            sound_name = os.path.splitext(sound_file)[0]
            
            if sound_name not in self.sounds:
                print(f"🔇 Sound file not found: {sound_file}")
                return False
                
            # Play sound
            sound = self.sounds[sound_name]
            use_volume = volume if volume is not None else self.volume
            sound.set_volume(use_volume)
            sound.play()
            
            print(f"🔊 Playing sound: {sound_file} for {event_type}")
            return True
            
        except Exception as e:
            print(f"❌ Error playing sound for {event_type}: {e}")
            return False
            
    def play_sound_file(self, filename, volume=None):
        """Play sound file langsung berdasarkan filename
        
        Args:
            filename: Nama file sound (tanpa atau dengan extension)
            volume: Custom volume (0.0 to 1.0)
        """
        if not self.enabled or not self.pygame_initialized:
            return False
            
        try:
            # Remove extension if present
            sound_name = os.path.splitext(filename)[0]
            
            if sound_name not in self.sounds:
                print(f"🔇 Sound not found: {filename}")
                return False
                
            sound = self.sounds[sound_name]
            use_volume = volume if volume is not None else self.volume
            sound.set_volume(use_volume)
            sound.play()
            
            print(f"🔊 Playing sound file: {filename}")
            return True
            
        except Exception as e:
            print(f"❌ Error playing sound file {filename}: {e}")
            return False
            
    def test_sound(self, event_type):
        """Test sound untuk event type tertentu"""
        print(f"🧪 Testing sound for event: {event_type}")
        return self.play_sound(event_type)
        
    def test_all_sounds(self):
        """Test semua sound mappings"""
        if not self.enabled:
            print("🔇 Sound system disabled")
            return
            
        print("🧪 Testing all sound mappings...")
        
        for event_type in self.sound_mapping.keys():
            print(f"   Testing {event_type}...")
            success = self.play_sound(event_type)
            if success:
                time.sleep(1)  # Delay between sounds
            else:
                print(f"   ❌ Failed to play sound for {event_type}")
                
    def set_volume(self, volume):
        """Set master volume
        
        Args:
            volume: Volume level (0.0 to 1.0)
        """
        self.volume = max(0.0, min(1.0, volume))
        print(f"🔊 Volume set to {self.volume:.1f}")
        
    def toggle_enabled(self):
        """Toggle sound system enabled/disabled"""
        self.enabled = not self.enabled
        status = "enabled" if self.enabled else "disabled"
        print(f"🔊 Sound system {status}")
        return self.enabled
        
    def get_available_sounds(self):
        """Get list of available sound files"""
        return list(self.sounds.keys())
        
    def get_sound_mapping(self):
        """Get current sound mapping configuration"""
        return self.sound_mapping.copy()
        
    def update_sound_mapping(self, event_type, sound_file):
        """Update sound mapping untuk event type
        
        Args:
            event_type: Event type to map
            sound_file: Sound filename to map to
        """
        self.sound_mapping[event_type] = sound_file
        print(f"🎵 Updated mapping: {event_type} -> {sound_file}")
        
    def remove_sound_mapping(self, event_type):
        """Remove sound mapping untuk event type"""
        if event_type in self.sound_mapping:
            del self.sound_mapping[event_type]
            print(f"🗑️ Removed mapping for: {event_type}")
            
    def get_status(self):
        """Get current sound system status"""
        return {
            'enabled': self.enabled,
            'pygame_initialized': self.pygame_initialized,
            'volume': self.volume,
            'sounds_loaded': len(self.sounds),
            'mappings_configured': len(self.sound_mapping),
            'sounds_folder': self.sounds_folder
        }
        
    def create_sample_sounds_readme(self):
        """Create README file untuk sound samples yang dibutuhkan"""
        readme_path = os.path.join(self.sounds_folder, 'README.md')
        
        readme_content = '''# TikTok Live Sound Effects

## Required Sound Files

Place the following sound files in this directory for full audio experience:

### Event Sound Mappings

| Event Type | Filename | Description |
|------------|----------|-------------|
| Like | `like_sound.wav` | Quick pleasant sound for likes |
| Follow | `follow_celebration.wav` | Celebration sound for new followers |
| Gift | `gift_received.wav` | Standard gift received sound |
| Large Gift | `big_gift_spectacular.wav` | Spectacular sound for expensive gifts |
| Share | `share_notification.wav` | Notification sound for shares |
| Comment | `comment_ping.wav` | Ping sound for new comments |
| Viewer Join | `viewer_join.wav` | Welcome sound for new viewers |
| Connection | `connected.wav` | Success sound for connections |
| Error | `error_sound.wav` | Alert sound for errors |

### Supported Formats

- WAV (recommended for low latency)
- MP3
- OGG

### Sound Guidelines

- Keep files under 2 seconds for quick events (like, share, comment)
- Use 3-5 second sounds for celebrations (follow, large gifts)
- Recommended sample rate: 22050 Hz or 44100 Hz
- Keep file sizes reasonable (< 500KB per file)

### Free Sound Resources

- Freesound.org
- Zapsplat.com
- YouTube Audio Library
- Creative Commons sounds

### Testing

Use the GUI Arduino Control tab to test individual sounds or run:

```python
from src.audio.sound_manager import SoundManager
sm = SoundManager()
sm.test_all_sounds()
```
'''

        try:
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(readme_content)
            print(f"📝 Created sound samples README: {readme_path}")
        except Exception as e:
            print(f"❌ Error creating README: {e}")


class TikTokSoundIntegration:
    """Integration class untuk connect sound system dengan TikTok events"""
    
    def __init__(self, sound_manager=None):
        """Initialize dengan SoundManager instance"""
        self.sound_manager = sound_manager or SoundManager()
        self.event_sound_map = {
            # TikTokLive event types ke sound events
            'like': 'like',
            'follow': 'follow', 
            'gift': 'gift',
            'gift_large': 'gift_large',  # For expensive gifts
            'share': 'share',
            'comment': 'comment',
            'join': 'viewer_join'
        }
        
    def play_event_sound(self, event_type, event_data=None):
        """Play sound berdasarkan TikTok event
        
        Args:
            event_type: Type dari TikTok event
            event_data: Optional event data untuk conditional logic
        """
        try:
            # Handle gift events dengan special logic
            if event_type == 'gift' and event_data:
                gift_value = getattr(event_data, 'gift', {}).get('diamond_count', 0)
                
                # Use large gift sound untuk expensive gifts
                if gift_value >= 1000:  # Threshold for large gifts
                    sound_event = 'gift_large'
                else:
                    sound_event = 'gift'
            else:
                sound_event = self.event_sound_map.get(event_type, event_type)
                
            return self.sound_manager.play_sound(sound_event)
            
        except Exception as e:
            print(f"❌ Error playing event sound {event_type}: {e}")
            return False
            
    def get_sound_manager(self):
        """Get reference ke SoundManager instance"""
        return self.sound_manager


def test_sound_system():
    """Test function untuk sound system"""
    print("🧪 Testing Sound Management System...")
    
    # Initialize sound manager
    sm = SoundManager()
    
    # Print status
    status = sm.get_status()
    print("\n📊 Sound System Status:")
    for key, value in status.items():
        print(f"   {key}: {value}")
        
    # Test if sounds are available
    available_sounds = sm.get_available_sounds()
    print(f"\n🎵 Available sounds: {len(available_sounds)}")
    for sound in available_sounds:
        print(f"   - {sound}")
        
    # Create README if no sounds found
    if len(available_sounds) == 0:
        print("\n📝 Creating sound samples guide...")
        sm.create_sample_sounds_readme()
        
    # Test TikTok integration
    print("\n🔗 Testing TikTok integration...")
    integration = TikTokSoundIntegration(sm)
    
    # Test different event types
    test_events = ['like', 'follow', 'gift', 'comment']
    for event in test_events:
        print(f"   Testing {event} event...")
        integration.play_event_sound(event)
        time.sleep(0.5)
        
    print("✅ Sound system test completed!")
    

if __name__ == "__main__":
    test_sound_system()
