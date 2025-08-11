/*
 * TikTok Live Controller - Advanced Arduino Sketch v3.0
 * ====================================================
 * 
 * Enhanced sketch untuk handle advanced rule engine commands:
 * - SIMULTANEOUS_PINS: Activate multiple pins simultaneously
 * - SEQUENTIAL_PINS: Activate pins in sequence
 * - RANDOM_PINS: Chaotic random pin activation
 * - Standard JSON commands for backward compatibility
 * 
 * Hardware Setup:
 * - Pin 13: Connection indicator LED (built-in LED)
 * - Pins 2-12: Available trigger outputs (11 pins total)
 * - Pin 0,1: Reserved for Serial communication
 * 
 * Command Protocol v3.0:
 * 1. Legacy JSON: {"cmd":"trigger","pins":[6,7],"duration":100}
 * 2. SIMULTANEOUS: SIMULTANEOUS_PINS:6,7,8:100
 * 3. SEQUENTIAL: SEQUENTIAL_PINS:6,7,8:100:50
 * 4. RANDOM: RANDOM_PINS:6,7,8:100:3:5:2
 * 
 * Author: TikTok Live Tracker Team - Advanced Rule Engine
 * Version: 3.0
 * Date: January 2025
 */

#include <ArduinoJson.h>

// Configuration
const int CONNECTION_LED = 13;
const int BAUD_RATE = 9600;
const int MAX_PINS = 11;
const int MIN_DURATION = 10;   // Minimum 10ms for faster response
const int MAX_DURATION = 10000; // Maximum 10 seconds
const int MAX_DELAY = 2000;    // Maximum 2 seconds delay

// Global variables
bool connectionActive = false;
unsigned long lastHeartbeat = 0;
const unsigned long HEARTBEAT_TIMEOUT = 15000; // 15 seconds

// Available pins for triggering (exclude pin 0,1 for serial, 13 for LED)
const int availablePins[] = {2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12};
const int numAvailablePins = sizeof(availablePins) / sizeof(availablePins[0]);

// Execution statistics
unsigned long totalCommands = 0;
unsigned long successfulCommands = 0;
unsigned long lastCommandTime = 0;

void setup() {
  Serial.begin(BAUD_RATE);
  Serial.setTimeout(100); // Quick timeout for responsive parsing
  
  // Initialize connection LED
  pinMode(CONNECTION_LED, OUTPUT);
  digitalWrite(CONNECTION_LED, LOW);
  
  // Initialize all available pins as outputs
  for (int i = 0; i < numAvailablePins; i++) {
    pinMode(availablePins[i], OUTPUT);
    digitalWrite(availablePins[i], LOW);
  }
  
  // Random seed for chaos mode
  randomSeed(analogRead(A0));
  
  // Startup sequence
  startupLedSequence();
  
  Serial.println("ARDUINO_READY:v3.0:advanced_rule_engine");
  Serial.flush();
}

void loop() {
  // Check for commands
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    if (command.length() > 0) {
      processCommand(command);
      lastHeartbeat = millis();
      connectionActive = true;
    }
  }
  
  // Connection timeout check
  if (connectionActive && (millis() - lastHeartbeat > HEARTBEAT_TIMEOUT)) {
    connectionActive = false;
    digitalWrite(CONNECTION_LED, LOW);
    Serial.println("CONNECTION_TIMEOUT");
  }
  
  // Update connection LED
  if (connectionActive) {
    digitalWrite(CONNECTION_LED, HIGH);
  }
  
  delay(1); // Small delay for stability
}

void processCommand(String command) {
  totalCommands++;
  lastCommandTime = millis();
  
  // Advanced command protocol
  if (command.startsWith("SIMULTANEOUS_PINS:")) {
    processSimultaneousCommand(command);
  }
  else if (command.startsWith("SEQUENTIAL_PINS:")) {
    processSequentialCommand(command);
  }
  else if (command.startsWith("RANDOM_PINS:")) {
    processRandomCommand(command);
  }
  else if (command.startsWith("HEARTBEAT") || command.startsWith("PING")) {
    processPingCommand();
  }
  else if (command.startsWith("STATUS")) {
    processStatusCommand();
  }
  else if (command.startsWith("RESET")) {
    processResetCommand();
  }
  else if (command.startsWith("LED_BLINK")) {
    processLedBlinkCommand(command);
  }
  else if (command.startsWith("TEST_PIN:")) {
    processTestPinCommand(command);
  }
  else if (command.startsWith("{")) {
    // Legacy JSON command
    processJsonCommand(command);
  }
  else {
    Serial.println("ERROR:unknown_command:" + command);
  }
}

