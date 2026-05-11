/*
 * =============================================================================
 *  SMART WASTE BIN — UNIFIED FIRMWARE v1.0
 * =============================================================================
 *
 *  Hardware:
 *    - ESP32-CAM (AI-Thinker)       → Camera + WiFi controller
 *    - HC-SR04 Ultrasonic Sensor    → Fill level detection
 *    - HC-SR501 PIR Motion Sensor   → Detects nearby motion
 *    - Active Buzzer                → Audible alert when bin is full (>85%)
 *
 *  Pin Mapping (all on the ESP32-CAM board):
 *    TRIG_PIN     = GPIO 12  ← HC-SR04 Trigger
 *    ECHO_PIN     = GPIO 13  ← HC-SR04 Echo
 *    PIR_PIN      = GPIO 14  ← HC-SR501 OUT
 *    BUZZER_PIN   = GPIO 15  ← Active Buzzer
 *    LED_PIN      = GPIO  4  ← Onboard LED (status)
 *    FLASH_PIN    = GPIO  2  ← Camera flash
 *
 *  NOTE: GPIO 0,2,4,5,12-15,21,22,25-27,32,34-36,39 are used by the
 *        AI-Thinker ESP32-CAM camera data bus. The pins chosen above
 *        (12,13,14,15) are the safe "free" GPIOs on that board that
 *        are NOT part of the camera data bus while the camera is running.
 *
 *  Behaviour:
 *    - Every 30 s: read ultrasonic fill level → POST to Django API
 *    - Fill > 85%: trigger buzzer alert (3 short beeps)
 *    - PIR detects motion: immediately capture + upload camera image
 *    - Camera also captures on a 60-second periodic schedule
 *
 *  Author : Smart Waste Management System
 *  Version: 1.0 (Unified Production)
 * =============================================================================
 */

#include "esp_camera.h"
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <esp_wifi.h>

// =============================================================================
//  CONFIGURATION  ← Update these values for your deployment
// =============================================================================

// --- WiFi ---
const char* WIFI_SSID     = "Orange-6B05";          // Your WiFi SSID
const char* WIFI_PASSWORD = "GbYMLNLq7h4";          // Your WiFi password

// --- Django Server ---
const char* SERVER_URL       = "http://192.168.1.116:8000"; // Django server IP
const char* SENSOR_ENDPOINT  = "/api/sensor-data/";
const char* CAMERA_ENDPOINT  = "/api/esp32-cam-upload/";

// --- Bin Identity ---
const String SENSOR_ID  = "SENSOR_001";   // Unique sensor ID
const String BIN_ID     = "BIN001";       // Which bin this unit is installed in
const String CAMERA_ID  = "CAM_BIN001";   // Camera identity for image uploads

// --- Bin Location ---
const float BIN_LATITUDE  = 4.0725;
const float BIN_LONGITUDE = 9.7634;

// --- Bin Physical Dimensions ---
const int BIN_DEPTH_CM  = 60;  // Total depth of bin interior in cm (sensor to bottom)
const int MIN_DIST_CM   = 5;   // Distance (cm) when bin is 100% full
const int MAX_DIST_CM   = 60;  // Distance (cm) when bin is 0% full (= BIN_DEPTH_CM)

// --- Alert Threshold ---
const float BUZZ_THRESHOLD = 85.0;  // Trigger buzzer when fill level > 85%

// --- Timing ---
const unsigned long SENSOR_INTERVAL  = 30000;  // 30 s  → POST sensor data
const unsigned long CAMERA_INTERVAL  = 60000;  // 60 s  → periodic camera capture
const unsigned long WIFI_CHECK_MS    = 30000;  // 30 s  → WiFi health check
const int           WIFI_TIMEOUT_MS  = 20000;  // 20 s  → max wait to connect
const int           HTTP_TIMEOUT_MS  = 15000;  // 15 s  → HTTP request timeout
const int           MAX_RETRIES      = 3;      // upload retry attempts

// --- PIR Cooldown ---
// After PIR fires and we take a photo, ignore further PIR triggers for this
// many milliseconds to avoid hammering the server with repeated images.
const unsigned long PIR_COOLDOWN_MS = 15000;   // 15 s cooldown

// =============================================================================
//  PIN DEFINITIONS
// =============================================================================

// Ultrasonic HC-SR04
#define TRIG_PIN   12
#define ECHO_PIN   13

// PIR HC-SR501
#define PIR_PIN    14

