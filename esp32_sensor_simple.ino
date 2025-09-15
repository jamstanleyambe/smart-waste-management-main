/*
 * ESP32 Smart Waste Sensor - Simple Version
 * 
 * Easy to configure and deploy
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
String sensorId = "ESP32_SENSOR_001";         // Unique sensor ID
String binId = "BIN001";                      // Bin ID this sensor monitors
float binLatitude = 4.0725;                   // Bin latitude
float binLongitude = 9.7634;                  // Bin longitude
// ===============================================

// Hardware pins
const int TRIG_PIN = 5;
const int ECHO_PIN = 18;
const int LED_PIN = 2;

// Timing
const unsigned long SEND_INTERVAL = 30000; // Send every 30 seconds

unsigned long lastSendTime = 0;

void setup() {
  Serial.begin(115200);
  Serial.println("🚀 ESP32 Smart Waste Sensor Starting...");
  
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(LED_PIN, OUTPUT);
  
  connectToWiFi();
  blinkLED(3, 200);
  Serial.println("✅ Setup completed!");
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    connectToWiFi();
    return;
  }
  
  if (millis() - lastSendTime >= SEND_INTERVAL) {
    sendSensorData();
    lastSendTime = millis();
  }
  
  delay(1000);
}

void connectToWiFi() {
  Serial.print("📡 Connecting to WiFi...");
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println();
  Serial.println("✅ WiFi connected!");
  Serial.print("📡 IP: ");
  Serial.println(WiFi.localIP());
}

float readFillLevel() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  
  long duration = pulseIn(ECHO_PIN, HIGH);
  float distance = duration * 0.034 / 2;
  
  // Convert distance to fill level (0-100%)
  float fillLevel = 0;
  if (distance >= 200) fillLevel = 0;      // Empty
  else if (distance <= 5) fillLevel = 100;  // Full
  else fillLevel = ((200 - distance) / 195.0) * 100;
  
  fillLevel = constrain(fillLevel, 0, 100);
  
  Serial.print("📏 Fill Level: ");
  Serial.print(fillLevel);
  Serial.println("%");
  
  return fillLevel;
}

void sendSensorData() {
  Serial.println("📤 Sending sensor data...");
  
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
  
  // Send HTTP POST
  HTTPClient http;
  String url = String(server_url) + "/api/sensor-data/";
  
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  
  int httpResponseCode = http.POST(jsonString);
  
  if (httpResponseCode > 0) {
    Serial.print("✅ Success! Response: ");
    Serial.println(httpResponseCode);
    blinkLED(1, 500);
  } else {
    Serial.print("❌ Error: ");
    Serial.println(httpResponseCode);
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