void processSimultaneousCommand(String command) {
  // Format: SIMULTANEOUS_PINS:6,7,8:100
  int firstColon = command.indexOf(':', 18);
  int secondColon = command.indexOf(':', firstColon + 1);
  
  if (firstColon == -1) {
    Serial.println("ERROR:invalid_simultaneous_format");
    return;
  }
  
  String pinsStr = command.substring(18, firstColon);
  int duration;
  
  if (secondColon == -1) {
    // Only duration at the end
    duration = command.substring(firstColon + 1).toInt();
  } else {
    duration = command.substring(firstColon + 1, secondColon).toInt();
  }
  
  // Parse pins
  int pins[MAX_PINS];
  int pinCount = parsePins(pinsStr, pins);
  
  if (pinCount == 0) {
    Serial.println("ERROR:no_valid_pins");
    return;
  }
  
  // Validate duration
  duration = constrain(duration, MIN_DURATION, MAX_DURATION);
  
  // Execute simultaneous activation
  executeSimultaneous(pins, pinCount, duration);
  
  successfulCommands++;
  Serial.println("OK:SIMULTANEOUS:" + String(pinCount) + ":" + String(duration));
}

void processSequentialCommand(String command) {
  // Format: SEQUENTIAL_PINS:6,7,8:100:50
  int firstColon = command.indexOf(':', 16);
  int secondColon = command.indexOf(':', firstColon + 1);
  int thirdColon = command.indexOf(':', secondColon + 1);
  
  if (firstColon == -1 || secondColon == -1) {
    Serial.println("ERROR:invalid_sequential_format");
    return;
  }
  
  String pinsStr = command.substring(16, firstColon);
  int duration = command.substring(firstColon + 1, secondColon).toInt();
  int stepDelay = 0;
  
  if (thirdColon != -1) {
    stepDelay = command.substring(secondColon + 1, thirdColon).toInt();
  } else {
    stepDelay = command.substring(secondColon + 1).toInt();
  }
  
  // Parse pins
  int pins[MAX_PINS];
  int pinCount = parsePins(pinsStr, pins);
  
  if (pinCount == 0) {
    Serial.println("ERROR:no_valid_pins");
    return;
  }
  
  // Validate parameters
  duration = constrain(duration, MIN_DURATION, MAX_DURATION);
  stepDelay = constrain(stepDelay, 0, MAX_DELAY);
  
  // Execute sequential activation
  executeSequential(pins, pinCount, duration, stepDelay);
  
  successfulCommands++;
  Serial.println("OK:SEQUENTIAL:" + String(pinCount) + ":" + String(duration) + ":" + String(stepDelay));
}

void processRandomCommand(String command) {
  // Format: RANDOM_PINS:6,7,8:100:3:5:2
  // Parameters: pins:duration:maxPins:repeatCount:cycleCount
  
  String parts[6];
  int partCount = splitString(command, ':', parts, 6);
  
  if (partCount < 4) {
    Serial.println("ERROR:invalid_random_format");
    return;
  }
  
  String pinsStr = parts[1];
  int duration = parts[2].toInt();
  int maxPins = parts[3].toInt();
  int repeatCount = (partCount > 4) ? parts[4].toInt() : 1;
  int cycleCount = (partCount > 5) ? parts[5].toInt() : 0;
  
  // Parse available pins
  int pins[MAX_PINS];
  int totalPins = parsePins(pinsStr, pins);
  
  if (totalPins == 0) {
    Serial.println("ERROR:no_valid_pins");
    return;
  }
  
  // Validate parameters
  duration = constrain(duration, MIN_DURATION, MAX_DURATION);
  maxPins = constrain(maxPins, 1, min(totalPins, MAX_PINS));
  repeatCount = constrain(repeatCount, 1, 10);
  cycleCount = constrain(cycleCount, 0, 5);
  
  // Execute random chaos
  executeRandom(pins, totalPins, duration, maxPins, repeatCount, cycleCount);
  
  successfulCommands++;
  Serial.println("OK:RANDOM:" + String(totalPins) + ":" + String(duration) + ":" + String(maxPins) + ":" + String(repeatCount) + ":" + String(cycleCount));
}

void processPingCommand() {
  Serial.println("PONG:v3.0:" + String(millis()));
}

void processStatusCommand() {
  float successRate = (totalCommands > 0) ? (float)successfulCommands / totalCommands * 100.0 : 100.0;
  
  Serial.println("STATUS:v3.0:" + String(totalCommands) + ":" + String(successfulCommands) + ":" + String(successRate, 1) + ":" + String(lastCommandTime));
}

void processResetCommand() {
  // Turn off all pins
  for (int i = 0; i < numAvailablePins; i++) {
    digitalWrite(availablePins[i], LOW);
  }
  
  // Reset statistics
  totalCommands = 0;
  successfulCommands = 0;
  lastCommandTime = 0;
  
  Serial.println("RESET:OK");
}

