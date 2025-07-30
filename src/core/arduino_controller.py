"""
Arduino Controller untuk TikTok Live Games
Mengelola komunikasi serial dengan multiple Arduino devices
"""

import serial
import serial.tools.list_ports
import threading
import time
import logging
import json
from typing import Dict, List, Optional, Any
from queue import Queue, Empty

class ArduinoController:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.connections: Dict[str, serial.Serial] = {}
        self.command_queue = Queue()
        self.is_running = False
        self.worker_thread = None
        self.device_configs: Dict[str, Dict] = {}
        
    def initialize(self, config_path: str = "config/arduino_config.json"):
        """Initialize Arduino connections from config"""
        self.logger.info("Initializing Arduino controller...")
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                self.device_configs = config.get('devices', {})
        except FileNotFoundError:
            self.logger.warning(f"Arduino config file not found: {config_path}")
            self.device_configs = {}
        except Exception as e:
            self.logger.error(f"Error loading Arduino config: {e}")
            return False
        
        # Start command processor thread
        self.is_running = True
        self.worker_thread = threading.Thread(target=self._command_processor, daemon=True)
        self.worker_thread.start()
        
        return True
    
    def scan_arduino_ports(self) -> List[Dict[str, str]]:
        """Scan for available Arduino ports"""
        ports = []
        available_ports = serial.tools.list_ports.comports()
        
        for port in available_ports:
            # Common Arduino VID/PID patterns
            arduino_patterns = [
                "2341",  # Arduino LLC
                "1A86",  # CH340 chips
                "0403",  # FTDI chips
                "10C4",  # Silicon Labs CP210x
            ]
            
            is_arduino = any(pattern in (port.vid or "") for pattern in arduino_patterns) or \
                        any(pattern in str(port.vid or 0) for pattern in arduino_patterns) or \
                        "Arduino" in (port.description or "") or \
                        "CH340" in (port.description or "") or \
                        "USB-SERIAL" in (port.description or "")
            
            ports.append({
                "port": port.device,
                "description": port.description or "Unknown",
                "hwid": port.hwid or "Unknown",
                "is_arduino": is_arduino
            })
        
        self.logger.info(f"Found {len(ports)} serial ports, {sum(1 for p in ports if p['is_arduino'])} likely Arduino")
        return ports
    
    def connect_arduino(self, port: str, account_id: str, baud_rate: int = 9600) -> bool:
        """Connect to Arduino on specific port"""
        try:
            if port in self.connections:
                self.logger.warning(f"Arduino already connected on port {port}")
                return True
            
            # Try to establish connection
            ser = serial.Serial(
                port=port,
                baudrate=baud_rate,
                timeout=1,
                write_timeout=1
            )
            
            # Wait for Arduino to initialize
            time.sleep(2)
            
            # Test connection with ping command
            test_command = "CMD:TEST:PING:0:"
            ser.write(test_command.encode() + b'\n')
            time.sleep(0.5)
            
            # Read response
            response = ser.readline().decode().strip()
            
            if "PONG" in response or "OK" in response:
                self.connections[account_id] = ser
                self.logger.info(f"Arduino connected successfully on {port} for account {account_id}")
                return True
            else:
                self.logger.warning(f"Arduino on {port} did not respond properly: {response}")
                ser.close()
                return False
                
        except serial.SerialException as e:
            self.logger.error(f"Failed to connect to Arduino on {port}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error connecting to Arduino: {e}")
            return False
    
    def disconnect_arduino(self, account_id: str):
        """Disconnect Arduino for specific account"""
        if account_id in self.connections:
            try:
                # Send stop command before disconnecting
                self.send_emergency_stop(account_id)
                time.sleep(0.5)
                
                self.connections[account_id].close()
                del self.connections[account_id]
                self.logger.info(f"Arduino disconnected for account {account_id}")
            except Exception as e:
                self.logger.error(f"Error disconnecting Arduino for account {account_id}: {e}")
    
    def send_command(self, account_id: str, device_id: str, action: str, duration: int = 1000, params: str = ""):
        """Send command to Arduino (non-blocking)"""
        command = {
            'account_id': account_id,
            'device_id': device_id,
            'action': action,
            'duration': duration,
            'params': params,
            'timestamp': time.time()
        }
        
        self.command_queue.put(command)
        self.logger.debug(f"Command queued: {command}")
    
    def send_emergency_stop(self, account_id: str):
        """Send emergency stop command (immediate)"""
        if account_id in self.connections:
            try:
                stop_command = "CMD:ALL:STOP:0:"
                self.connections[account_id].write(stop_command.encode() + b'\n')
                self.logger.warning(f"Emergency stop sent to account {account_id}")
            except Exception as e:
                self.logger.error(f"Failed to send emergency stop: {e}")
    
    def _command_processor(self):
        """Process commands from queue in separate thread"""
        self.logger.info("Arduino command processor started")
        
        while self.is_running:
            try:
                # Get command from queue with timeout
                command = self.command_queue.get(timeout=1)
                self._execute_command(command)
                self.command_queue.task_done()
                
            except Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error processing command: {e}")
        
        self.logger.info("Arduino command processor stopped")
    
    def _execute_command(self, command: Dict[str, Any]):
        """Execute single command"""
        account_id = command['account_id']
        
        if account_id not in self.connections:
            self.logger.warning(f"No Arduino connection for account {account_id}")
            return
        
        try:
            # Format command string
            cmd_string = f"CMD:{command['device_id']}:{command['action']}:{command['duration']}:{command['params']}"
            
            # Send command
            self.connections[account_id].write(cmd_string.encode() + b'\n')
            
            # Wait for response
            time.sleep(0.1)
            if self.connections[account_id].in_waiting > 0:
                response = self.connections[account_id].readline().decode().strip()
                self.logger.debug(f"Arduino response: {response}")
            
            self.logger.info(f"Command executed: {cmd_string}")
            
        except Exception as e:
            self.logger.error(f"Failed to execute command {command}: {e}")
    
    def get_connection_status(self) -> Dict[str, bool]:
        """Get connection status for all accounts"""
        status = {}
        for account_id, connection in self.connections.items():
            try:
                status[account_id] = connection.is_open
            except:
                status[account_id] = False
        return status
    
    def test_device(self, account_id: str, device_id: str) -> bool:
        """Test specific device"""
        try:
            self.send_command(account_id, device_id, "TEST", 500)
            return True
        except Exception as e:
            self.logger.error(f"Device test failed for {device_id}: {e}")
            return False
    
    def cleanup(self):
        """Cleanup connections and stop threads"""
        self.logger.info("Cleaning up Arduino controller...")
        
        # Stop command processor
        self.is_running = False
        
        # Send emergency stop to all devices
        for account_id in list(self.connections.keys()):
            self.send_emergency_stop(account_id)
            time.sleep(0.1)
        
        # Close all connections
        for account_id in list(self.connections.keys()):
            self.disconnect_arduino(account_id)
        
        # Wait for worker thread to finish
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=2)
        
        self.logger.info("Arduino controller cleanup complete")

# Device action mappings
DEVICE_ACTIONS = {
    'selenoid': {
        'push': 'PUSH',
        'pull': 'PULL',
        'toggle': 'TOGGLE'
    },
    'motor': {
        'rotate': 'ROTATE',
        'stop': 'STOP',
        'forward': 'FORWARD',
        'backward': 'BACKWARD'
    },
    'led': {
        'on': 'ON',
        'off': 'OFF',
        'blink': 'BLINK',
        'fade': 'FADE',
        'color': 'COLOR'
    },
    'servo': {
        'move': 'MOVE',
        'sweep': 'SWEEP',
        'center': 'CENTER'
    },
    'fan': {
        'on': 'ON',
        'off': 'OFF',
        'speed': 'SPEED'
    }
}
