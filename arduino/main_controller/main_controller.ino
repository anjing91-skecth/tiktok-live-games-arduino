/*
  TikTok Live Games Arduino Controller
  
  Receives commands via Serial and controls various devices:
  - Selenoids (push/pull)
  - Servo motors
  - LED strips
  - Fans
  - Buzzers
  
  Command Format: CMD:DEVICE_ID:ACTION:DURATION:PARAMS
  Example: CMD:SOL1:PUSH:2000:
  Example: CMD:LED1:COLOR:3000:255,0,0
  Example: CMD:MOT1:ROTATE:5000:90
*/

#include <Servo.h>

// Pin definitions
#define SELENOID_1_PIN 2
#define SELENOID_2_PIN 3
#define LED_STRIP_PIN 4
#define SERVO_MOTOR_PIN 9
#define FAN_PIN 5
#define BUZZER_PIN 6
#define EMERGENCY_STOP_PIN 13

// Device objects
Servo servoMotor;

// Device states
bool selenoid1_active = false;
bool selenoid2_active = false;
bool fan_active = false;
unsigned long selenoid1_stop_time = 0;
unsigned long selenoid2_stop_time = 0;
unsigned long fan_stop_time = 0;
unsigned long led_stop_time = 0;

// Command parsing
String command_buffer = "";
bool command_ready = false;

// Emergency stop
bool emergency_stop = false;