void processJsonCommand(String command) {
  // Enhanced JSON command support
  DynamicJsonDocument doc(256);
  DeserializationError error = deserializeJson(doc, command);
  
  if (error) {
    Serial.println("ERROR:json_parse:" + String(error.c_str()));
    return;
  }
  
  String cmd = doc["cmd"];
  
  if (cmd == "trigger") {
    // Legacy trigger command
    // Extract pins array
    JsonArray pinsArray = doc["pins"];
    int pins[MAX_PINS];
    int pinCount = 0;
    
    for (int pin : pinsArray) {
      if (isValidPin(pin) && pinCount < MAX_PINS) {
        pins[pinCount++] = pin;
      }
    }
    
    if (pinCount == 0) {
      Serial.println("ERROR:no_valid_json_pins");
      return;
    }
    
    int duration = doc["duration"];
    duration = constrain(duration, MIN_DURATION, MAX_DURATION);
    
    // Execute as simultaneous (legacy behavior)
    executeSimultaneous(pins, pinCount, duration);
    
    successfulCommands++;
    
    // JSON response
    DynamicJsonDocument response(256);
    response["status"] = "ok";
    response["executed"] = pinCount;
    response["duration"] = duration;
    response["time"] = millis();
    
    serializeJson(response, Serial);
    Serial.println();
  }
  else if (cmd == "test_pin") {
    // New test_pin JSON command
    int pin = doc["pin"];
    int duration = doc["duration"];
    
    // Validate pin
    if (!isValidPin(pin)) {
      DynamicJsonDocument response(256);
      response["status"] = "error";
      response["message"] = "invalid_pin";
      response["pin"] = pin;
      serializeJson(response, Serial);
      Serial.println();
      return;
    }
    
    // Validate duration
    duration = constrain(duration, MIN_DURATION, MAX_DURATION);
    
    // Test the pin
    digitalWrite(pin, HIGH);
    delay(duration);
    digitalWrite(pin, LOW);
    
    successfulCommands++;
    
    // JSON response
    DynamicJsonDocument response(256);
    response["status"] = "ok";
    response["pin"] = pin;
    response["duration"] = duration;
    response["time"] = millis();
    
    serializeJson(response, Serial);
    Serial.println();
  }
  else if (cmd == "test_led") {
    // New test_led JSON command
    int blinks = doc["blinks"];
    int interval = doc["interval"];
    
    // Validate parameters
    blinks = constrain(blinks, 1, 10);
    interval = constrain(interval, 50, 1000);
    
    // Test LED
    for (int i = 0; i < blinks; i++) {
      digitalWrite(CONNECTION_LED, HIGH);
      delay(interval);
      digitalWrite(CONNECTION_LED, LOW);
      if (i < blinks - 1) {
        delay(interval);
      }
    }
    
    successfulCommands++;
    
    // JSON response
    DynamicJsonDocument response(256);
    response["status"] = "ok";
    response["blinks"] = blinks;
    response["interval"] = interval;
    response["time"] = millis();
    
    serializeJson(response, Serial);
    Serial.println();
  }
  else if (cmd == "ping") {
    // Ping command
    DynamicJsonDocument response(256);
    response["status"] = "pong";
    response["version"] = "v3.0";
    response["time"] = millis();
    
    serializeJson(response, Serial);
    Serial.println();
  }
  else {
    DynamicJsonDocument response(256);
    response["status"] = "error";
    response["message"] = "unknown_command";
    response["command"] = cmd;
    
    serializeJson(response, Serial);
    Serial.println();
  }
}

int parsePins(String pinsStr, int pins[]) {
  int count = 0;
  int startIndex = 0;
  
  while (startIndex < pinsStr.length() && count < MAX_PINS) {
    int commaIndex = pinsStr.indexOf(',', startIndex);
    
    String pinStr;
    if (commaIndex == -1) {
      pinStr = pinsStr.substring(startIndex);
      startIndex = pinsStr.length();
    } else {
      pinStr = pinsStr.substring(startIndex, commaIndex);
      startIndex = commaIndex + 1;
    }
    
    pinStr.trim();
    int pin = pinStr.toInt();
    
    if (isValidPin(pin)) {
      pins[count++] = pin;
    }
  }
  
  return count;
}

int splitString(String str, char delimiter, String result[], int maxParts) {
  int count = 0;
  int startIndex = 0;
  
  while (startIndex < str.length() && count < maxParts) {
    int delimiterIndex = str.indexOf(delimiter, startIndex);
    
    if (delimiterIndex == -1) {
      result[count++] = str.substring(startIndex);
      break;
    } else {
      result[count++] = str.substring(startIndex, delimiterIndex);
      startIndex = delimiterIndex + 1;
    }
  }
  
  return count;
}

