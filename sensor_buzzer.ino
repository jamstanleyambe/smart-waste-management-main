/*
 * =====================================================================
 * SMART WASTE MANAGEMENT SYSTEM
 * Sensor: Active Buzzer — Standalone Alert Unit
 * Board:  ESP32 Dev Module
 *
 * WHAT THIS DOES:
 *   This is a STANDALONE buzzer unit that reads fill level FROM the
 *   Django server and sounds an alert if a bin is too full.
 *
 *   Use this if you want a buzzer in a location separate from the
 *   ultrasonic sensor (e.g. at a collection station or office).
 *   If your buzzer is on the same ESP32 as the ultrasonic sensor,
 *   use sensor_ultrasonic.ino instead — it already handles the buzzer.
 *
 *   Every CHECK_INTERVAL milliseconds:
 *     1. GET /api/bin-data/?bin_id=BIN001 from Django
 *     2. Parse the fill level from the response
 *     3. If fill >= 85% → buzzer stays ON (continuous alert)
 *     4. If fill >= 70% → one short beep (warning)
 *     5. If fill <  70% → buzzer OFF (silent)
 *
 * WIRING:
 *   Active Buzzer + → ESP32 GPIO 2
 *   Active Buzzer - → ESP32 GND
 *   LED (optional) → ESP32 GPIO 4 + 330Ω resistor → GND
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

// =====================================================================
// SECTION 1: WIFI + SERVER SETTINGS
// =====================================================================
const char* WIFI_SSID     = "Orange-6B05";
const char* WIFI_PASSWORD = "GbYMLNLq7h4";
// Mac's permanent Bonjour hostname — works on ANY WiFi network, never changes
const char* MAC_HOSTNAME  = "Jams-MacBook-Pro.local";

// Which bin this buzzer unit is watching — must match a bin_id in the database
const char* BIN_ID = "BIN001";

String SERVER_URL = "";  // Resolved from hostname at runtime

// =====================================================================
// SECTION 2: ALERT THRESHOLDS
// =====================================================================
const float ALERT_THRESHOLD   = 85.0;  // Continuous buzzer above this
const float WARNING_THRESHOLD = 70.0;  // Single short beep above this

// =====================================================================
// SECTION 3: CHECK INTERVAL
// How often to poll the server for the latest fill level
// =====================================================================
const unsigned long CHECK_INTERVAL = 5000;  // Check every 5 seconds

// =====================================================================
// PIN DEFINITIONS
// =====================================================================
#define BUZZ_PIN 2   // Active buzzer signal pin
#define LED_PIN  4   // Status LED (optional)

// =====================================================================
// GLOBAL VARIABLES
// =====================================================================
unsigned long lastCheck    = 0;
float         lastFillLevel = 0.0;   // Last known fill level from server
bool          alertActive  = false;  // True when continuous buzzer is ON

// =====================================================================
// SETUP — runs once when ESP32 powers on
// =====================================================================
void setup() {
  Serial.begin(115200);
  delay(1000);

  pinMode(BUZZ_PIN, OUTPUT);
  pinMode(LED_PIN,  OUTPUT);
  digitalWrite(BUZZ_PIN, LOW);
  digitalWrite(LED_PIN,  LOW);

  Serial.println("=== Bin Buzzer Alert System ===");
  Serial.print("Watching bin : "); Serial.println(BIN_ID);
  Serial.print("Alert at     : "); Serial.print(ALERT_THRESHOLD);   Serial.println("%");
  Serial.print("Warning at   : "); Serial.print(WARNING_THRESHOLD); Serial.println("%");

  // Connect to WiFi
  connectWiFi();

  // Startup beep — confirms buzzer hardware is working
  Serial.println("[BUZZ] Startup beep test...");
  beepOnce(200);
  delay(300);
  beepOnce(200);

  // Check fill level immediately on boot
  checkAndAlert();
  lastCheck = millis();
}

// =====================================================================
// MAIN LOOP — repeats forever
// =====================================================================
void loop() {
  // 1. Reconnect WiFi if dropped
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[WiFi] Lost — reconnecting...");
    // Turn off buzzer while reconnecting so we don't alert on stale data
    digitalWrite(BUZZ_PIN, LOW);
    alertActive = false;
    connectWiFi();
  }

  // 2. Poll server every CHECK_INTERVAL ms
  if (millis() - lastCheck >= CHECK_INTERVAL) {
    checkAndAlert();
    lastCheck = millis();
  }

  // 3. If continuous alert is active, keep buzzer ON between polls
  //    (so it doesn't go silent between 5-second checks)
  if (alertActive) {
    digitalWrite(BUZZ_PIN, HIGH);
  }

  // No delay() — loop driven by millis() timers
}

// =====================================================================
// FUNCTION: Connect to WiFi + resolve Mac hostname via mDNS
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
    Serial.print("[WiFi] IP: "); Serial.println(WiFi.localIP());

    // Resolve Mac hostname via mDNS
    Serial.print("[mDNS] Resolving "); Serial.print(MAC_HOSTNAME); Serial.println("...");
    IPAddress serverIP;
    int resolved = WiFi.hostByName(MAC_HOSTNAME, serverIP);
    if (resolved == 1) {
      SERVER_URL = "http://" + serverIP.toString() + ":8000";
      Serial.print("[mDNS] Resolved to: "); Serial.println(SERVER_URL);
    } else {
      SERVER_URL = "http://192.168.1.128:8000";
      Serial.println("[mDNS] Could not resolve — using fallback IP.");
    }
  } else {
    Serial.println("[WiFi] FAILED. Will retry next loop.");
  }
}

// =====================================================================
// FUNCTION: GET fill level from server and decide alert state
// =====================================================================
void checkAndAlert() {
  Serial.println("\n[HTTP] Fetching fill level from server...");

  String url = String(SERVER_URL) + "/api/bin-data/?bin_id=" + String(BIN_ID);

  HTTPClient http;
  http.begin(url);
  http.setTimeout(2000);  // 2 second timeout — don't block too long

  int code = http.GET();

  if (code != 200) {
    Serial.print("[HTTP] Request failed — code: ");
    Serial.println(code);
    http.end();
    // 5 rapid error beeps
    for (int i = 0; i < 5; i++) {
      beepOnce(50);
      delay(50);
    }
    return;
  }

  String response = http.getString();
  http.end();

  Serial.println("[HTTP] Response received.");

  // Parse JSON — API may return array, single object, or paginated
  DynamicJsonDocument doc(2048);
  DeserializationError err = deserializeJson(doc, response);

  if (err) {
    Serial.print("[JSON] Parse error: ");
    Serial.println(err.c_str());
    return;
  }

  // Extract fill level from whichever response format is returned
  if (doc.is<JsonArray>() && doc.size() > 0) {
    lastFillLevel = doc[0]["fill_level"].as<float>();
  } else if (doc.containsKey("fill_level")) {
    lastFillLevel = doc["fill_level"].as<float>();
  } else if (doc.containsKey("results") && doc["results"].size() > 0) {
    lastFillLevel = doc["results"][0]["fill_level"].as<float>();
  } else {
    Serial.println("[JSON] Could not find fill_level in response.");
    return;
  }

  Serial.print("[BIN] Current fill level: ");
  Serial.print(lastFillLevel, 1);
  Serial.println("%");

  // --- Apply alert logic ---
  if (lastFillLevel >= ALERT_THRESHOLD) {
    // CRITICAL: continuous buzzer ON until fill drops below threshold
    Serial.println("[ALERT] Bin CRITICAL (>= 85%) — continuous buzzer ON!");
    alertActive = true;
    digitalWrite(BUZZ_PIN, HIGH);
    digitalWrite(LED_PIN,  HIGH);

  } else if (lastFillLevel >= WARNING_THRESHOLD) {
    // WARNING: one short beep, then silence
    Serial.println("[WARNING] Bin HIGH (>= 70%) — 1 warning beep.");
    alertActive = false;
    digitalWrite(BUZZ_PIN, LOW);
    digitalWrite(LED_PIN,  LOW);
    beepOnce(400);

  } else {
    // OK: silent
    Serial.println("[OK] Bin level is fine — silent.");
    alertActive = false;
    digitalWrite(BUZZ_PIN, LOW);
    digitalWrite(LED_PIN,  LOW);
  }
}

// =====================================================================
// HELPERS: Beep patterns
// =====================================================================

// Single beep of given duration (ms)
void beepOnce(int durationMs) {
  digitalWrite(BUZZ_PIN, HIGH);
  delay(durationMs);
  digitalWrite(BUZZ_PIN, LOW);
}