void setup() {
  Serial.begin(9600);
  
  // Initialize pins
  pinMode(SELENOID_1_PIN, OUTPUT);
  pinMode(SELENOID_2_PIN, OUTPUT);
  pinMode(LED_STRIP_PIN, OUTPUT);
  pinMode(FAN_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(EMERGENCY_STOP_PIN, INPUT_PULLUP);
  
  // Initialize servo
  servoMotor.attach(SERVO_MOTOR_PIN);
  servoMotor.write(90); // Center position
  
  // Set initial states
  digitalWrite(SELENOID_1_PIN, LOW);
  digitalWrite(SELENOID_2_PIN, LOW);
  digitalWrite(LED_STRIP_PIN, LOW);
  digitalWrite(FAN_PIN, LOW);
  digitalWrite(BUZZER_PIN, LOW);
  
  Serial.println("Arduino TikTok Live Controller Ready");
  Serial.println("Format: CMD:DEVICE_ID:ACTION:DURATION:PARAMS");
}

void loop() {
  // Check emergency stop button
  if (digitalRead(EMERGENCY_STOP_PIN) == LOW) {
    emergency_stop = true;
    stopAllDevices();
    Serial.println("EMERGENCY_STOP:HARDWARE");
  }
  
  // Read serial commands
  readSerialCommands();
  
  // Process commands
  if (command_ready && !emergency_stop) {
    processCommand(command_buffer);
    command_buffer = "";
    command_ready = false;
  }
  
  // Update device timers
  updateDeviceTimers();
  
  delay(10);
}

void readSerialCommands() {
  while (Serial.available()) {
    char c = Serial.read();
    
    if (c == '\n' || c == '\r') {
      if (command_buffer.length() > 0) {
        command_ready = true;
      }
    } else {
      command_buffer += c;
    }
  }
}

void processCommand(String cmd) {
  // Parse command: CMD:DEVICE_ID:ACTION:DURATION:PARAMS
  cmd.trim();
  
  if (!cmd.startsWith("CMD:")) {
    Serial.println("ERROR:INVALID_FORMAT");
    return;
  }
  
  // Remove CMD: prefix
  cmd = cmd.substring(4);
  
  // Split by colons
  String parts[5];
  int partCount = 0;
  int lastIndex = 0;
  
  for (int i = 0; i <= cmd.length(); i++) {
    if (i == cmd.length() || cmd.charAt(i) == ':') {
      if (partCount < 5) {
        parts[partCount] = cmd.substring(lastIndex, i);
        partCount++;
      }
      lastIndex = i + 1;
    }
  }
  
  if (partCount < 3) {
    Serial.println("ERROR:MISSING_PARAMETERS");
    return;
  }
  
  String deviceId = parts[0];
  String action = parts[1];
  int duration = parts[2].toInt();
  String params = partCount > 3 ? parts[3] : "";
  
  // Execute command
  executeDeviceCommand(deviceId, action, duration, params);
}

void executeDeviceCommand(String deviceId, String action, int duration, String params) {
  // Handle emergency stop
  if (deviceId == "ALL" && action == "STOP") {
    emergency_stop = true;
    stopAllDevices();
    Serial.println("OK:ALL_STOPPED");
    return;
  }
  
  // Reset emergency stop for normal commands
  if (emergency_stop && action != "STOP") {
    emergency_stop = false;
    Serial.println("INFO:EMERGENCY_STOP_RESET");
  }
  
  // Handle test commands
  if (action == "TEST" || action == "PING") {
    Serial.println("PONG:" + deviceId);
    return;
  }
  
  // Execute device-specific commands
  if (deviceId == "SOL1") {
    handleSelenoidCommand(1, action, duration);
  } else if (deviceId == "SOL2") {
    handleSelenoidCommand(2, action, duration);
  } else if (deviceId == "LED1") {
    handleLEDCommand(action, duration, params);
  } else if (deviceId == "MOT1") {
    handleMotorCommand(action, duration, params);
  } else if (deviceId == "FAN1") {
    handleFanCommand(action, duration);
  } else if (deviceId == "BUZ1") {
    handleBuzzerCommand(action, duration, params);
  } else {
    Serial.println("ERROR:UNKNOWN_DEVICE:" + deviceId);
    return;
  }
  
  Serial.println("OK:" + deviceId + ":" + action + ":" + String(duration));
}

void handleSelenoidCommand(int selenoidNum, String action, int duration) {
  int pin = (selenoidNum == 1) ? SELENOID_1_PIN : SELENOID_2_PIN;
  bool* active = (selenoidNum == 1) ? &selenoid1_active : &selenoid2_active;
  unsigned long* stop_time = (selenoidNum == 1) ? &selenoid1_stop_time : &selenoid2_stop_time;
  
  if (action == "PUSH" || action == "ON") {
    digitalWrite(pin, HIGH);
    *active = true;
    *stop_time = millis() + duration;
  } else if (action == "PULL" || action == "OFF") {
    digitalWrite(pin, LOW);
    *active = false;
    *stop_time = 0;
  } else if (action == "TOGGLE") {
    digitalWrite(pin, !digitalRead(pin));
    *active = digitalRead(pin);
    if (*active) {
      *stop_time = millis() + duration;
    } else {
      *stop_time = 0;
    }
  }
}

void handleLEDCommand(String action, int duration, String params) {
  if (action == "ON" || action == "BLINK") {
    digitalWrite(LED_STRIP_PIN, HIGH);
    led_stop_time = millis() + duration;
  } else if (action == "OFF") {
    digitalWrite(LED_STRIP_PIN, LOW);
    led_stop_time = 0;
  } else if (action == "FLASH") {
    // Simple flash pattern
    for (int i = 0; i < 5; i++) {
      digitalWrite(LED_STRIP_PIN, HIGH);
      delay(100);
      digitalWrite(LED_STRIP_PIN, LOW);
      delay(100);
    }
    led_stop_time = 0;
  } else if (action == "COLOR") {
    // For RGB LED strips (simplified - just turn on)
    digitalWrite(LED_STRIP_PIN, HIGH);
    led_stop_time = millis() + duration;
  }
}

void handleMotorCommand(String action, int duration, String params) {
  if (action == "ROTATE" || action == "MOVE") {
    int angle = 90; // Default center
    if (params.length() > 0) {
      angle = params.toInt();
      angle = constrain(angle, 0, 180);
    }
    servoMotor.write(angle);
    
    // Return to center after duration
    delay(duration);
    servoMotor.write(90);
  } else if (action == "SWEEP") {
    // Sweep servo back and forth
    unsigned long start_time = millis();
    while (millis() - start_time < duration) {
      for (int pos = 0; pos <= 180; pos += 5) {
        servoMotor.write(pos);
        delay(50);
        if (millis() - start_time >= duration) break;
      }
      for (int pos = 180; pos >= 0; pos -= 5) {
        servoMotor.write(pos);
        delay(50);
        if (millis() - start_time >= duration) break;
      }
    }
    servoMotor.write(90); // Return to center
  } else if (action == "CENTER") {
    servoMotor.write(90);
  }
}

void handleFanCommand(String action, int duration) {
  if (action == "ON") {
    digitalWrite(FAN_PIN, HIGH);
    fan_active = true;
    fan_stop_time = millis() + duration;
  } else if (action == "OFF") {
    digitalWrite(FAN_PIN, LOW);
    fan_active = false;
    fan_stop_time = 0;
  } else if (action == "SPEED") {
    // For PWM speed control (simplified - just turn on)
    digitalWrite(FAN_PIN, HIGH);
    fan_active = true;
    fan_stop_time = millis() + duration;
  }
}

void handleBuzzerCommand(String action, int duration, String params) {
  if (action == "BEEP") {
    int frequency = 1000; // Default frequency
    if (params.length() > 0) {
      frequency = params.toInt();
    }
    
    tone(BUZZER_PIN, frequency, duration);
  } else if (action == "PATTERN") {
    // Simple beep pattern
    for (int i = 0; i < 3; i++) {
      tone(BUZZER_PIN, 1000, 200);
      delay(300);
    }
  } else if (action == "OFF") {
    noTone(BUZZER_PIN);
  }
}

void updateDeviceTimers() {
  unsigned long current_time = millis();
  
  // Check selenoid 1 timer
  if (selenoid1_active && selenoid1_stop_time > 0 && current_time >= selenoid1_stop_time) {
    digitalWrite(SELENOID_1_PIN, LOW);
    selenoid1_active = false;
    selenoid1_stop_time = 0;
  }
  
  // Check selenoid 2 timer
  if (selenoid2_active && selenoid2_stop_time > 0 && current_time >= selenoid2_stop_time) {
    digitalWrite(SELENOID_2_PIN, LOW);
    selenoid2_active = false;
    selenoid2_stop_time = 0;
  }
  
  // Check fan timer
  if (fan_active && fan_stop_time > 0 && current_time >= fan_stop_time) {
    digitalWrite(FAN_PIN, LOW);
    fan_active = false;
    fan_stop_time = 0;
  }
  
  // Check LED timer
  if (led_stop_time > 0 && current_time >= led_stop_time) {
    digitalWrite(LED_STRIP_PIN, LOW);
    led_stop_time = 0;
  }
}

void stopAllDevices() {
  // Stop all outputs immediately
  digitalWrite(SELENOID_1_PIN, LOW);
  digitalWrite(SELENOID_2_PIN, LOW);
  digitalWrite(LED_STRIP_PIN, LOW);
  digitalWrite(FAN_PIN, LOW);
  digitalWrite(BUZZER_PIN, LOW);
  noTone(BUZZER_PIN);
  
  // Reset states
  selenoid1_active = false;
  selenoid2_active = false;
  fan_active = false;
  selenoid1_stop_time = 0;
  selenoid2_stop_time = 0;
  fan_stop_time = 0;
  led_stop_time = 0;
  
  // Return servo to center
  servoMotor.write(90);
}