// Buzzer
#define BUZZER_PIN 15

// ESP32-CAM onboard LEDs
#define LED_PIN     4   // status LED
#define FLASH_PIN   2   // camera flash

// =============================================================================
//  GLOBAL STATE
// =============================================================================

bool          wifiConnected       = false;
unsigned long lastSensorSend      = 0;
unsigned long lastCameraCapture   = 0;
unsigned long lastWifiCheck       = 0;
unsigned long lastPirTrigger      = 0;
int           consecutiveFailures = 0;
const int     MAX_FAILURES        = 5;

// =============================================================================
//  SETUP
// =============================================================================

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n============================================");
  Serial.println(" Smart Waste Bin — Unified Firmware v1.0");
  Serial.println("============================================");

  // --- GPIO setup ---
  pinMode(TRIG_PIN,   OUTPUT);
  pinMode(ECHO_PIN,   INPUT);
  pinMode(PIR_PIN,    INPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(LED_PIN,    OUTPUT);
  pinMode(FLASH_PIN,  OUTPUT);

  digitalWrite(TRIG_PIN,   LOW);
  digitalWrite(BUZZER_PIN, LOW);
  digitalWrite(LED_PIN,    LOW);
  digitalWrite(FLASH_PIN,  LOW);

  Serial.println("[GPIO] All pins initialised.");

  // --- PIR warmup countdown ---
  Serial.println("[PIR] HC-SR501 warming up (30 s)...");
  for (int i = 30; i > 0; i--) {
    Serial.print("  Ready in: ");
    Serial.print(i);
    Serial.println(" s");
    delay(1000);
  }
  Serial.println("[PIR] PIR sensor ready!");

  // --- Camera init ---
  if (!initCamera()) {
    Serial.println("[CAM] ERROR: Camera init failed — rebooting in 5 s...");
    blinkError(10);
    delay(5000);
    ESP.restart();
  }
  Serial.println("[CAM] Camera initialised.");

  // --- WiFi ---
  connectWifi();

  // --- First sensor read right away ---
  if (wifiConnected) {
    readAndSendSensorData();
    lastSensorSend = millis();
  }

  Serial.println("[SYS] Setup complete. Entering main loop...\n");
}

// =============================================================================
//  MAIN LOOP
// =============================================================================

void loop() {
  unsigned long now = millis();

  // 1. WiFi health check
  if (now - lastWifiCheck >= WIFI_CHECK_MS) {
    if (WiFi.status() != WL_CONNECTED) {
      Serial.println("[WiFi] Connection lost — reconnecting...");
      connectWifi();
    }
    lastWifiCheck = now;
  }

  // 2. Periodic sensor data upload (every 30 s)
  if (wifiConnected && (now - lastSensorSend >= SENSOR_INTERVAL)) {
    readAndSendSensorData();
    lastSensorSend = now;
  }

  // 3. PIR motion detection → immediate camera snapshot
  if (digitalRead(PIR_PIN) == HIGH) {
    if ((now - lastPirTrigger) >= PIR_COOLDOWN_MS) {
      Serial.println("[PIR] MOTION DETECTED — triggering camera!");
      lastPirTrigger = now;
      if (wifiConnected) {
        captureAndUploadImage("MOTION");
        lastCameraCapture = now;
      } else {
        Serial.println("[PIR] WiFi unavailable — image not sent.");
      }
    }
  }

  // 4. Periodic camera capture (every 60 s, independent of PIR)
  if (wifiConnected && (now - lastCameraCapture >= CAMERA_INTERVAL)) {
    captureAndUploadImage("SCHEDULED");
    lastCameraCapture = now;
  }

  yield();
  delay(500);
}

// =============================================================================
//  ULTRASONIC — READ FILL LEVEL
// =============================================================================

float readFillLevel() {
  // Send a 10-µs pulse
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  // Read echo (30 ms timeout = ~510 cm max — well beyond any bin)
  long duration = pulseIn(ECHO_PIN, HIGH, 30000);

  if (duration == 0) {
    Serial.println("[ULTRA] No echo — sensor error. Defaulting to 50%.");
    return 50.0;
  }

  float distance = duration * 0.034 / 2.0;
  float fill     = 0.0;

  if (distance >= MAX_DIST_CM) {
    fill = 0.0;
  } else if (distance <= MIN_DIST_CM) {
    fill = 100.0;
  } else {
    fill = ((float)(MAX_DIST_CM - distance) / (float)(MAX_DIST_CM - MIN_DIST_CM)) * 100.0;
  }

  fill = constrain(fill, 0.0, 100.0);

  Serial.print("[ULTRA] Distance: ");
  Serial.print(distance, 1);
  Serial.print(" cm  →  Fill: ");
  Serial.print(fill, 1);
  Serial.println("%");

  return fill;
}

