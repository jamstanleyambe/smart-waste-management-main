/*
 * ESP32 Smart Waste Management Sensor
 * 
 * Updated version with correct IP configuration
 * Compatible with Django REST API
 * 
 * Features:
 * - WiFi connectivity
 * - Ultrasonic sensor for fill level detection
 * - Real-time data transmission to Django server
 * - Battery monitoring
 * - Signal strength reporting
 * - Error handling and retry logic
 * 
 * Hardware: ESP32 + HC-SR04 Ultrasonic Sensor
 * 
 * Author: Smart Waste Management System
 * Version: 2.0 (Updated IP Configuration)
 * Date: 2025
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Wire.h>

// WiFi Configuration
const char* ssid = "YOUR_WIFI_SSID";           // ← Change to your WiFi name
const char* password = "YOUR_WIFI_PASSWORD";   // ← Change to your WiFi password

// Server Configuration - UPDATED IP ADDRESS
const char* server_url = "http://172.20.10.6:8000";  // ← Updated with your current IP
const char* sensor_endpoint = "/api/sensor-data/";

// Hardware Pins
const int TRIG_PIN = 5;    // Ultrasonic sensor trigger pin
const int ECHO_PIN = 18;   // Ultrasonic sensor echo pin
const int LED_PIN = 2;     // Built-in LED for status
const int BATTERY_PIN = A0; // Battery voltage reading pin

// Sensor Configuration
const int MAX_DISTANCE = 200;  // Maximum distance in cm (empty bin)
const int MIN_DISTANCE = 5;    // Minimum distance in cm (full bin)
const int SENSOR_HEIGHT = 30;  // Height of sensor from bin bottom in cm

// Timing Configuration
const unsigned long SEND_INTERVAL = 30000;  // Send data every 30 seconds
const unsigned long RETRY_DELAY = 5000;     // Retry delay on failure
const int MAX_RETRIES = 3;                  // Maximum retry attempts

// Global Variables
unsigned long lastSendTime = 0;
int retryCount = 0;
String sensorId = "ESP32_SENSOR_001";  // ← Change this for each sensor
String binId = "BIN001";               // ← Change this for each bin

// Bin Location (Update for each sensor)
float binLatitude = 4.0725;   // ← Update with actual bin coordinates
float binLongitude = 9.7634;  // ← Update with actual bin coordinates

void setup() {
  Serial.begin(115200);
  Serial.println("🚀 ESP32 Smart Waste Sensor Starting...");
  
  // Initialize hardware
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(LED_PIN, OUTPUT);
  
  // Initialize WiFi
  connectToWiFi();
  
  // Blink LED to indicate startup
  blinkLED(3, 200);
  
  Serial.println("✅ Setup completed successfully!");
}

void loop() {
  // Check WiFi connection
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("❌ WiFi disconnected, reconnecting...");
    connectToWiFi();
    return;
  }
  
  // Send sensor data at intervals
  if (millis() - lastSendTime >= SEND_INTERVAL) {
    sendSensorData();
    lastSendTime = millis();
  }
  
  // Small delay to prevent overwhelming the system
  delay(1000);
}

void connectToWiFi() {
  Serial.print("📡 Connecting to WiFi: ");
  Serial.println(ssid);
  
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println();
    Serial.println("✅ WiFi connected successfully!");
    Serial.print("📡 IP Address: ");
    Serial.println(WiFi.localIP());
    Serial.print("📡 Signal Strength: ");
    Serial.print(WiFi.RSSI());
    Serial.println(" dBm");
  } else {
    Serial.println();
    Serial.println("❌ WiFi connection failed!");
    blinkLED(5, 100); // Rapid blinking for error
  }
}

float readFillLevel() {
  // Send ultrasonic pulse
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  
  // Read echo
  long duration = pulseIn(ECHO_PIN, HIGH);
  
  // Calculate distance
  float distance = duration * 0.034 / 2; // Speed of sound = 340 m/s
  
  // Convert distance to fill level percentage
  float fillLevel = 0;
  if (distance >= MAX_DISTANCE) {
    fillLevel = 0; // Empty bin
  } else if (distance <= MIN_DISTANCE) {
    fillLevel = 100; // Full bin
  } else {
    // Linear interpolation between empty and full
    fillLevel = ((MAX_DISTANCE - distance) / (MAX_DISTANCE - MIN_DISTANCE)) * 100;
  }
  
  // Ensure fill level is within bounds
  fillLevel = constrain(fillLevel, 0, 100);
  
  Serial.print("📏 Distance: ");
  Serial.print(distance);
  Serial.print(" cm, Fill Level: ");
  Serial.print(fillLevel);
  Serial.println("%");
  
  return fillLevel;
}

float readBatteryLevel() {
  // Read battery voltage (assuming voltage divider)
  int rawValue = analogRead(BATTERY_PIN);
  float voltage = (rawValue / 4095.0) * 3.3 * 2; // Assuming 2:1 voltage divider
  
  // Convert to percentage (assuming 3.7V = 100%, 3.0V = 0%)
  float batteryPercent = ((voltage - 3.0) / (3.7 - 3.0)) * 100;
  batteryPercent = constrain(batteryPercent, 0, 100);
  
  Serial.print("🔋 Battery: ");
  Serial.print(voltage);
  Serial.print("V (");
  Serial.print(batteryPercent);
  Serial.println("%)");
  
  return batteryPercent;
}

void sendSensorData() {
  Serial.println("📤 Sending sensor data...");
  
  // Read sensor values
  float fillLevel = readFillLevel();
  float batteryLevel = readBatteryLevel();
  int signalStrength = WiFi.RSSI();
  
  // Create JSON payload
  DynamicJsonDocument doc(1024);
  doc["sensor_id"] = sensorId;
  doc["bin_id"] = binId;
  doc["fill_level"] = fillLevel;
  doc["latitude"] = binLatitude;
  doc["longitude"] = binLongitude;
  doc["organic_percentage"] = random(30, 60);  // Simulated waste composition
  doc["plastic_percentage"] = random(20, 40);
  doc["metal_percentage"] = random(10, 30);
  doc["sensor_status"] = "ONLINE";
  doc["battery_level"] = batteryLevel;
  doc["signal_strength"] = signalStrength;
  doc["temperature"] = random(20, 35);  // Simulated temperature
  doc["humidity"] = random(40, 80);     // Simulated humidity
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  Serial.println("📊 Data to send:");
  Serial.println(jsonString);
  
  // Send HTTP POST request
  HTTPClient http;
  String url = String(server_url) + String(sensor_endpoint);
  
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  
  int httpResponseCode = http.POST(jsonString);
  
  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.print("✅ HTTP Response Code: ");
    Serial.println(httpResponseCode);
    Serial.print("📥 Response: ");
    Serial.println(response);
    
    // Success - reset retry count and blink LED
    retryCount = 0;
    blinkLED(1, 500);
    
  } else {
    Serial.print("❌ HTTP Error: ");
    Serial.println(httpResponseCode);
    Serial.print("❌ Error: ");
    Serial.println(http.errorToString(httpResponseCode));
    
    // Increment retry count
    retryCount++;
    
    if (retryCount >= MAX_RETRIES) {
      Serial.println("❌ Max retries reached, waiting before next attempt...");
      retryCount = 0;
      delay(RETRY_DELAY * 2); // Longer delay after max retries
    } else {
      delay(RETRY_DELAY);
    }
    
    // Blink LED for error
    blinkLED(2, 200);
  }
  
  http.end();
}

void blinkLED(int times, int delayMs) {
  for (int i = 0; i < times; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(delayMs);
    digitalWrite(LED_PIN, LOW);
    delay(delayMs);
  }
}

// Function to update sensor configuration (call from setup if needed)
void updateSensorConfig(String newSensorId, String newBinId, float newLat, float newLon) {
  sensorId = newSensorId;
  binId = newBinId;
  binLatitude = newLat;
  binLongitude = newLon;
  
  Serial.println("🔧 Sensor configuration updated:");
  Serial.print("   Sensor ID: ");
  Serial.println(sensorId);
  Serial.print("   Bin ID: ");
  Serial.println(binId);
  Serial.print("   Location: ");
  Serial.print(binLatitude);
  Serial.print(", ");
  Serial.println(binLongitude);
}
