#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// WiFi Configuration
const char* ssid = "SM";
const char* password = "SM-12345";

// API Configuration - UPDATED IP ADDRESS
const char* apiUrl = "http://192.168.43.159:8000/api/sensor-data/";
const char* binId = "BIN001";

// Pin Configuration
const int TRIG_PIN = 2;
const int ECHO_PIN = 4;
const int LED_PIN = 5;

// Bin Parameters
const float BIN_HEIGHT = 120.0;
const float SENSOR_OFFSET = 10.0;
const float MAX_FILL_LEVEL = 100.0;

// Timing
const unsigned long SEND_INTERVAL = 5000; // 5 seconds for debugging
unsigned long lastSendTime = 0;

// Data Variables
float currentFillPercentage = 0;
float latitude = 4.0511;
float longitude = 9.7679;

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("\n=== ESP32 DEBUG TEST STARTING ===");
  Serial.println("📋 Configuration:");
  Serial.print("   Server: ");
  Serial.println(apiUrl);
  Serial.print("   Bin ID: ");
  Serial.println(binId);
  Serial.print("   WiFi: ");
  Serial.println(ssid);
  
  // Initialize pins
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(LED_PIN, OUTPUT);
  
  digitalWrite(TRIG_PIN, LOW);
  digitalWrite(LED_PIN, LOW);
  
  Serial.println("✓ Pins initialized");
  
  // Connect WiFi
  connectWiFi();
  
  Serial.println("✓ Setup complete - System ready!");
  Serial.println("🔍 DEBUG MODE: Send data every 5 seconds");
  Serial.println("📱 Move sensor up/down to see changes");
  Serial.println("📊 Watch Serial Monitor for readings");
  Serial.println();
}

void loop() {
  unsigned long currentTime = millis();
  
  if (currentTime - lastSendTime >= SEND_INTERVAL) {
    currentFillPercentage = readSensor();
    sendData();
    lastSendTime = currentTime;
  }
  
  // Status LED heartbeat
  static unsigned long lastBlink = 0;
  if (currentTime - lastBlink >= 1000) {
    digitalWrite(LED_PIN, !digitalRead(LED_PIN));
    lastBlink = currentTime;
  }
  
  delay(100);
}

void connectWiFi() {
  Serial.print("🔗 Connecting to WiFi: ");
  Serial.println(ssid);
  
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(1000);
    Serial.print(".");
    attempts++;
    digitalWrite(LED_PIN, !digitalRead(LED_PIN));
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println();
    Serial.println("✅ WiFi connected successfully!");
    Serial.print("  📍 IP Address: ");
    Serial.println(WiFi.localIP());
    Serial.print("  📶 Signal Strength: ");
    Serial.print(WiFi.RSSI());
    Serial.println(" dBm");
    
    // Success blink
    for (int i = 0; i < 3; i++) {
      digitalWrite(LED_PIN, HIGH);
      delay(200);
      digitalWrite(LED_PIN, LOW);
      delay(200);
    }
  } else {
    Serial.println();
    Serial.println("❌ WiFi connection failed!");
    Serial.println("🔧 Check WiFi credentials and signal strength");
  }
}

float readSensor() {
  Serial.println("┌────────── SENSOR READING ─────────┐");
  
  // Clear trigger
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(5);
  
  // Send trigger pulse
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  
  // Read echo
  unsigned long duration = pulseIn(ECHO_PIN, HIGH, 30000);
  
  if (duration == 0) {
    Serial.println("│ Sensor Status:     ❌ TIMEOUT      │");
    Serial.println("│ Distance:          NO READING     │");
    Serial.println("│ Fill Level:        0.0%           │");
    Serial.println("└────────────────────────────────────┘");
    return 0;
  }
  
  // Calculate distance
  float distance = (duration * 0.034) / 2.0;
  
  // Validate distance
  if (distance < 2.0 || distance > 400.0) {
    Serial.println("│ Sensor Status:     ❌ INVALID      │");
    Serial.printf("│ Distance:          %.1f cm        │\n", distance);
    Serial.println("│ Fill Level:        0.0%           │");
    Serial.println("└────────────────────────────────────┘");
    return 0;
  }
  
  // Calculate fill level
  float fillLevel = BIN_HEIGHT - SENSOR_OFFSET - distance;
  if (fillLevel < 0) fillLevel = 0;
  if (fillLevel > MAX_FILL_LEVEL) fillLevel = MAX_FILL_LEVEL;
  
  // Convert to percentage
  float percentage = (fillLevel / MAX_FILL_LEVEL) * 100;
  if (percentage < 0) percentage = 0;
  if (percentage > 100) percentage = 100;
  
  Serial.println("│ Sensor Status:     ✅ ACTIVE       │");
  Serial.printf("│ Distance:          %.1f cm        │\n", distance);
  Serial.printf("│ Fill Level:        %.1f%%          │\n", percentage);
  Serial.println("└────────────────────────────────────┘");
  
  return percentage;
}

void sendData() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("⚠️ WiFi disconnected, reconnecting...");
    connectWiFi();
    return;
  }
  
  HTTPClient http;
  
  if (!http.begin(apiUrl)) {
    Serial.println("❌ HTTP client failed to start");
    return;
  }
  
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(10000); // 10 second timeout
  
  // Create JSON payload
  StaticJsonDocument<200> doc;
  doc["sensor_id"] = "ESP32_001";
  doc["bin_id"] = binId;
  doc["fill_level"] = currentFillPercentage;
  doc["latitude"] = latitude;
  doc["longitude"] = longitude;
  doc["organic_percentage"] = 40.0;
  doc["plastic_percentage"] = 35.0;
  doc["metal_percentage"] = 25.0;
  doc["sensor_status"] = "ONLINE";
  doc["battery_level"] = 95.0;
  doc["signal_strength"] = WiFi.RSSI();
  doc["temperature"] = 25.0;
  doc["humidity"] = 60.0;
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  Serial.print("📡 Sending data: ");
  Serial.println(jsonString);
  
  // Send POST request
  int httpCode = http.POST(jsonString);
  
  if (httpCode > 0) {
    String response = http.getString();
    Serial.printf("📨 Server response: %d ", httpCode);
    
    if (httpCode == 201) {
      Serial.println("- ✅ SUCCESS!");
      
      // Success blink
      for (int i = 0; i < 2; i++) {
        digitalWrite(LED_PIN, HIGH);
        delay(100);
        digitalWrite(LED_PIN, LOW);
        delay(100);
      }
    } else {
      Serial.printf("- ❌ Error: %s\n", response.c_str());
    }
  } else {
    Serial.printf("❌ Connection failed: %s\n", http.errorToString(httpCode).c_str());
  }
  
  http.end();
  Serial.println(); // Add spacing between transmissions
}