// =============================================================================
//  BUZZER — ALERT PATTERN
// =============================================================================

void triggerBuzzerAlert() {
  Serial.println("[BUZZ] Fill > 85% — triggering 3-beep alert!");
  for (int i = 0; i < 3; i++) {
    digitalWrite(BUZZER_PIN, HIGH);
    delay(300);
    digitalWrite(BUZZER_PIN, LOW);
    delay(200);
  }
}

// =============================================================================
//  SENSOR DATA — BUILD JSON & POST
// =============================================================================

void readAndSendSensorData() {
  Serial.println("\n[SENSOR] Reading and sending sensor data...");

  float fillLevel     = readFillLevel();
  float batteryLevel  = 100.0;               // Placeholder — add ADC circuit for real reading
  int   signalStrength = WiFi.RSSI();

  // Alert if bin is above threshold
  if (fillLevel >= BUZZ_THRESHOLD) {
    triggerBuzzerAlert();
  }

  // Build JSON payload
  DynamicJsonDocument doc(512);
  doc["sensor_id"]          = SENSOR_ID;
  doc["bin_id"]             = BIN_ID;
  doc["fill_level"]         = fillLevel;
  doc["latitude"]           = BIN_LATITUDE;
  doc["longitude"]          = BIN_LONGITUDE;
  doc["organic_percentage"] = 0;   // If you add a waste-type sensor, update here
  doc["plastic_percentage"] = 0;
  doc["metal_percentage"]   = 0;
  doc["sensor_status"]      = wifiConnected ? "ONLINE" : "OFFLINE";
  doc["battery_level"]      = batteryLevel;
  doc["signal_strength"]    = signalStrength;
  doc["temperature"]        = 0;   // Add DHT22 here if needed
  doc["humidity"]           = 0;

  String jsonStr;
  serializeJson(doc, jsonStr);

  Serial.print("[SENSOR] Payload: ");
  Serial.println(jsonStr);

  // Send with retry
  bool sent = false;
  for (int attempt = 1; attempt <= MAX_RETRIES; attempt++) {
    Serial.printf("[SENSOR] Upload attempt %d/%d...\n", attempt, MAX_RETRIES);
    HTTPClient http;
    String url = String(SERVER_URL) + String(SENSOR_ENDPOINT);
    http.begin(url);
    http.addHeader("Content-Type", "application/json");
    http.setTimeout(HTTP_TIMEOUT_MS);

    int code = http.POST(jsonStr);
    if (code == 200 || code == 201) {
      Serial.println("[SENSOR] Data sent successfully!");
      blinkOK(2);
      sent = true;
      consecutiveFailures = 0;
      http.end();
      break;
    } else {
      Serial.printf("[SENSOR] Failed with code %d\n", code);
      http.end();
      if (attempt < MAX_RETRIES) delay(5000);
    }
  }

  if (!sent) {
    Serial.println("[SENSOR] All retry attempts failed.");
    consecutiveFailures++;
    blinkError(3);
    if (consecutiveFailures >= MAX_FAILURES) {
      Serial.println("[SYS] Too many failures — restarting...");
      delay(3000);
      ESP.restart();
    }
  }
}

// =============================================================================
//  CAMERA — INIT
// =============================================================================