bool isValidPin(int pin) {
  for (int i = 0; i < numAvailablePins; i++) {
    if (availablePins[i] == pin) {
      return true;
    }
  }
  return false;
}

void executeSimultaneous(int pins[], int pinCount, int duration) {
  // Turn all pins ON simultaneously
  for (int i = 0; i < pinCount; i++) {
    digitalWrite(pins[i], HIGH);
  }
  
  // Wait for duration
  delay(duration);
  
  // Turn all pins OFF simultaneously
  for (int i = 0; i < pinCount; i++) {
    digitalWrite(pins[i], LOW);
  }
}

void executeSequential(int pins[], int pinCount, int duration, int stepDelay) {
  for (int i = 0; i < pinCount; i++) {
    // Turn pin ON
    digitalWrite(pins[i], HIGH);
    
    // Wait for duration
    delay(duration);
    
    // Turn pin OFF
    digitalWrite(pins[i], LOW);
    
    // Delay before next pin (except last)
    if (i < pinCount - 1) {
      delay(stepDelay);
    }
  }
}

void executeRandom(int pins[], int totalPins, int duration, int maxPins, int repeatCount, int cycleCount) {
  for (int cycle = 0; cycle <= cycleCount; cycle++) {
    for (int repeat = 0; repeat < repeatCount; repeat++) {
      // Random pin selection
      int selectedCount = random(1, maxPins + 1);
      int selectedPins[MAX_PINS];
      
      // Randomly select pins
      for (int i = 0; i < selectedCount; i++) {
        int randomIndex = random(totalPins);
        selectedPins[i] = pins[randomIndex];
      }
      
      // Random duration variation (±25%)
      int varyDuration = duration + random(-duration/4, duration/4 + 1);
      varyDuration = constrain(varyDuration, MIN_DURATION, MAX_DURATION);
      
      // Execute chaos pattern
      executeSimultaneous(selectedPins, selectedCount, varyDuration);
      
      // Random delay between repeats
      if (repeat < repeatCount - 1) {
        delay(random(10, 100));
      }
    }
    
    // Delay between cycles
    if (cycle < cycleCount) {
      delay(random(100, 500));
    }
  }
}

void startupLedSequence() {
  // Brief startup sequence to indicate Arduino is ready
  for (int i = 0; i < 3; i++) {
    digitalWrite(CONNECTION_LED, HIGH);
    delay(200);
    digitalWrite(CONNECTION_LED, LOW);
    delay(200);
  }
}

void processLedBlinkCommand(String command) {
  // Handle LED_BLINK commands for testing
  int blinkCount = 3; // Default
  
  if (command.indexOf("_") != -1) {
    // Extract number from command like "LED_BLINK_5"
    int underscorePos = command.lastIndexOf('_');
    if (underscorePos != -1) {
      String countStr = command.substring(underscorePos + 1);
      int count = countStr.toInt();
      if (count > 0 && count <= 10) {
        blinkCount = count;
      }
    }
  }
  
  // Perform LED blink test
  Serial.println("OK:led_blink_start:" + String(blinkCount));
  
  for (int i = 0; i < blinkCount; i++) {
    digitalWrite(CONNECTION_LED, HIGH);
    delay(300);
    digitalWrite(CONNECTION_LED, LOW);
    delay(300);
  }
  
  Serial.println("OK:led_blink_complete:" + String(blinkCount));
  successfulCommands++;
}

void processTestPinCommand(String command) {
  // Handle TEST_PIN:pin_number:duration commands
  // Format: TEST_PIN:6:500
  int firstColon = command.indexOf(':');
  int secondColon = command.indexOf(':', firstColon + 1);
  
  if (firstColon == -1) {
    Serial.println("ERROR:invalid_test_pin_format");
    return;
  }
  
  int pin = command.substring(firstColon + 1, secondColon != -1 ? secondColon : command.length()).toInt();
  int duration = 500; // Default 500ms
  
  if (secondColon != -1) {
    duration = command.substring(secondColon + 1).toInt();
  }
  
  // Validate pin
  bool validPin = false;
  for (int i = 0; i < numAvailablePins; i++) {
    if (availablePins[i] == pin) {
      validPin = true;
      break;
    }
  }
  
  if (!validPin) {
    Serial.println("ERROR:invalid_pin:" + String(pin));
    return;
  }
  
  // Validate duration
  duration = constrain(duration, MIN_DURATION, MAX_DURATION);
  
  // Test the pin
  Serial.println("OK:test_pin_start:" + String(pin) + ":" + String(duration));
  
  digitalWrite(pin, HIGH);
  delay(duration);
  digitalWrite(pin, LOW);
  
  Serial.println("OK:test_pin_complete:" + String(pin));
  successfulCommands++;
}
