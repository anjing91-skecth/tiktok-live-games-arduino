"""
Arduino Port Scanner - Serial Port Detection Utility
===================================================

Provides utilities for scanning and detecting Arduino devices
on serial ports with detailed device information.
"""

import serial
import serial.tools.list_ports
import time
import json
import logging
from typing import List, Dict, Optional, Tuple


class PortScanner:
    """Serial port scanner with Arduino detection"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def scan_all_ports(self, include_details: bool = True) -> List[Dict]:
        """Scan all available serial ports"""
        ports = []
        
        for port in serial.tools.list_ports.comports():
            port_info = {
                'port': port.device,
                'description': port.description or 'Unknown',
                'hwid': port.hwid or 'Unknown',
                'available': True
            }
            
            if include_details:
                port_info.update({
                    'manufacturer': port.manufacturer or 'Unknown',
                    'product': port.product or 'Unknown',
                    'serial_number': port.serial_number or 'Unknown',
                    'location': port.location or 'Unknown',
                    'vid': port.vid,
                    'pid': port.pid,
                    'interface': port.interface
                })
                
            ports.append(port_info)
            
        self.logger.info(f"Found {len(ports)} serial ports")
        return ports
    
    def detect_arduino_ports(self) -> List[Dict]:
        """Detect Arduino devices specifically"""
        all_ports = self.scan_all_ports()
        arduino_ports = []
        
        # Arduino identification patterns
        arduino_patterns = {
            'vid_pid': [
                (0x2341, None),    # Arduino official VID
                (0x1A86, 0x7523),  # CH340 chip (common in Arduino clones)
                (0x0403, 0x6001),  # FTDI chip
                (0x10C4, 0xEA60),  # CP210x chip
                (0x16C0, 0x0483),  # Generic USB-Serial
            ],
            'description_keywords': [
                'arduino', 'ch340', 'ch341', 'ftdi', 'cp210', 'usb serial',
                'usb-serial', 'serial port', 'com port'
            ],
            'manufacturer_keywords': [
                'arduino', 'ftdi', 'prolific', 'silicon labs', 'wch'
            ]
        }
        
        for port in all_ports:
            is_arduino = False
            confidence = 0
            reasons = []
            
            # Check VID/PID pairs
            if port.get('vid') and port.get('pid'):
                for vid, pid in arduino_patterns['vid_pid']:
                    if port['vid'] == vid and (pid is None or port['pid'] == pid):
                        is_arduino = True
                        confidence += 40
                        reasons.append(f"VID:PID match ({hex(vid)}:{hex(pid) if pid else 'any'})")
                        break
            
            # Check description keywords
            description = port['description'].lower()
            for keyword in arduino_patterns['description_keywords']:
                if keyword in description:
                    confidence += 20
                    reasons.append(f"Description contains '{keyword}'")
                    if keyword == 'arduino':
                        confidence += 20  # Extra points for explicit Arduino mention
                        is_arduino = True
                    break
            
            # Check manufacturer keywords
            manufacturer = port.get('manufacturer', '').lower()
            for keyword in arduino_patterns['manufacturer_keywords']:
                if keyword in manufacturer:
                    confidence += 15
                    reasons.append(f"Manufacturer contains '{keyword}'")
                    if keyword == 'arduino':
                        is_arduino = True
                    break
            
            # Add to Arduino ports if detected or has reasonable confidence
            if is_arduino or confidence >= 20:
                port['is_arduino'] = is_arduino
                port['confidence'] = confidence
                port['detection_reasons'] = reasons
                arduino_ports.append(port)
        
        # Sort by confidence (highest first)
        arduino_ports.sort(key=lambda x: x['confidence'], reverse=True)
        
        self.logger.info(f"Detected {len(arduino_ports)} potential Arduino ports")
        return arduino_ports
    
    def test_port_connection(self, port: str, baudrate: int = 9600, 
                           timeout: float = 2.0) -> Tuple[bool, Optional[str]]:
        """Test if a port can be opened for communication"""
        try:
            with serial.Serial(port=port, baudrate=baudrate, timeout=timeout):
                return True, "Port opened successfully"
        except serial.SerialException as e:
            return False, str(e)
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    def test_arduino_handshake(self, port: str, baudrate: int = 9600, 
                             timeout: float = 5.0) -> Tuple[bool, Optional[Dict]]:
        """Test Arduino communication with handshake"""
        try:
            ser = serial.Serial(port=port, baudrate=baudrate, timeout=2.0)
            
            # Wait for Arduino to initialize
            time.sleep(2)
            
            # Send ping command
            ping_cmd = json.dumps({"cmd": "ping"}) + "\\n"
            ser.write(ping_cmd.encode())
            
            # Wait for response
            start_time = time.time()
            while (time.time() - start_time) < timeout:
                if ser.in_waiting > 0:
                    response_str = ser.readline().decode().strip()
                    if response_str:
                        try:
                            response = json.loads(response_str)
                            ser.close()
                            
                            if response.get("status") == "pong":
                                return True, {
                                    'response': response,
                                    'response_time': time.time() - start_time,
                                    'arduino_confirmed': True
                                }
                            else:
                                return False, {
                                    'response': response,
                                    'error': 'Invalid ping response'
                                }
                        except json.JSONDecodeError:
                            continue  # Try next line
                time.sleep(0.1)
            
            ser.close()
            return False, {'error': 'Ping timeout', 'timeout': timeout}
            
        except Exception as e:
            return False, {'error': str(e)}
    
    def get_best_arduino_port(self) -> Optional[Dict]:
        """Get the most likely Arduino port"""
        arduino_ports = self.detect_arduino_ports()
        
        if not arduino_ports:
            return None
        
        # Test the most confident ports first
        for port_info in arduino_ports[:3]:  # Test top 3 candidates
            port = port_info['port']
            
            # First test basic connection
            can_connect, connect_msg = self.test_port_connection(port)
            if not can_connect:
                self.logger.debug(f"Cannot connect to {port}: {connect_msg}")
                continue
            
            # Then test Arduino handshake
            is_arduino, handshake_result = self.test_arduino_handshake(port)
            if is_arduino:
                port_info['handshake_result'] = handshake_result
                port_info['verified'] = True
                return port_info
            else:
                self.logger.debug(f"Handshake failed for {port}: {handshake_result}")
        
        # If no port responds to handshake, return the most confident one
        # (might be Arduino with different firmware)
        return arduino_ports[0] if arduino_ports else None
    
    def format_port_info(self, port_info: Dict) -> str:
        """Format port information for display"""
        lines = []
        lines.append(f"Port: {port_info['port']}")
        lines.append(f"Description: {port_info['description']}")
        
        if 'confidence' in port_info:
            lines.append(f"Arduino Confidence: {port_info['confidence']}%")
            
        if 'detection_reasons' in port_info:
            lines.append("Detection Reasons:")
            for reason in port_info['detection_reasons']:
                lines.append(f"  - {reason}")
                
        if 'handshake_result' in port_info:
            result = port_info['handshake_result']
            if result.get('arduino_confirmed'):
                lines.append(f"✅ Arduino Verified (response time: {result['response_time']:.2f}s)")
            else:
                lines.append(f"❌ Arduino Verification Failed: {result.get('error', 'Unknown')}")
        
        return "\\n".join(lines)


def main():
    """Test the port scanner"""
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='Arduino Port Scanner')
    parser.add_argument('--all', action='store_true', help='Show all ports')
    parser.add_argument('--test', action='store_true', help='Test Arduino handshake')
    parser.add_argument('--best', action='store_true', help='Find best Arduino port')
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    scanner = PortScanner()
    
    if args.all:
        ports = scanner.scan_all_ports()
        print(f"\\nFound {len(ports)} serial ports:")
        for port in ports:
            print(f"  {port['port']} - {port['description']}")
            
    elif args.best:
        best_port = scanner.get_best_arduino_port()
        if best_port:
            print("\\nBest Arduino port found:")
            print(scanner.format_port_info(best_port))
        else:
            print("\\nNo Arduino ports detected")
            
    else:
        arduino_ports = scanner.detect_arduino_ports()
        print(f"\\nFound {len(arduino_ports)} potential Arduino ports:")
        
        for i, port in enumerate(arduino_ports, 1):
            print(f"\\n{i}. {scanner.format_port_info(port)}")
            
            if args.test:
                print("   Testing handshake...")
                is_arduino, result = scanner.test_arduino_handshake(port['port'])
                if is_arduino and result:
                    print(f"   ✅ Arduino confirmed! Response time: {result['response_time']:.2f}s")
                else:
                    error_msg = result.get('error', 'Unknown') if result else 'No response'
                    print(f"   ❌ Handshake failed: {error_msg}")


if __name__ == "__main__":
    main()
