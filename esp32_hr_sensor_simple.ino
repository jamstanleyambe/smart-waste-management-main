/*
 * ESP32 HR (Ultrasonic) Sensor - Simple Version
 * 
 * Easy to configure and deploy
 * Perfect for quick setup and testing
 * 
 * Hardware: ESP32 + HC-SR04 Ultrasonic Sensor
 * 
 * Configuration Steps:
 * 1. Update WiFi credentials
 * 2. Update sensor ID and bin ID
 * 3. Update bin coordinates
 * 4. Upload to ESP32
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// ===== CONFIGURATION - UPDATE THESE VALUES =====
const char* ssid = "YOUR_WIFI_SSID";           // Your WiFi name
const char* password = "YOUR_WIFI_PASSWORD";   // Your WiFi password
const char* server_url = "http://172.20.10.6:8000";  // Your Django server IP
String sensorId = "ESP32_HR_SENSOR_001";     // Unique sensor ID
String binId = "BIN001";                      // Bin ID this sensor monitors
float binLatitude = 4.0725;                   // Bin latitude
float binLongitude = 9.7634;                  // Bin longitude
// ===============================================

// Hardware pins
const int TRIG_PIN = 5;    // Ultrasonic sensor trigger pin
const int ECHO_PIN = 18;   // Ultrasonic sensor echo pin
const int LED_PIN = 2;     // Status LED pin

// Timing
const unsigned long SEND_INTERVAL = 30000; // Send every 30 seconds

// Global variables
unsigned long lastSendTime = 0;

void setup() {
  Serial.begin(115200);
  Serial.println("🚀 ESP32 HR Sensor Starting...");
  Serial.println("📋 Configuration:");
  Serial.print("   Sensor ID: ");
  Serial.println(sensorId);
  Serial.print("   Bin ID: ");
  Serial.println(binId);
  Serial.print("   Server: ");
  Serial.println(server_url);
  
  // Initialize hardware
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(LED_PIN, OUTPUT);
  
  // Initialize ultrasonic sensor
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  
  // Connect to WiFi
  connectToWiFi();
  
  // Blink LED to indicate startup
  blinkLED(3, 200);
  
  Serial.println("✅ Setup completed!");
  Serial.println("🔄 Starting main loop...");
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
  Serial.println("📏 Reading fill level...");
  
  // Send ultrasonic pulse
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  
  // Read echo
  long duration = pulseIn(ECHO_PIN, HIGH, 30000); // 30ms timeout
  
  if (duration == 0) {
    Serial.println("⚠️ No echo received, using default value");
    return 50.0; // Default fill level
  }
  
  // Calculate distance
  float distance = duration * 0.034 / 2; // Speed of sound = 340 m/s
  
  // Convert distance to fill level percentage
  float fillLevel = 0;
  if (distance >= 200) {
    fillLevel = 0;      // Empty bin
  } else if (distance <= 5) {
    fillLevel = 100;    // Full bin
  } else {
    // Linear interpolation between empty and full
    fillLevel = ((200 - distance) / 195.0) * 100;
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

void sendSensorData() {
  Serial.println("📤 Sending sensor data...");
  
  // Read sensor values
  float fillLevel = readFillLevel();
  int signalStrength = WiFi.RSSI();
  
  // Create JSON payload
  DynamicJsonDocument doc(512);
  doc["sensor_id"] = sensorId;
  doc["bin_id"] = binId;
  doc["fill_level"] = fillLevel;
  doc["latitude"] = binLatitude;
  doc["longitude"] = binLongitude;
  doc["organic_percentage"] = random(30, 60);
  doc["plastic_percentage"] = random(20, 40);
  doc["metal_percentage"] = random(10, 30);
  doc["sensor_status"] = "ONLINE";
  doc["battery_level"] = random(80, 100);
  doc["signal_strength"] = signalStrength;
  doc["temperature"] = random(20, 35);
  doc["humidity"] = random(40, 80);
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  Serial.println("📊 Data to send:");
  Serial.println(jsonString);
  
  // Send HTTP POST
  HTTPClient http;
  String url = String(server_url) + "/api/sensor-data/";
  
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(10000); // 10 second timeout
  
  Serial.print("🌐 Sending to: ");
  Serial.println(url);
  
  int httpResponseCode = http.POST(jsonString);
  
  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.print("✅ Success! Response Code: ");
    Serial.println(httpResponseCode);
    Serial.print("📥 Response: ");
    Serial.println(response);
    blinkLED(1, 500);
  } else {
    Serial.print("❌ Error: ");
    Serial.println(httpResponseCode);
    Serial.print("❌ Error Details: ");
    Serial.println(http.errorToString(httpResponseCode));
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

// Test function - call from setup() to test sensor without sending data
void testSensor() {
  Serial.println("🧪 Testing sensor...");
  
  float fillLevel = readFillLevel();
  int signalStrength = WiFi.RSSI();
  
  Serial.println("📊 Test Results:");
  Serial.print("   Fill Level: ");
  Serial.print(fillLevel);
  Serial.println("%");
  Serial.print("   Signal Strength: ");
  Serial.print(signalStrength);
  Serial.println(" dBm");
  Serial.print("   WiFi Status: ");
  Serial.println(WiFi.status() == WL_CONNECTED ? "Connected" : "Disconnected");
}
