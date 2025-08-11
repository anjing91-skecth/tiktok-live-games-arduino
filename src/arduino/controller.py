"""
Arduino Controller - Serial Communication Handler
===============================================

Handles all communication between PC and Arduino for TikTok Live events.
Provides high-level interface for pin triggering and status monitoring.
"""

import serial
import json
import time
import logging
import threading
from typing import Dict, List, Optional, Callable, Any
import serial.tools.list_ports


class ArduinoController:
    """Main Arduino communication controller"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.serial_connection: Optional[serial.Serial] = None
        self.port: Optional[str] = None
        self.baud_rate = 9600
        self.timeout = 2.0
        
        # Connection status
        self.is_connected = False
        self.device_info = {}
        
        # Event callbacks
        self.status_callbacks: List[Callable] = []
        self.error_callbacks: List[Callable] = []
        
        # Statistics
        self.stats = {
            'commands_sent': 0,
            'commands_successful': 0,
            'commands_failed': 0,
            'connection_attempts': 0,
            'last_command_time': None
        }
        
    def add_status_callback(self, callback: Callable):
        """Add callback for status updates"""
        self.status_callbacks.append(callback)
        
    def add_error_callback(self, callback: Callable):
        """Add callback for error notifications"""
        self.error_callbacks.append(callback)
        
    def _notify_status(self, status: str, message: str, data: Any = None):
        """Notify status callbacks"""
        for callback in self.status_callbacks:
            try:
                callback(status, message, data)
            except Exception as e:
                self.logger.error(f"Status callback error: {e}")
                
    def _notify_error(self, error: str, details: str = ""):
        """Notify error callbacks"""
        for callback in self.error_callbacks:
            try:
                callback(error, details)
            except Exception as e:
                self.logger.error(f"Error callback error: {e}")
    
    def scan_ports(self) -> List[Dict[str, str]]:
        """Scan for available serial ports"""
        ports = []
        for port in serial.tools.list_ports.comports():
            port_info = {
                'port': port.device,
                'description': port.description,
                'hwid': port.hwid,
                'manufacturer': port.manufacturer or 'Unknown',
                'serial_number': port.serial_number or 'Unknown'
            }
            ports.append(port_info)
            
        self.logger.info(f"Found {len(ports)} serial ports")
        return ports
    
    def detect_arduino(self, ports: Optional[List[Dict]] = None) -> Optional[Dict[str, str]]:
        """Auto-detect Arduino device"""
        if ports is None:
            ports = self.scan_ports()
            
        arduino_indicators = ['arduino', 'ch340', 'cp210', 'ftdi']
        
        for port_info in ports:
            description = port_info['description'].lower()
            manufacturer = port_info['manufacturer'].lower()
            
            # Check for Arduino indicators
            for indicator in arduino_indicators:
                if indicator in description or indicator in manufacturer:
                    self.logger.info(f"Arduino detected on {port_info['port']}: {port_info['description']}")
                    return port_info
                    
        return None
    
    def connect(self, port: Optional[str] = None) -> bool:
        """Connect to Arduino"""
        try:
            if port is None:
                # Auto-detect Arduino
                arduino_port = self.detect_arduino()
                if not arduino_port:
                    self._notify_error("No Arduino detected", "Please check USB connection")
                    return False
                port = arduino_port['port']
                
            self.stats['connection_attempts'] += 1
            
            # Close existing connection
            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.close()
                
            # Open new connection
            self.serial_connection = serial.Serial(
                port=port,
                baudrate=self.baud_rate,
                timeout=self.timeout,
                write_timeout=self.timeout
            )
            
            # Wait for Arduino to initialize
            time.sleep(3)  # Increased from 2 to 3 seconds
            
            # Clear any startup messages
            while self.serial_connection.in_waiting > 0:
                startup_msg = self.serial_connection.readline().decode().strip()
                if startup_msg:
                    self.logger.info(f"Arduino startup: {startup_msg}")
            
            # Test connection with ping
            if self._test_connection():
                self.port = port
                self.is_connected = True
                self._notify_status("connected", f"Arduino connected on {port}")
                self.logger.info(f"✅ Arduino connected successfully on {port}")
                return True
            else:
                self.serial_connection.close()
                self._notify_error("Connection test failed", f"Arduino on {port} did not respond")
                return False
                
        except serial.SerialException as e:
            self._notify_error("Serial connection failed", str(e))
            self.logger.error(f"Serial connection failed: {e}")
            return False
        except Exception as e:
            self._notify_error("Unexpected connection error", str(e))
            self.logger.error(f"Unexpected connection error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from Arduino"""
        try:
            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.close()
                
            self.is_connected = False
            self.port = None
            self._notify_status("disconnected", "Arduino disconnected")
            self.logger.info("Arduino disconnected")
            
        except Exception as e:
            self.logger.error(f"Error during disconnect: {e}")
    
    def _test_connection(self) -> bool:
        """Test Arduino connection with ping command"""
        try:
            response = self._send_command({"cmd": "ping"}, timeout=5.0)  # Increased timeout
            return bool(response and response.get("status") == "pong")
        except Exception:
            return False
    
    def _send_command(self, command: Dict, timeout: Optional[float] = None) -> Optional[Dict]:
        """Send command to Arduino and wait for response"""
        if not self.serial_connection or not self.serial_connection.is_open:
            self._notify_error("Not connected", "Arduino not connected")
            return None
            
        try:
            self.stats['commands_sent'] += 1
            self.stats['last_command_time'] = time.time()
            
            # Send command as JSON
            command_str = json.dumps(command) + '\n'  # Fixed: single backslash for actual newline
            self.logger.debug(f"Sending command: {command_str.strip()}")
            self.serial_connection.write(command_str.encode())
            
            # Wait for response
            response_timeout = timeout or self.timeout
            start_time = time.time()
            
            while (time.time() - start_time) < response_timeout:
                if self.serial_connection.in_waiting > 0:
                    response_str = self.serial_connection.readline().decode().strip()
                    self.logger.debug(f"Received response: {response_str}")
                    if response_str:
                        try:
                            response = json.loads(response_str)
                            self.stats['commands_successful'] += 1
                            self.logger.debug(f"Parsed response: {response}")
                            return response
                        except json.JSONDecodeError as e:
                            self.logger.error(f"Invalid JSON response: {response_str}")
                            continue
                            
                time.sleep(0.01)  # Small delay to prevent busy waiting
                
            # Timeout occurred
            self.stats['commands_failed'] += 1
            self.logger.error(f"Command timeout after {response_timeout}s for: {command}")
            self._notify_error("Command timeout", f"No response for: {command}")
            return None
            
        except Exception as e:
            self.stats['commands_failed'] += 1
            self._notify_error("Command send failed", str(e))
            self.logger.error(f"Error sending command: {e}")
            return None
    
    def test_led(self, blinks: int = 3, interval: int = 200) -> bool:
        """Test connection LED"""
        command = {
            "cmd": "test_led",
            "blinks": blinks,
            "interval": interval
        }
        
        response = self._send_command(command)
        if response and response.get("status") == "ok":
            self._notify_status("led_test", "LED test completed", response)
            return True
        return False
    
    def trigger_pins(self, pins: List[int], duration: int = 100) -> bool:
        """Trigger pins simultaneously"""
        command = {
            "cmd": "trigger",
            "pins": pins,
            "duration": max(duration, 50)  # Minimum 50ms
        }
        
        response = self._send_command(command)
        if response and response.get("status") == "ok":
            self._notify_status("pins_triggered", "Pins triggered successfully", response)
            return True
        else:
            error_msg = response.get("message", "Unknown error") if response else "No response"
            self._notify_error("Pin trigger failed", error_msg)
            return False
    
    def trigger_pins_sequential(self, pins: List[int], duration: int = 100,
                              delay: int = 50, cycles: int = 1) -> bool:
        """Trigger pins sequentially"""
        command = {
            "cmd": "trigger_seq",
            "pins": pins,
            "duration": max(duration, 50),
            "delay": delay,
            "cycles": cycles
        }
        
        # Calculate dynamic timeout based on complexity
        # Formula: (pins * duration + (pins-1) * delay) * cycles + inter-cycle delays + buffer
        execution_time = (len(pins) * duration + (len(pins) - 1) * delay) * cycles
        inter_cycle_time = (cycles - 1) * delay * 2 if cycles > 1 else 0
        estimated_time = (execution_time + inter_cycle_time) / 1000.0  # Convert to seconds
        timeout = max(estimated_time + 1.0, self.timeout)  # Add 1s buffer, minimum default timeout
        
        self.logger.debug(f"Sequential trigger timeout: {timeout:.1f}s (estimated: {estimated_time:.1f}s)")
        
        response = self._send_command(command, timeout=timeout)
        if response and response.get("status") == "ok":
            self._notify_status("sequential_triggered", "Sequential trigger completed", response)
            return True
        else:
            error_msg = response.get("message", "Unknown error") if response else "No response"
            self._notify_error("Sequential trigger failed", error_msg)
            return False
    
    def get_pin_status(self) -> Optional[Dict]:
        """Get current pin status from Arduino"""
        response = self._send_command({"cmd": "pin_status"})
        return response
    
    def test_led_blink(self, count: int = 3) -> bool:
        """Test LED blinking functionality using JSON command"""
        if not self.is_connected or not self.serial_connection:
            self._notify_error("Arduino not connected")
            return False
            
        try:
            # Use JSON command format for consistency
            command = {
                "cmd": "test_led",
                "blinks": count,
                "interval": 200
            }
            
            response = self._send_command(command)
            if response and response.get("status") == "ok":
                self._notify_status("led_test", f"LED test completed - {count} blinks", 
                                  {"count": count})
                self.logger.info(f"LED blink test completed: {count} blinks")
                return True
            else:
                error_msg = response.get("message", "Unknown error") if response else "No response"
                self._notify_error("LED test failed", error_msg)
                return False
                
        except Exception as e:
            self.logger.error(f"LED blink test error: {e}")
            self._notify_error("LED test failed", str(e))
            return False
    
    def test_pin(self, pin: int, duration: int = 500) -> bool:
        """Test individual pin functionality using JSON command"""
        if not self.is_connected or not self.serial_connection:
            self._notify_error("Arduino not connected")
            return False
            
        try:
            # Use JSON command format for consistency
            command = {
                "cmd": "test_pin",
                "pin": pin,
                "duration": duration
            }
            
            response = self._send_command(command)
            if response and response.get("status") == "ok":
                self._notify_status("pin_test", f"Pin {pin} test completed", 
                                  {"pin": pin, "duration": duration})
                self.logger.info(f"Pin {pin} test completed successfully")
                return True
            else:
                error_msg = response.get("message", "Unknown error") if response else "No response"
                self._notify_error("Pin test failed", error_msg)
                return False
                
        except Exception as e:
            self.logger.error(f"Pin test error: {e}")
            self._notify_error("Pin test failed", str(e))
            return False
    
    def get_stats(self) -> Dict:
        """Get controller statistics"""
        return {
            **self.stats,
            'is_connected': self.is_connected,
            'port': self.port,
            'success_rate': (
                self.stats['commands_successful'] / self.stats['commands_sent'] * 100
                if self.stats['commands_sent'] > 0 else 0
            )
        }
    
    def __del__(self):
        """Cleanup on destruction"""
        try:
            self.disconnect()
        except:
            pass
