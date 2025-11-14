#include <WiFi.h>
#include <HTTPClient.h>

// WiFi Configuration
const char* ssid = "SM";
const char* password = "SM-12345";

// Test URLs - try different approaches
const char* testUrls[] = {
  "http://192.168.43.159:8000/api/sensor-data/",  // Your Django server
  "http://192.168.43.159:8000/",                  // Django root
  "http://192.168.1.1",                          // Common router IP
  "http://8.8.8.8"                               // Google DNS
};

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("\n=== ESP32 NETWORK DEBUG TEST ===");
  Serial.println("🔍 Testing network connectivity...");
  
  // Connect WiFi
  connectWiFi();
  
  // Test each URL
  for (int i = 0; i < 4; i++) {
    testConnection(testUrls[i]);
    delay(2000);
  }
  
  Serial.println("\n✅ Network test complete!");
}

void loop() {
  // Just blink LED to show it's running
  static unsigned long lastBlink = 0;
  if (millis() - lastBlink >= 1000) {
    digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));
    lastBlink = millis();
  }
}

void connectWiFi() {
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);
  
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(1000);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println();
    Serial.println("✅ WiFi connected successfully!");
    Serial.print("  ESP32 IP Address: ");
    Serial.println(WiFi.localIP());
    Serial.print("  Gateway IP: ");
    Serial.println(WiFi.gatewayIP());
    Serial.print("  Subnet Mask: ");
    Serial.println(WiFi.subnetMask());
    Serial.print("  Signal Strength: ");
    Serial.print(WiFi.RSSI());
    Serial.println(" dBm");
  } else {
    Serial.println();
    Serial.println("❌ WiFi connection failed!");
  }
}

void testConnection(const char* url) {
  Serial.print("\n🌐 Testing: ");
  Serial.println(url);
  
  HTTPClient http;
  
  if (!http.begin(url)) {
    Serial.println("❌ HTTP client failed to start");
    return;
  }
  
  http.setTimeout(5000); // 5 second timeout
  
  int httpCode = http.GET();
  
  if (httpCode > 0) {
    Serial.printf("✅ SUCCESS! HTTP Code: %d\n", httpCode);
    String response = http.getString();
    Serial.print("Response: ");
    Serial.println(response.substring(0, 100)); // First 100 chars
  } else {
    Serial.printf("❌ FAILED! Error: %s\n", http.errorToString(httpCode).c_str());
  }
  
  http.end();
}
