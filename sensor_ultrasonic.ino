/*
 * =====================================================================
 * SMART WASTE MANAGEMENT SYSTEM
 * Sensor : HC-SR04 Ultrasonic + Active Buzzer
 * Board  : ESP32 Dev Module
 *
 * ── TRANSPORT PRIORITY ──────────────────────────────────────────────
 * 1. USB SERIAL (primary)
 *    On startup the firmware waits 4 seconds for the Mac's
 *    serial_bridge.py to send "BRIDGE_READY".  If received → USB mode.
 *    Data is printed as a single-line JSON to Serial.
 *    serial_bridge.py reads it and POSTs it to Django — no WiFi needed.
 *
 * 2. WiFi HTTP (fallback)
 *    If no handshake arrives within 4 seconds (bridge not running),
 *    the firmware connects to WiFi and POSTs directly to Django.
 *
 * ── API PAYLOAD (POST /api/sensor-data/) ────────────────────────────
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
 * ── WIRING ───────────────────────────────────────────────────────────
 *   HC-SR04 TRIG  → GPIO 5
 *   HC-SR04 ECHO  → GPIO 18
 *   HC-SR04 VCC   → 5V (or 3.3V)
 *   HC-SR04 GND   → GND
 *   Active Buzzer + → GPIO 2
 *   Active Buzzer - → GND
 *
 * ── REQUIRED LIBRARIES ───────────────────────────────────────────────
 *   ArduinoJson  (v6.x) — install via Arduino IDE Library Manager
 * =====================================================================
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <ESPmDNS.h>

// =====================================================================
// SECTION 1: WIFI + SERVER SETTINGS (only used in WiFi fallback mode)
// =====================================================================
const char* WIFI_SSID     = "Orange-6B05";
const char* WIFI_PASSWORD = "GbYMLNLq7h4";
const char* MAC_HOSTNAME  = "Jams-MacBook-Pro.local";
const char* API_ENDPOINT  = "/api/sensor-data/";
String      SERVER_URL    = "";       // resolved at runtime via mDNS

// =====================================================================
// SECTION 2: BIN IDENTITY
// =====================================================================
const char* SENSOR_ID = "SENSOR_ULTRA_001";
const char* BIN_ID    = "BIN001";

// =====================================================================
// SECTION 3: BIN LOCATION
// =====================================================================
const float BIN_LATITUDE  = 4.0725;
const float BIN_LONGITUDE = 9.7634;

// =====================================================================
// SECTION 4: BIN PHYSICAL MEASUREMENTS
//   BIN_DEPTH_CM = distance from sensor to bin bottom when EMPTY
//   BIN_MIN_CM   = distance when bin is considered 100 % full
// =====================================================================
const float BIN_DEPTH_CM = 100.0;
const float BIN_MIN_CM   = 5.0;

// =====================================================================
// SECTION 5: WASTE COMPOSITION (must sum to 100.0)
// =====================================================================
const float ORGANIC_PCT = 40.0;
const float PLASTIC_PCT = 35.0;
const float METAL_PCT   = 25.0;

// =====================================================================
// SECTION 6: ALERT THRESHOLDS & TIMING
// =====================================================================
const float         WARN_THRESHOLD  = 65.0;  // triple-beep warning
const float         CRIT_THRESHOLD  = 85.0;  // continuous alarm
const unsigned long SEND_INTERVAL   = 500;   // send data every 500 ms
const unsigned long SENSOR_INTERVAL = 60;    // HC-SR04 minimum cycle (ms)
const unsigned long USB_WAIT_MS     = 4000;  // wait for bridge handshake (ms)

// =====================================================================
// PIN DEFINITIONS
// =====================================================================
#define TRIG_PIN  5
#define ECHO_PIN  18
#define BUZZ_PIN  2

// =====================================================================
// GLOBAL STATE
// =====================================================================
bool          USB_MODE      = false;   // true = send via Serial, false = WiFi
unsigned long lastSendTime  = 0;
unsigned long lastReadTime  = 0;
float         lastFillLevel = 0.0;

// =====================================================================
// FORWARD DECLARATIONS
// =====================================================================
void  connectWiFi();
float readDistanceCm();
float distanceToFillLevel(float distanceCm);
void  buzzerAlert(float fillLevel);
void  sendSensorData(float fillLevel);
void  sendViaUSB(float fillLevel);
void  sendViaWiFi(float fillLevel);

// =====================================================================
// SETUP
// =====================================================================
void setup() {
  Serial.begin(115200);
  delay(500);

  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(BUZZ_PIN, OUTPUT);
  digitalWrite(TRIG_PIN, LOW);
  digitalWrite(BUZZ_PIN, LOW);

  Serial.println(F("===================================="));
  Serial.println(F("  Smart Waste — Ultrasonic Sensor  "));
  Serial.println(F("===================================="));
  Serial.print(F("Sensor ID : ")); Serial.println(SENSOR_ID);
  Serial.print(F("Bin ID    : ")); Serial.println(BIN_ID);
  Serial.println();

  // ── USB handshake detection ──────────────────────────────────────
  Serial.println(F("[USB] Waiting for serial_bridge.py handshake..."));
  Serial.println(F("[USB] (Run:  python3 serial_bridge.py  on your Mac)"));
  Serial.println(F("[USB] Waiting 4 seconds..."));

  unsigned long waitStart = millis();
  while (millis() - waitStart < USB_WAIT_MS) {
    if (Serial.available()) {
      String incoming = Serial.readStringUntil('\n');
      incoming.trim();
      if (incoming == "BRIDGE_READY") {
        USB_MODE = true;
        break;
      }
    }
    delay(50);
  }

  if (USB_MODE) {
    Serial.println(F("[USB] ✅ Bridge detected! Running in USB mode."));
    Serial.println(F("[USB] Data will be sent via USB Serial to Django."));
  } else {
    Serial.println(F("[WiFi] No bridge found — falling back to WiFi mode."));
    connectWiFi();
  }

  // Take first reading immediately
  lastFillLevel = distanceToFillLevel(readDistanceCm());
  sendSensorData(lastFillLevel);
  lastSendTime = millis();
}

// =====================================================================
// MAIN LOOP
// =====================================================================
void loop() {
  // 1. Read sensor every SENSOR_INTERVAL ms
  if (millis() - lastReadTime >= SENSOR_INTERVAL) {
    float distance = readDistanceCm();
    lastFillLevel  = distanceToFillLevel(distance);
    buzzerAlert(lastFillLevel);
    lastReadTime = millis();
  }

  // 2. WiFi-only: reconnect if dropped
  if (!USB_MODE && WiFi.status() != WL_CONNECTED) {
    Serial.println(F("[WiFi] Lost connection — reconnecting..."));
    connectWiFi();
  }

  // 3. Send data every SEND_INTERVAL ms
  if (millis() - lastSendTime >= SEND_INTERVAL) {
    sendSensorData(lastFillLevel);
    lastSendTime = millis();
  }
}

// =====================================================================
// ROUTER: picks USB or WiFi transport
// =====================================================================
void sendSensorData(float fillLevel) {
  if (USB_MODE) {
    sendViaUSB(fillLevel);
  } else {
    sendViaWiFi(fillLevel);
  }
}

// =====================================================================
// SEND VIA USB SERIAL
// Prints a single-line JSON that serial_bridge.py reads and POSTs.
// =====================================================================
void sendViaUSB(float fillLevel) {
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
  doc["battery_level"]      = 100.0;
  doc["signal_strength"]    = -1;   // no WiFi in USB mode

  String payload;
  serializeJson(doc, payload);

  // serial_bridge.py detects lines starting with '{' as JSON payloads
  Serial.println(payload);
  Serial.print(F("[USB] Sent  fill="));
  Serial.print(fillLevel, 1);
  Serial.println(F("%"));
}

// =====================================================================
// SEND VIA WIFI HTTP POST
// =====================================================================
void sendViaWiFi(float fillLevel) {
  int signal = WiFi.RSSI();

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
  doc["battery_level"]      = 100.0;
  doc["signal_strength"]    = signal;

  String payload;
  serializeJson(doc, payload);

  Serial.println(F("--- Sending via WiFi ---"));
  Serial.println(payload);

  WiFiClient client;
  HTTPClient http;
  String url = SERVER_URL + String(API_ENDPOINT);

  Serial.print(F("[HTTP] → ")); Serial.println(url);

  http.begin(client, url);
  http.addHeader("Content-Type", "application/json");
  http.setFollowRedirects(HTTPC_STRICT_FOLLOW_REDIRECTS);
  http.setTimeout(3000);

  int code = http.POST(payload);

  if (code == 200 || code == 201) {
    Serial.print(F("[HTTP] ✅ SUCCESS  code=")); Serial.println(code);
  } else {
    Serial.print(F("[HTTP] ❌ FAILED   code=")); Serial.println(code);
    if (code > 0) Serial.println("[HTTP] Response: " + http.getString());
    else          Serial.println(F("[HTTP] No response — check IP/WiFi."));
  }

  http.end();
}

// =====================================================================
// FUNCTION: Connect to WiFi + resolve Mac IP via mDNS
// =====================================================================
void connectWiFi() {
  Serial.print(F("[WiFi] Connecting to ")); Serial.print(WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 40) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println(F("[WiFi] ✅ Connected!"));
    Serial.print(F("[WiFi] IP: ")); Serial.println(WiFi.localIP());
    Serial.print(F("[WiFi] Signal: ")); Serial.print(WiFi.RSSI()); Serial.println(F(" dBm"));

    IPAddress serverIP;
    Serial.print(F("[mDNS] Resolving ")); Serial.print(MAC_HOSTNAME); Serial.println(F("..."));
    if (WiFi.hostByName(MAC_HOSTNAME, serverIP) == 1) {
      SERVER_URL = "http://" + serverIP.toString() + ":8000";
      Serial.print(F("[mDNS] ✅ Resolved: ")); Serial.println(SERVER_URL);
    } else {
      SERVER_URL = "http://192.168.43.148:8000";
      Serial.println(F("[mDNS] ⚠️  Could not resolve — using fallback IP."));
    }
  } else {
    Serial.println(F("[WiFi] ❌ FAILED to connect."));
  }
}

// =====================================================================
// FUNCTION: Read distance in cm from HC-SR04
// =====================================================================
float readDistanceCm() {
  digitalWrite(TRIG_PIN, LOW);  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH); delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  long duration = pulseIn(ECHO_PIN, HIGH, 30000);
  if (duration == 0) {
    Serial.println(F("[Sensor] No echo — sensor not connected or blocked!"));
    return -1;
  }

  float distanceCm = duration * 0.034 / 2.0;
  Serial.print(F("[Sensor] Distance: ")); Serial.print(distanceCm, 1); Serial.println(F(" cm"));
  return distanceCm;
}

// =====================================================================
// FUNCTION: Convert distance → fill level %
// =====================================================================
float distanceToFillLevel(float distanceCm) {
  if (distanceCm < 0) return 50.0;  // sensor error → safe default

  float fillLevel;
  if      (distanceCm <= BIN_MIN_CM)   fillLevel = 100.0;
  else if (distanceCm >= BIN_DEPTH_CM) fillLevel = 0.0;
  else    fillLevel = ((BIN_DEPTH_CM - distanceCm) / (BIN_DEPTH_CM - BIN_MIN_CM)) * 100.0;

  fillLevel = constrain(fillLevel, 0.0, 100.0);
  Serial.print(F("[Sensor] Fill: ")); Serial.print(fillLevel, 1); Serial.println(F("%"));
  return fillLevel;
}

// =====================================================================
// FUNCTION: Buzzer alert
//   >= 85%        → continuous alarm
//   65% – 85%     → triple-beep loop
//   < 65%         → silent
// =====================================================================
void buzzerAlert(float fillLevel) {
  if (fillLevel >= CRIT_THRESHOLD) {
    Serial.println(F("[BUZZ] CRITICAL — continuous alarm!"));
    digitalWrite(BUZZ_PIN, HIGH);

  } else if (fillLevel >= WARN_THRESHOLD) {
    Serial.println(F("[BUZZ] WARNING — triple beep!"));
    for (int i = 0; i < 3; i++) {
      digitalWrite(BUZZ_PIN, HIGH); delay(100);
      digitalWrite(BUZZ_PIN, LOW);  delay(50);
    }
    delay(400);

  } else {
    digitalWrite(BUZZ_PIN, LOW);
  }
}