bool initCamera() {
  camera_config_t config;
  config.ledc_channel  = LEDC_CHANNEL_0;
  config.ledc_timer    = LEDC_TIMER_0;
  config.pin_d0        = 5;
  config.pin_d1        = 18;
  config.pin_d2        = 19;
  config.pin_d3        = 21;
  config.pin_d4        = 36;
  config.pin_d5        = 39;
  config.pin_d6        = 34;
  config.pin_d7        = 35;
  config.pin_xclk      = 0;
  config.pin_pclk      = 22;
  config.pin_vsync     = 25;
  config.pin_href       = 23;
  config.pin_sscb_sda  = 26;
  config.pin_sscb_scl  = 27;
  config.pin_pwdn      = 32;
  config.pin_reset     = -1;
  config.xclk_freq_hz  = 20000000;
  config.pixel_format  = PIXFORMAT_JPEG;
  config.grab_mode     = CAMERA_GRAB_WHEN_EMPTY;

  if (psramFound()) {
    config.frame_size  = FRAMESIZE_SVGA;       // 800×600
    config.jpeg_quality = 10;
    config.fb_count    = 2;
    config.fb_location = CAMERA_FB_IN_PSRAM;
  } else {
    config.frame_size  = FRAMESIZE_VGA;        // 640×480
    config.jpeg_quality = 15;
    config.fb_count    = 1;
    config.fb_location = CAMERA_FB_IN_DRAM;
  }

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("[CAM] esp_camera_init failed: 0x%x\n", err);
    return false;
  }

  // Optimise sensor
  sensor_t* s = esp_camera_sensor_get();
  if (s) {
    s->set_brightness(s, 0);
    s->set_contrast(s, 0);
    s->set_whitebal(s, 1);
    s->set_awb_gain(s, 1);
    s->set_exposure_ctrl(s, 1);
    s->set_gain_ctrl(s, 1);
  }

  return true;
}

// =============================================================================
//  CAMERA — CAPTURE + UPLOAD
// =============================================================================

void captureAndUploadImage(const char* triggerReason) {
  Serial.printf("\n[CAM] Capturing image (trigger: %s)...\n", triggerReason);

  // Flash on
  digitalWrite(FLASH_PIN, HIGH);
  delay(100);

  camera_fb_t* fb = esp_camera_fb_get();
  digitalWrite(FLASH_PIN, LOW);

  if (!fb) {
    Serial.println("[CAM] Failed to capture frame!");
    return;
  }

  Serial.printf("[CAM] Captured %dx%d image, %d bytes\n", fb->width, fb->height, fb->len);

  // Upload with retry
  bool sent = false;
  for (int attempt = 1; attempt <= MAX_RETRIES; attempt++) {
    Serial.printf("[CAM] Upload attempt %d/%d...\n", attempt, MAX_RETRIES);

    HTTPClient http;
    String url = String(SERVER_URL) + String(CAMERA_ENDPOINT);
    http.begin(url);
    http.addHeader("X-Camera-ID",      CAMERA_ID);
    http.addHeader("X-Camera-Type",    "ESP32-CAM");
    http.addHeader("X-Trigger",        triggerReason);
    http.addHeader("X-Bin-ID",         BIN_ID);
    http.addHeader("X-Analysis-Type",  "WASTE_CLASSIFICATION");
    http.addHeader("Content-Type",     "image/jpeg");
    http.setTimeout(HTTP_TIMEOUT_MS);

    int code = http.POST(fb->buf, fb->len);
    if (code == 200 || code == 201) {
      Serial.println("[CAM] Image uploaded successfully!");
      blinkOK(3);
      sent = true;
      http.end();
      break;
    } else {
      Serial.printf("[CAM] Upload failed with code %d\n", code);
      http.end();
      if (attempt < MAX_RETRIES) delay(5000);
    }
  }

  esp_camera_fb_return(fb);

  if (!sent) {
    Serial.println("[CAM] All upload attempts failed.");
    blinkError(5);
  }
}

// =============================================================================
//  WiFi
// =============================================================================

void connectWifi() {
  Serial.print("[WiFi] Connecting to ");
  Serial.println(WIFI_SSID);

  if (WiFi.status() == WL_CONNECTED) {
    WiFi.disconnect();
    delay(1000);
  }

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < WIFI_TIMEOUT_MS) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {
    wifiConnected = true;
    Serial.println("[WiFi] Connected!");
    Serial.print("[WiFi] IP: ");
    Serial.println(WiFi.localIP());
    Serial.printf("[WiFi] RSSI: %d dBm\n", WiFi.RSSI());
    blinkOK(3);
  } else {
    wifiConnected = false;
    Serial.println("[WiFi] Connection failed!");
    blinkError(5);
  }
}

// =============================================================================
//  LED HELPERS
// =============================================================================

void blinkOK(int times) {
  for (int i = 0; i < times; i++) {
    digitalWrite(LED_PIN, HIGH); delay(150);
    digitalWrite(LED_PIN, LOW);  delay(150);
  }
}

void blinkError(int times) {
  for (int i = 0; i < times; i++) {
    digitalWrite(LED_PIN, HIGH); delay(80);
    digitalWrite(LED_PIN, LOW);  delay(80);
  }
}

// =============================================================================
//  END OF UNIFIED FIRMWARE
// =============================================================================
