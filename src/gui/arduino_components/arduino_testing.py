"""
Arduino Testing Component
========================

Handles all testing functionality for Arduino tab including:
- LED testing
- Pin testing  
- Connection testing
- Hardware diagnostics
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import json

try:
    import serial
    import serial.tools.list_ports
    SerialException = serial.SerialException
except ImportError:
    print("Warning: pyserial not available")
    serial = None
    SerialException = Exception

try:
    from arduino.controller import ArduinoController
except ImportError:
    print("Warning: ArduinoController not available")
    ArduinoController = None

class ArduinoTesting:
    """Manages all Arduino testing functionality"""
    
    def __init__(self, log_callback=None, arduino_hardware=None, arduino_tab=None):
        self.log_callback = log_callback
        self.arduino_hardware = arduino_hardware
        self.arduino_controller = None
        self.arduino_tab = arduino_tab  # Reference to Arduino tab for port access
        
        # Initialize Arduino controller if available
        if ArduinoController:
            try:
                self.arduino_controller = ArduinoController()
                if self.log_callback:
                    self.log_callback("✅ Arduino controller initialized for testing")
            except Exception as e:
                if self.log_callback:
                    self.log_callback(f"⚠️ Arduino controller init failed: {e}")
    
    def test_led_blink(self, count=3, port=None):
        """Test LED blinking functionality"""
        try:
            # Try using controller first
            if self.arduino_controller and self.arduino_controller.is_connected:
                success = self.arduino_controller.test_led_blink(count)
                if success:
                    if self.log_callback:
                        self.log_callback(f"✅ LED test command sent via controller - Arduino should blink {count} times")
                    messagebox.showinfo("LED Test", f"LED test command sent!\nArduino should blink {count} times if connected correctly.")
                    return True
                else:
                    if self.log_callback:
                        self.log_callback("❌ LED test failed via controller")
                    return False
            
            # Fallback to direct serial communication
            if not port:
                port = self._get_selected_port()
                
            if not port:
                if self.log_callback:
                    self.log_callback("❌ No port available for LED test")
                messagebox.showerror("Error", "No Arduino port found. Please connect Arduino and try again.")
                return False
                
            if not serial:
                messagebox.showerror("Error", "Serial library not available")
                return False
                
            if self.log_callback:
                self.log_callback(f"💡 Testing LED on {port}...")
            
            # Temporary connection untuk test
            test_serial = None
            try:
                test_serial = serial.Serial(port, 9600, timeout=3)
                time.sleep(0.5)  # Wait for Arduino initialization
                
                # Clear buffers
                test_serial.reset_input_buffer()
                test_serial.reset_output_buffer()
                
                # Send blink command using JSON format
                command = json.dumps({
                    "cmd": "test_led",
                    "blinks": count,
                    "interval": 200
                }) + "\n"
                
                if self.log_callback:
                    self.log_callback(f"📤 Sending LED test command: {count} blinks")
                
                test_serial.write(command.encode())
                test_serial.flush()
                
                # Wait for response with timeout
                start_time = time.time()
                response_received = False
                
                while time.time() - start_time < 5.0:  # 5 second timeout
                    if test_serial.in_waiting > 0:
                        response = test_serial.readline().decode().strip()
                        if response:
                            response_received = True
                            if self.log_callback:
                                self.log_callback(f"📟 Arduino response: {response}")
                            break
                    time.sleep(0.1)
                
                if not response_received:
                    if self.log_callback:
                        self.log_callback("⚠️ No response from Arduino, but command sent")
                
                if self.log_callback:
                    self.log_callback(f"✅ LED test command sent - Arduino should blink {count} times")
                
                messagebox.showinfo("LED Test", f"LED test command sent!\nArduino should blink {count} times if connected correctly.")
                return True
                
            except SerialException as e:
                if self.log_callback:
                    self.log_callback(f"❌ LED test failed - Serial error: {e}")
                messagebox.showerror("Test Failed", f"Could not test LED:\n{e}")
                return False
            finally:
                if test_serial:
                    test_serial.close()
                    
        except Exception as e:
            if self.log_callback:
                self.log_callback(f"❌ LED test error: {e}")
            messagebox.showerror("Error", f"LED test failed:\n{e}")
            return False
    
    def show_pin_test_dialog(self, parent_widget=None):
        """Show pin test dialog with proper error handling"""
        try:
            # Create pin selection dialog
            pin_dialog = tk.Toplevel()
            pin_dialog.title("Test Pin")
            pin_dialog.geometry("300x250")
            
            # Set parent and grab focus
            if parent_widget:
                pin_dialog.transient(parent_widget)
            pin_dialog.grab_set()
            
            # Pin selection frame
            pin_frame = ttk.Frame(pin_dialog, padding=20)
            pin_frame.pack(fill='both', expand=True)
            
            ttk.Label(pin_frame, text="Select Pin to Test:").pack(pady=(0, 10))
            
            pin_var = tk.StringVar(value="6")
            pin_entry = ttk.Entry(pin_frame, textvariable=pin_var, width=10)
            pin_entry.pack(pady=(0, 10))
            
            ttk.Label(pin_frame, text="Duration (ms):").pack(pady=(5, 5))
            
            duration_var = tk.StringVar(value="500")
            duration_entry = ttk.Entry(pin_frame, textvariable=duration_var, width=10)
            duration_entry.pack(pady=(0, 15))
            
            # Status label
            status_label = ttk.Label(pin_frame, text="", foreground='blue')
            status_label.pack(pady=(5, 10))
            
            def execute_test():
                try:
                    pin = int(pin_var.get())
                    duration = int(duration_var.get())
                    
                    # Validate pin number
                    if pin < 2 or pin > 13:
                        messagebox.showerror("Invalid Pin", "Pin must be between 2 and 13")
                        return
                        
                    # Validate duration
                    if duration < 100 or duration > 5000:
                        messagebox.showerror("Invalid Duration", "Duration must be between 100ms and 5000ms")
                        return
                    
                    status_label.config(text="Testing pin...", foreground='blue')
                    pin_dialog.update()
                    
                    # Test the pin
                    success = self.test_individual_pin(pin, duration)
                    
                    if success:
                        status_label.config(text=f"✅ Pin {pin} test completed!", foreground='green')
                        if self.log_callback:
                            self.log_callback(f"✅ Pin {pin} test command sent for {duration}ms")
                        messagebox.showinfo("Pin Test", f"Pin {pin} test command sent!\nPin should activate for {duration}ms if connected correctly.")
                    else:
                        status_label.config(text=f"❌ Pin {pin} test failed!", foreground='red')
                        if self.log_callback:
                            self.log_callback(f"❌ Pin {pin} test failed")
                        messagebox.showerror("Test Failed", f"Could not send pin {pin} test command")
                        
                except ValueError:
                    messagebox.showerror("Invalid Input", "Pin and duration must be valid numbers")
                except Exception as e:
                    if self.log_callback:
                        self.log_callback(f"❌ Pin test error: {e}")
                    messagebox.showerror("Error", f"Pin test failed:\n{e}")
            
            # Buttons frame
            btn_frame = ttk.Frame(pin_frame)
            btn_frame.pack(pady=(10, 0))
            
            ttk.Button(btn_frame, text="Test Pin", command=execute_test).pack(side='left', padx=(0, 10))
            ttk.Button(btn_frame, text="Cancel", command=pin_dialog.destroy).pack(side='left')
            
            # Focus on pin entry
            pin_entry.focus_set()
            
        except Exception as e:
            if self.log_callback:
                self.log_callback(f"❌ Pin test dialog error: {e}")
            messagebox.showerror("Error", f"Could not open pin test dialog:\n{e}")
    
    def test_individual_pin(self, pin, duration=500):
        """Test individual pin functionality using JSON commands"""
        try:
            # Validate pin number
            if not (2 <= pin <= 12):
                if self.log_callback:
                    self.log_callback(f"❌ Invalid pin number: {pin}. Valid range: 2-12")
                return False
            
            # Try using controller first
            if self.arduino_controller and self.arduino_controller.is_connected:
                success = self.arduino_controller.test_pin(pin, duration)
                if success and self.log_callback:
                    self.log_callback(f"✅ Pin {pin} test successful via controller")
                return success
            
            # Fallback to direct serial communication with JSON commands
            port = self._get_selected_port()
            if not port:
                if self.log_callback:
                    self.log_callback("❌ No port available for pin test")
                return False
                
            try:
                import serial
                with serial.Serial(port, 9600, timeout=3) as ser:
                    time.sleep(0.5)  # Arduino reset delay
                    
                    # Clear any existing data
                    ser.reset_input_buffer()
                    ser.reset_output_buffer()
                    
                    # Send JSON pin test command
                    command = json.dumps({
                        "cmd": "test_pin",
                        "pin": pin,
                        "duration": duration
                    }) + "\n"
                    
                    if self.log_callback:
                        self.log_callback(f"📤 Sending pin test command: Pin {pin}, Duration {duration}ms")
                    
                    ser.write(command.encode())
                    ser.flush()
                    
                    # Wait for response with timeout
                    start_time = time.time()
                    response_received = False
                    
                    while time.time() - start_time < 3.0:  # 3 second timeout
                        if ser.in_waiting > 0:
                            response = ser.readline().decode().strip()
                            if response:
                                response_received = True
                                if self.log_callback:
                                    self.log_callback(f"📟 Arduino response: {response}")
                                break
                        time.sleep(0.1)
                    
                    if not response_received:
                        if self.log_callback:
                            self.log_callback("⚠️ No response from Arduino, but command sent")
                    
                    if self.log_callback:
                        self.log_callback(f"✅ Pin {pin} test command sent successfully")
                    
                    return True
                    
            except SerialException as e:
                if self.log_callback:
                    self.log_callback(f"❌ Pin test serial error: {e}")
                return False
            
        except Exception as e:
            if self.log_callback:
                self.log_callback(f"❌ Pin test error: {e}")
            return False
            
    def _get_selected_port(self):
        """Get currently selected port from Arduino tab"""
        try:
            # Try to get port from Arduino tab
            if (self.arduino_tab and 
                hasattr(self.arduino_tab, 'port_var') and 
                self.arduino_tab.port_var):
                port_selection = self.arduino_tab.port_var.get()
                if port_selection and ' - ' in port_selection:
                    return port_selection.split(' - ')[0]
                if port_selection and port_selection != "Select Port":
                    return port_selection
                
            # Try to get from Arduino controller
            if (self.arduino_controller and 
                hasattr(self.arduino_controller, 'port') and 
                self.arduino_controller.port):
                return self.arduino_controller.port
                
            # Try to get from hardware component
            if (self.arduino_hardware and 
                hasattr(self.arduino_hardware, 'serial_port') and 
                self.arduino_hardware.serial_port):
                return self.arduino_hardware.serial_port
            
            # Auto-detect Arduino port as fallback
            if serial:
                ports = serial.tools.list_ports.comports()
                for port in ports:
                    # Look for Arduino or common USB-to-serial chips
                    description = port.description.lower()
                    if ('arduino' in description or 'ch340' in description or 
                        'cp210' in description or 'ftdi' in description or
                        'usb-serial' in description):
                        if self.log_callback:
                            self.log_callback(f"🔍 Auto-detected Arduino port: {port.device}")
                        return port.device
                        
                # If no Arduino-like device found, try first available COM port
                if ports:
                    if self.log_callback:
                        self.log_callback(f"⚠️ Using first available port: {ports[0].device}")
                    return ports[0].device
                
            return None
        except Exception as e:
            if self.log_callback:
                self.log_callback(f"❌ Port detection error: {e}")
            return None
    
    def test_connection_ping(self):
        """Test Arduino connection with ping"""
        try:
            if self.arduino_controller and self.arduino_controller.is_connected:
                # Send ping command
                response = self.arduino_controller._send_command({"cmd": "ping"})
                if response:
                    if self.log_callback:
                        self.log_callback("✅ Arduino ping successful")
                    return True
                else:
                    if self.log_callback:
                        self.log_callback("❌ Arduino ping failed")
                    return False
            
            if self.log_callback:
                self.log_callback("❌ Arduino not connected for ping test")
            return False
            
        except Exception as e:
            if self.log_callback:
                self.log_callback(f"❌ Ping test error: {e}")
            return False
    
    def get_controller_status(self):
        """Get Arduino controller status"""
        try:
            if self.arduino_controller:
                return {
                    'available': True,
                    'connected': self.arduino_controller.is_connected,
                    'port': getattr(self.arduino_controller, 'port', None),
                    'stats': self.arduino_controller.get_stats() if hasattr(self.arduino_controller, 'get_stats') else {}
                }
            else:
                return {
                    'available': False,
                    'connected': False,
                    'port': None,
                    'stats': {}
                }
        except Exception as e:
            return {
                'available': False,
                'connected': False,
                'port': None,
                'error': str(e),
                'stats': {}
            }
