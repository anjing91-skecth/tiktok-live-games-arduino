"""
Unicode-compatible logging configuration for Windows systems
Fixes emoji and special character logging issues on Windows console
"""

import logging
import sys
import os
from datetime import datetime


class UnicodeStreamHandler(logging.StreamHandler):
    """Custom stream handler that properly handles Unicode characters on Windows"""
    
    def __init__(self, stream=None):
        super().__init__(stream)
        
    def emit(self, record):
        try:
            msg = self.format(record)
            
            # Handle Windows console encoding issues
            if sys.platform == 'win32' and hasattr(self.stream, 'buffer'):
                # Try to encode to UTF-8 bytes for Windows console
                try:
                    msg_bytes = msg.encode('utf-8', errors='replace')
                    self.stream.buffer.write(msg_bytes + b'\n')
                    self.stream.buffer.flush()
                    return
                except (AttributeError, UnicodeEncodeError):
                    pass
            
            # Fallback: Replace problematic Unicode characters
            clean_msg = self._clean_unicode(msg)
            self.stream.write(clean_msg + self.terminator)
            self.flush()
            
        except Exception:
            self.handleError(record)
    
    def _clean_unicode(self, text):
        """Replace problematic Unicode characters with ASCII equivalents"""
        replacements = {
            '🎮': '[GAME]',
            '🚀': '[START]',
            '📊': '[DASHBOARD]',
            '📡': '[SIGNAL]',
            '⚡': '[POWER]',
            '🔄': '[LOADING]',
            '💥': '[ERROR]',
            '❌': '[FAIL]',
            '✅': '[OK]',
            '⚠️': '[WARNING]',
            '💡': '[INFO]',
            '⏱️': '[TIME]',
            '🎁': '[GIFT]',
            '💬': '[COMMENT]',
            '👍': '[LIKE]',
            '🌟': '[STAR]',
            '🔥': '[HOT]',
            '💎': '[DIAMOND]',
            '🎯': '[TARGET]',
            '🎪': '[CIRCUS]',
            '🎭': '[MASK]',
            '🎨': '[ART]',
            '🏆': '[TROPHY]',
            '💝': '[GIFT_BOX]',
            '🌈': '[RAINBOW]',
            '⭐': '[STAR2]',
            '💫': '[STARS]',
            '🎊': '[CONFETTI]',
            '🎉': '[PARTY]',
            '✨': '[SPARKLE]',
            '🔊': '[SOUND]',
            '🎵': '[MUSIC]',
            '🎶': '[NOTES]'
        }
        
        clean_text = text
        for emoji, replacement in replacements.items():
            clean_text = clean_text.replace(emoji, replacement)
        
        # Remove any remaining non-ASCII characters
        clean_text = clean_text.encode('ascii', errors='replace').decode('ascii')
        
        return clean_text


def setup_unicode_logging(name, level=logging.INFO):
    """
    Setup Unicode-compatible logging for Windows systems
    
    Args:
        name: Logger name
        level: Logging level
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create custom Unicode handler for console
    console_handler = UnicodeStreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(console_handler)
    logger.setLevel(level)
    logger.propagate = False
    
    return logger


def get_safe_emoji_logger(name, level=logging.INFO):
    """
    Get a logger that safely handles emojis on all platforms
    
    Args:
        name: Logger name  
        level: Logging level
    
    Returns:
        Logger instance with safe Unicode handling
    """
    return setup_unicode_logging(name, level)


class SafeEmojiFormatter:
    """Utility class for safe emoji formatting in log messages"""
    
    EMOJI_MAP = {
        'game': '🎮' if sys.platform != 'win32' else '[GAME]',
        'start': '🚀' if sys.platform != 'win32' else '[START]',
        'dashboard': '📊' if sys.platform != 'win32' else '[DASHBOARD]',
        'signal': '📡' if sys.platform != 'win32' else '[SIGNAL]',
        'power': '⚡' if sys.platform != 'win32' else '[POWER]',
        'loading': '🔄' if sys.platform != 'win32' else '[LOADING]',
        'error': '💥' if sys.platform != 'win32' else '[ERROR]',
        'fail': '❌' if sys.platform != 'win32' else '[FAIL]',
        'ok': '✅' if sys.platform != 'win32' else '[OK]',
        'warning': '⚠️' if sys.platform != 'win32' else '[WARNING]',
        'info': '💡' if sys.platform != 'win32' else '[INFO]',
        'time': '⏱️' if sys.platform != 'win32' else '[TIME]',
        'gift': '🎁' if sys.platform != 'win32' else '[GIFT]',
        'comment': '💬' if sys.platform != 'win32' else '[COMMENT]',
        'like': '👍' if sys.platform != 'win32' else '[LIKE]',
        'star': '🌟' if sys.platform != 'win32' else '[STAR]',
        'hot': '🔥' if sys.platform != 'win32' else '[HOT]',
        'diamond': '💎' if sys.platform != 'win32' else '[DIAMOND]'
    }
    
    @classmethod
    def format(cls, emoji_name):
        """Get platform-appropriate emoji or fallback"""
        return cls.EMOJI_MAP.get(emoji_name, f'[{emoji_name.upper()}]')
    
    @classmethod
    def safe_format(cls, message, **emoji_kwargs):
        """Format message with safe emojis"""
        for key, emoji_name in emoji_kwargs.items():
            # Convert emoji_name to string if it's not already
            emoji_name_str = str(emoji_name)
            
            # Special handling for username - don't format as emoji
            if key == 'username':
                emoji = emoji_name_str.upper()  # Just uppercase the username
            else:
                emoji = cls.format(emoji_name_str)
            
            message = message.replace(f'{{{key}}}', emoji)
        return message


# Export main functions
__all__ = ['setup_unicode_logging', 'get_safe_emoji_logger', 'SafeEmojiFormatter', 'UnicodeStreamHandler']
