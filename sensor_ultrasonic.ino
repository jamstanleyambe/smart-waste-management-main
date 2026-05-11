/*
 * =====================================================================
 * SMART WASTE MANAGEMENT SYSTEM
 * Sensor: HC-SR04 Ultrasonic + Active Buzzer
 * Board:  ESP32 Dev Module
 *
 * WHAT THIS DOES:
 *   Every 30 seconds:
 *   1. Reads the distance inside the bin using the HC-SR04 ultrasonic sensor
 *   2. Converts that distance into a fill level percentage (0% - 100%)
 *   3. Sends the fill level to the Django backend via WiFi (HTTP POST)
 *   4. The backend AUTOMATICALLY updates the Bin record in the database
 *   5. If fill level is >= 85%, the buzzer beeps to alert people nearby
 *
 * WHAT THE BACKEND RECEIVES (POST /api/sensor-data/):
 *   {
 *     "sensor_id":          "SENSOR_ULTRA_001",
 *     "bin_id":             "BIN001",
 *     "fill_level":         72.5,
 *     "latitude":           4.0725,
 *     "longitude":          9.7634,
 *     "organic_percentage": 40.0,
 *     "plastic_percentage": 35.0,
 *     "metal_percentage":   25.0,
 *     "sensor_status":      "ONLINE",
 *     "battery_level":      100.0,
 *     "signal_strength":    -67
 *   }
 *
 * WIRING:
 *   HC-SR04 TRIG  → ESP32 GPIO 5
 *   HC-SR04 ECHO  → ESP32 GPIO 18
 *   HC-SR04 VCC   → ESP32 5V (or 3.3V)
 *   HC-SR04 GND   → ESP32 GND
 *
 *   Active Buzzer + → ESP32 GPIO 2
 *   Active Buzzer - → ESP32 GND
 *
 * REQUIRED LIBRARY (install via Arduino IDE Library Manager):
 *   - ArduinoJson by Benoit Blanchon (version 6.x)
 *
 * BOARD SETTINGS IN ARDUINO IDE:
 *   Tools → Board    → ESP32 Arduino → ESP32 Dev Module
 *   Tools → Port     → your COM/USB port
 *   Tools → Baud Rate → 115200
 * =====================================================================
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <ESPmDNS.h>

// =====================================================================
// SECTION 1: WIFI + SERVER SETTINGS (same as your working ESP32-CAM)
// =====================================================================
const char* WIFI_SSID     = "Orange-6B05";
const char* WIFI_PASSWORD = "GbYMLNLq7h4";
// Mac's permanent Bonjour hostname — works on ANY WiFi network, never changes
const char* MAC_HOSTNAME  = "Jams-MacBook-Pro.local";
const char* API_ENDPOINT  = "/api/sensor-data/";
String SERVER_URL = "";  // Resolved from hostname at runtime

// =====================================================================
// SECTION 2: BIN IDENTITY
// Change SENSOR_ID and BIN_ID for each physical bin unit you install.
// BIN_ID must match an existing bin_id in your database.
// =====================================================================
const char* SENSOR_ID = "SENSOR_ULTRA_001";
const char* BIN_ID    = "BIN001";

// =====================================================================
// SECTION 3: BIN LOCATION (GPS coordinates of this bin)
// =====================================================================
const float BIN_LATITUDE  = 4.0725;
const float BIN_LONGITUDE = 9.7634;

// =====================================================================
// SECTION 4: BIN PHYSICAL MEASUREMENT
//
// HOW TO MEASURE:
//   - Place sensor at the TOP of the bin, facing DOWN.
//   - BIN_DEPTH_CM = distance from sensor face to the BOTTOM of the bin
//     when the bin is completely empty. Measure this with a ruler.
//   - BIN_MIN_CM   = distance when the bin is considered 100% full
//     (typically 3-5 cm, when waste reaches near the sensor).
//
// EXAMPLE: A bin that is 100cm (1 meter) deep:
//   BIN_DEPTH_CM = 100  (empty = 100cm to bottom)
//   BIN_MIN_CM   = 5    (full  = 5cm gap remaining)
// =====================================================================
const float BIN_DEPTH_CM = 100.0;  // 1 meter bin — distance when EMPTY (0% full)
const float BIN_MIN_CM   = 5.0;    // Distance when FULL (100% full)

// =====================================================================
// SECTION 5: WASTE COMPOSITION
// These are fixed percentages for this bin type.
// They MUST add up to exactly 100.0
// =====================================================================
const float ORGANIC_PCT = 40.0;
const float PLASTIC_PCT = 35.0;
const float METAL_PCT   = 25.0;   // 40 + 35 + 25 = 100 ✓

// =====================================================================
// SECTION 6: ALERT SETTINGS
// =====================================================================
const float WARN_THRESHOLD = 65.0;          // Triple-beep warning: 65% - 85%
const float CRIT_THRESHOLD = 85.0;          // Continuous beep critical: > 85%
const unsigned long SEND_INTERVAL   = 500;  // POST to server every 0.5 seconds
const unsigned long SENSOR_INTERVAL = 60;   // HC-SR04 minimum cycle time (ms)

// =====================================================================
// PIN DEFINITIONS
// =====================================================================
#define TRIG_PIN  5    // HC-SR04 Trigger
#define ECHO_PIN  18   // HC-SR04 Echo
#define BUZZ_PIN  2    // Active Buzzer

// =====================================================================
// GLOBAL VARIABLES — do not change
// =====================================================================
unsigned long lastSendTime  = 0;
unsigned long lastReadTime  = 0;   // Tracks last HC-SR04 trigger time
float         lastFillLevel = 0.0;  // Cached fill level updated every loop

// =====================================================================
// SETUP — runs once when ESP32 powers on
// =====================================================================
void setup() {
  Serial.begin(115200);
  delay(1000);

  // Configure pins
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(BUZZ_PIN, OUTPUT);
  digitalWrite(TRIG_PIN, LOW);
  digitalWrite(BUZZ_PIN, LOW);

  Serial.println("====================================");
  Serial.println("  Smart Waste — Ultrasonic Sensor  ");
  Serial.println("====================================");
  Serial.print("Sensor ID : "); Serial.println(SENSOR_ID);
  Serial.print("Bin ID    : "); Serial.println(BIN_ID);
  Serial.print("Server    : "); Serial.println(SERVER_URL);

  // Connect to WiFi
  connectWiFi();

  // Send the first reading immediately on boot
  lastFillLevel = distanceToFillLevel(readDistanceCm());
  sendSensorData(lastFillLevel);
  lastSendTime = millis();
}

// =====================================================================
// MAIN LOOP — repeats forever
// =====================================================================
void loop() {
  // 1. Read sensor every SENSOR_INTERVAL ms (HC-SR04 needs >= 60ms between reads)
  if (millis() - lastReadTime >= SENSOR_INTERVAL) {
    float distance = readDistanceCm();
    lastFillLevel  = distanceToFillLevel(distance);
    buzzerAlert(lastFillLevel);   // ← always up-to-date, never blocked by HTTP
    lastReadTime = millis();
  }

  // 2. If WiFi dropped, reconnect (non-blocking check)
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[WiFi] Lost connection — reconnecting...");
    connectWiFi();
  }

  // 3. POST to server only every SEND_INTERVAL ms
  if (millis() - lastSendTime >= SEND_INTERVAL) {
    sendSensorData(lastFillLevel);  // reuse already-computed fill level
    lastSendTime = millis();
  }
  // No delay() — loop is driven purely by millis() timers
}

// =====================================================================
// FUNCTION: Connect to WiFi
// =====================================================================
void connectWiFi() {
  Serial.print("[WiFi] Connecting to ");
  Serial.print(WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 40) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("[WiFi] Connected!");
    Serial.print("[WiFi] IP Address: "); Serial.println(WiFi.localIP());
    Serial.print("[WiFi] Signal: "); Serial.print(WiFi.RSSI()); Serial.println(" dBm");

    // Resolve Mac's hostname to IP using mDNS (works on any network)
    Serial.print("[mDNS] Resolving "); Serial.print(MAC_HOSTNAME); Serial.println("...");
    IPAddress serverIP;
    int resolved = WiFi.hostByName(MAC_HOSTNAME, serverIP);
    if (resolved == 1) {
      SERVER_URL = "http://" + serverIP.toString() + ":8000";
      Serial.print("[mDNS] Resolved to: "); Serial.println(SERVER_URL);
    } else {
      // Fallback: use last known IP
      SERVER_URL = "http://192.168.1.128:8000";
      Serial.println("[mDNS] Could not resolve hostname — using fallback IP.");
    }
  } else {
    Serial.println("[WiFi] FAILED to connect. Will retry next loop.");
  }
}

// =====================================================================
// FUNCTION: Read distance in cm from HC-SR04
// =====================================================================
float readDistanceCm() {
  // Send a 10-microsecond trigger pulse
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  // Measure how long the echo takes to come back
  // Timeout = 30,000 microseconds (~510cm max — plenty for any bin)
  long duration = pulseIn(ECHO_PIN, HIGH, 30000);

  if (duration == 0) {
    Serial.println("[Sensor] No echo received — sensor not connected or blocked!");
    return -1;  // -1 means error
  }

  // Speed of sound = 0.034 cm per microsecond, divide by 2 (there and back)
  float distanceCm = duration * 0.034 / 2.0;

  Serial.print("[Sensor] Raw distance: ");
  Serial.print(distanceCm, 1);
  Serial.println(" cm");

  return distanceCm;
}

// =====================================================================
// FUNCTION: Convert distance to fill level percentage
// =====================================================================
float distanceToFillLevel(float distanceCm) {
  if (distanceCm < 0) {
    return 50.0;  // Sensor error — return 50% as safe default
  }

  float fillLevel;

  if (distanceCm <= BIN_MIN_CM) {
    fillLevel = 100.0;  // Bin is full
  } else if (distanceCm >= BIN_DEPTH_CM) {
    fillLevel = 0.0;    // Bin is empty
  } else {
    // Linear mapping: as distance decreases, fill level increases
    fillLevel = ((BIN_DEPTH_CM - distanceCm) / (BIN_DEPTH_CM - BIN_MIN_CM)) * 100.0;
  }

  // Make sure result stays within 0-100 bounds
  fillLevel = constrain(fillLevel, 0.0, 100.0);

  Serial.print("[Sensor] Fill level: ");
  Serial.print(fillLevel, 1);
  Serial.println("%");

  return fillLevel;
}

// =====================================================================
// FUNCTION: Buzzer alert
//   65% - 85%  → Triple beep NON-STOP (repeats every loop call)
//   > 85%      → Continuous non-stop solid beep
//   < 65%      → Silent
// =====================================================================
void buzzerAlert(float fillLevel) {
  if (fillLevel >= CRIT_THRESHOLD) {
    // CRITICAL (>= 85%): solid continuous non-stop buzzer
    Serial.println("[BUZZ] CRITICAL: Bin >= 85% full — continuous alarm!");
    digitalWrite(BUZZ_PIN, HIGH);

  } else if (fillLevel >= WARN_THRESHOLD) {
    // WARNING (65%-85%): beep-beep-beep → pause → repeat | Total cycle = 800ms
    Serial.println("[BUZZ] WARNING: Bin 65-85% full — triple beep!");
    // Beep 1 (100ms ON + 50ms OFF)
    digitalWrite(BUZZ_PIN, HIGH); delay(100); digitalWrite(BUZZ_PIN, LOW); delay(50);
    // Beep 2 (100ms ON + 50ms OFF)
    digitalWrite(BUZZ_PIN, HIGH); delay(100); digitalWrite(BUZZ_PIN, LOW); delay(50);
    // Beep 3 (100ms ON)
    digitalWrite(BUZZ_PIN, HIGH); delay(100); digitalWrite(BUZZ_PIN, LOW);
    // 400ms silence → total = 300+100+400 = 800ms
    delay(400);

  } else {
    // Below 65%: silent
    digitalWrite(BUZZ_PIN, LOW);
  }
}

// =====================================================================
// FUNCTION: POST cached fill level to Django server
// Sensor reading and buzzer are handled separately in loop()
// =====================================================================
void sendSensorData(float fillLevel) {
  int signal = WiFi.RSSI();

  // Build JSON payload — exact fields the API requires
  DynamicJsonDocument doc(512);
  doc["sensor_id"]          = SENSOR_ID;
  doc["bin_id"]             = BIN_ID;
  doc["fill_level"]         = fillLevel;
  doc["latitude"]           = BIN_LATITUDE;
  doc["longitude"]          = BIN_LONGITUDE;
  doc["organic_percentage"] = ORGANIC_PCT;
  doc["plastic_percentage"] = PLASTIC_PCT;
  doc["metal_percentage"]   = METAL_PCT;
  doc["sensor_status"]      = (fillLevel == 50.0) ? "ERROR" : "ONLINE";
  doc["battery_level"]      = 100.0;   // No battery circuit — hardcoded 100
  doc["signal_strength"]    = signal;

  String payload;
  serializeJson(doc, payload);

  Serial.println("--- Sending to server ---");
  Serial.println(payload);

  // HTTP POST to Django
  WiFiClient client;
  HTTPClient http;
  String url = String(SERVER_URL) + String(API_ENDPOINT);
  
  Serial.print("[HTTP] Connecting to: ");
  Serial.println(url);
  
  http.begin(client, url);
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(3000);  // 3 second timeout
  
  Serial.println("[HTTP] Executing POST request...");
  int responseCode = http.POST(payload);
  Serial.println("[HTTP] POST execution finished.");

  if (responseCode == 200 || responseCode == 201) {
    Serial.print("[HTTP] SUCCESS — code: ");
    Serial.println(responseCode);
    Serial.println("[HTTP] Server accepted the data and updated the bin.");
  } else {
    Serial.print("[HTTP] FAILED — code: ");
    Serial.println(responseCode);
    if (responseCode > 0) {
      Serial.println("[HTTP] Server response: " + http.getString());
    } else {
      Serial.println("[HTTP] No response — check server IP and WiFi.");
    }
  }

  http.end();
}
