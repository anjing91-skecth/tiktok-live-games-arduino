"""
Arduino Hardware Communication Component
======================================

Handles all Arduino hardware communication and port management.
Extracted from arduino_tab.py for better maintainability.
"""

import serial
import serial.tools.list_ports
from typing import List, Dict, Any, Optional
import threading
import time


class ArduinoHardware:
    """Manages Arduino hardware communication and port operations"""
    
    def __init__(self, log_callback=None):
        """Initialize Arduino hardware manager"""
        self.log_message = log_callback or print
        self.arduino_connected = False
        self.arduino_serial = None
        self.available_ports = []
        
    def scan_ports(self) -> List[str]:
        """Scan for available serial ports"""
        try:
            ports = serial.tools.list_ports.comports()
            available_ports = []
            
            for port in ports:
                available_ports.append(port.device)
                
            self.available_ports = available_ports
            self.log_message(f"🔍 Found {len(available_ports)} serial ports")
            return available_ports
            
        except Exception as e:
            self.log_message(f"❌ Error scanning ports: {e}")
            return []
    
    def connect(self, port: str, baudrate: int = 9600) -> bool:
        """Connect to Arduino on specified port"""
        try:
            if self.arduino_connected:
                self.log_message("⚠️ Arduino already connected")
                return False
                
            self.arduino_serial = serial.Serial(port, baudrate, timeout=1)
            time.sleep(2)  # Wait for Arduino reset
            
            self.arduino_connected = True
            self.log_message(f"✅ Arduino connected on {port}")
            return True
            
        except serial.SerialException as e:
            self.log_message(f"❌ Connection failed: {e}")
            return False
        except Exception as e:
            self.log_message(f"❌ Unexpected error: {e}")
            return False
    
    def disconnect(self) -> bool:
        """Disconnect from Arduino"""
        try:
            if not self.arduino_connected:
                self.log_message("⚠️ Arduino not connected")
                return False
                
            if self.arduino_serial:
                self.arduino_serial.close()
                self.arduino_serial = None
                
            self.arduino_connected = False
            self.log_message("🔌 Arduino disconnected")
            return True
            
        except Exception as e:
            self.log_message(f"❌ Disconnect error: {e}")
            return False
    
    def send_command(self, command: str) -> bool:
        """Send command to Arduino"""
        try:
            if not self.arduino_connected or not self.arduino_serial:
                self.log_message("❌ Arduino not connected")
                return False
                
            self.arduino_serial.write(f"{command}\n".encode())
            self.log_message(f"📤 Sent: {command}")
            return True
            
        except Exception as e:
            self.log_message(f"❌ Send error: {e}")
            return False
    
    def test_led(self, port: str) -> bool:
        """Test LED on Arduino"""
        try:
            test_serial = serial.Serial(port, 9600, timeout=1)
            time.sleep(2)
            
            test_serial.write(b"LED_TEST\n")
            time.sleep(1)
            
            test_serial.close()
            self.log_message("✅ LED test completed")
            return True
            
        except Exception as e:
            self.log_message(f"❌ LED test failed: {e}")
            return False
    
    def is_connected(self) -> bool:
        """Check if Arduino is connected"""
        return self.arduino_connected
    
    def get_port_info(self) -> Dict[str, Any]:
        """Get current port information"""
        return {
            'connected': self.arduino_connected,
            'port': self.arduino_serial.port if self.arduino_serial else None,
            'available_ports': self.available_ports
        }
