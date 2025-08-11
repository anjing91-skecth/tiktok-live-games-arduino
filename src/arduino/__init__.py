"""
Arduino Integration Package
==========================

Arduino hardware control for TikTok Live interactions.
Provides serial communication, pin control, and device detection.
"""

from .controller import ArduinoController
from .port_scanner import PortScanner

__all__ = ['ArduinoController', 'PortScanner']
