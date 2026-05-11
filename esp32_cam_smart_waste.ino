/*
 * =====================================================================
 * SMART WASTE MANAGEMENT SYSTEM
 * Module: ESP32-CAM — Waste Dataset Capture
 * Board:  AI Thinker ESP32-CAM
 *
 * WHAT THIS DOES:
 *   1. Connects to WiFi and resolves Django server via mDNS
 *   2. Polls Django every 500ms for the current bin fill level
 *   3. When fill level changes by >= 1% since the last photo:
 *      → Captures a JPEG photo
 *      → Uploads it to Django tagged with bin_id + fill_level
 *   This builds a continuous visual dataset at every fill stage
 *   for waste segmentation / ML training.
 *
 * ENDPOINTS USED:
 *   GET  /api/bin-data/?bin_id=BIN001  → get current fill level
 *   POST /api/camera-images/           → upload photo + metadata
 *
 * ARDUINO IDE BOARD SETTINGS:
 *   Tools → Board    → AI Thinker ESP32-CAM
 *   Tools → Port     → your COM/USB port
 *   Tools → Baud Rate → 115200
 *   GPIO 0 → GND to flash, then disconnect for normal run
 * =====================================================================
 */

#include "esp_camera.h"
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// =====================================================================
// SECTION 1: WIFI + SERVER SETTINGS
// =====================================================================
const char* WIFI_SSID     = "Orange-6B05";
const char* WIFI_PASSWORD = "GbYMLNLq7h4";
const char* MAC_HOSTNAME  = "Jams-MacBook-Pro.local";
const char* FILL_ENDPOINT   = "/api/bin-data/";
const char* UPLOAD_ENDPOINT = "/api/esp32-cam-upload/";
String SERVER_URL = "";  // Resolved from hostname at runtime

// =====================================================================
// SECTION 2: BIN IDENTITY
// =====================================================================
const char* CAMERA_ID = "ESP32_CAM_001";
const char* BIN_ID    = "BIN001";

// =====================================================================
// SECTION 3: CAPTURE SETTINGS
// =====================================================================
const float          FILL_CHANGE_THRESHOLD = 1.0;   // Photo if fill changes >= 1%
const unsigned long  POLL_INTERVAL         = 500;   // Poll Django every 500ms

// =====================================================================
// CAMERA PIN DEFINITIONS (AI Thinker ESP32-CAM)
// =====================================================================
#define PWDN_GPIO_NUM   32
#define RESET_GPIO_NUM  -1
#define XCLK_GPIO_NUM    0
#define SIOD_GPIO_NUM   26
#define SIOC_GPIO_NUM   27
#define Y9_GPIO_NUM     35
#define Y8_GPIO_NUM     34
#define Y7_GPIO_NUM     39
#define Y6_GPIO_NUM     36
#define Y5_GPIO_NUM     21
#define Y4_GPIO_NUM     19
#define Y3_GPIO_NUM     18
#define Y2_GPIO_NUM      5
#define VSYNC_GPIO_NUM  25
#define HREF_GPIO_NUM   23
#define PCLK_GPIO_NUM   22
#define FLASH_PIN        4   // Built-in flash LED

// =====================================================================
// GLOBAL VARIABLES
// =====================================================================
float         lastPhotoFillLevel = -999.0;  // -999 forces first photo on boot
unsigned long lastPollTime       = 0;
int           photoCount         = 0;

// =====================================================================
// SETUP
// =====================================================================
void setup() {
  Serial.begin(115200);
  delay(1000);

  pinMode(FLASH_PIN, OUTPUT);
  digitalWrite(FLASH_PIN, LOW);

  Serial.println("====================================");
  Serial.println("  Smart Waste — ESP32-CAM Dataset  ");
  Serial.println("  >>> CODE VERSION 2.0 <<<          ");
  Serial.println("====================================");
  Serial.print("[SYS] PSRAM: ");
  Serial.println(psramFound() ? "FOUND" : "NOT FOUND");
  Serial.print("Camera ID : "); Serial.println(CAMERA_ID);
  Serial.print("Bin ID    : "); Serial.println(BIN_ID);
  Serial.print("Threshold : "); Serial.print(FILL_CHANGE_THRESHOLD);
  Serial.println("% change triggers photo");

  // Print available memory BEFORE camera init
  Serial.print("[SYS] Free heap: "); Serial.println(ESP.getFreeHeap());
  Serial.print("[SYS] Largest free block: "); Serial.println(ESP.getMaxAllocHeap());

  // Initialize camera — MUST happen before WiFi to get DMA memory
  if (!initCamera()) {
    Serial.println("[CAM] FATAL: Camera init failed!");
    Serial.print("[SYS] Free heap after fail: "); Serial.println(ESP.getFreeHeap());
    // Flash rapidly forever to signal hardware error
    while (true) {
      digitalWrite(FLASH_PIN, HIGH); delay(100);
      digitalWrite(FLASH_PIN, LOW);  delay(100);
    }
  }
  Serial.println("[CAM] Camera ready.");

  // Connect to WiFi and resolve server
  connectWiFi();

  Serial.println("[SYS] Starting capture loop...");
}

// =====================================================================
// MAIN LOOP
// =====================================================================
void loop() {
  // Reconnect WiFi if dropped
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[WiFi] Lost — reconnecting...");
    connectWiFi();
  }

  // Poll fill level every POLL_INTERVAL ms
  if (millis() - lastPollTime >= POLL_INTERVAL) {
    lastPollTime = millis();

    float currentFill = fetchFillLevel();

    if (currentFill < 0) {
      return;  // Fetch error — skip this cycle
    }

    float change = abs(currentFill - lastPhotoFillLevel);

    Serial.print("[FILL] ");
    Serial.print(currentFill, 1);
    Serial.print("% | last photo: ");
    Serial.print(lastPhotoFillLevel == -999.0 ? 0 : lastPhotoFillLevel, 1);
    Serial.print("% | delta: ");
    Serial.print(change, 1);
    Serial.println("%");

    if (change >= FILL_CHANGE_THRESHOLD) {
      Serial.println("[CAM] Change detected — capturing photo...");
      captureAndUpload(currentFill);
      lastPhotoFillLevel = currentFill;
    }
  }
  // No delay() — loop is millis() driven
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
    Serial.print("[WiFi] Signal: "); Serial.print(WiFi.RSSI()); Serial.println(" dBm");

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
// FUNCTION: GET current fill level from Django
// Returns fill level (0.0–100.0) or -1.0 on error
// =====================================================================
float fetchFillLevel() {
  HTTPClient http;
  String url = SERVER_URL + String(FILL_ENDPOINT) + "?bin_id=" + String(BIN_ID);
  http.begin(url);
  http.setTimeout(2000);

  int code = http.GET();
  if (code != 200) {
    Serial.print("[HTTP] Fill fetch failed — code: ");
    Serial.println(code);
    http.end();
    return -1.0;
  }

  String response = http.getString();
  http.end();

  DynamicJsonDocument doc(1024);
  DeserializationError err = deserializeJson(doc, response);
  if (err) {
    Serial.println("[JSON] Parse error: " + String(err.c_str()));
    return -1.0;
  }

  float fillLevel = -1.0;
  if (doc.is<JsonArray>() && doc.size() > 0) {
    fillLevel = doc[0]["fill_level"].as<float>();
  } else if (doc.containsKey("fill_level")) {
    fillLevel = doc["fill_level"].as<float>();
  } else if (doc.containsKey("results") && doc["results"].size() > 0) {
    fillLevel = doc["results"][0]["fill_level"].as<float>();
  } else {
    Serial.println("[JSON] fill_level not found in response.");
  }

  return fillLevel;
}

// =====================================================================
// FUNCTION: Capture photo + upload to Django
// =====================================================================
void captureAndUpload(float fillLevel) {
  // Brief flash for better image in low-light bin interior
  digitalWrite(FLASH_PIN, HIGH);
  delay(150);

  camera_fb_t* fb = esp_camera_fb_get();
  digitalWrite(FLASH_PIN, LOW);

  if (!fb) {
    Serial.println("[CAM] Capture failed — no frame buffer.");
    return;
  }

  photoCount++;
  Serial.printf("[CAM] Photo #%d | %dx%d | %d bytes | fill=%.1f%%\n",
                photoCount, fb->width, fb->height, fb->len, fillLevel);

  bool ok = uploadImage(fb->buf, fb->len, fillLevel);
  esp_camera_fb_return(fb);

  if (ok) {
    Serial.println("[HTTP] Upload OK.");
  } else {
    Serial.println("[HTTP] Upload FAILED.");
  }
}

// =====================================================================
// FUNCTION: POST JPEG image to Django /api/camera-images/
// Fill level is sent as HTTP header for dataset labeling
// =====================================================================
bool uploadImage(uint8_t* data, size_t len, float fillLevel) {
  HTTPClient http;
  String url = SERVER_URL + String(UPLOAD_ENDPOINT);
  http.begin(url);
  http.setTimeout(10000);  // 10s — image payloads are larger

  http.addHeader("Content-Type", "image/jpeg");
  http.addHeader("X-Camera-ID",  CAMERA_ID);
  http.addHeader("X-Bin-ID",     BIN_ID);

  // Tag every photo with the fill level at time of capture
  char fillStr[10];
  dtostrf(fillLevel, 1, 1, fillStr);
  http.addHeader("X-Fill-Level", String(fillStr));

  int code = http.POST(data, len);

  if (code == 200 || code == 201) {
    http.end();
    return true;
  }

  Serial.print("[HTTP] Upload code: "); Serial.println(code);
  if (code > 0) Serial.println("[HTTP] Response: " + http.getString());
  http.end();
  return false;
}

// =====================================================================
// FUNCTION: Initialize camera hardware
// =====================================================================
bool initCamera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer   = LEDC_TIMER_0;
  config.pin_d0       = Y2_GPIO_NUM;
  config.pin_d1       = Y3_GPIO_NUM;
  config.pin_d2       = Y4_GPIO_NUM;
  config.pin_d3       = Y5_GPIO_NUM;
  config.pin_d4       = Y6_GPIO_NUM;
  config.pin_d5       = Y7_GPIO_NUM;
  config.pin_d6       = Y8_GPIO_NUM;
  config.pin_d7       = Y9_GPIO_NUM;
  config.pin_xclk     = XCLK_GPIO_NUM;
  config.pin_pclk     = PCLK_GPIO_NUM;
  config.pin_vsync    = VSYNC_GPIO_NUM;
  config.pin_href     = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn     = PWDN_GPIO_NUM;
  config.pin_reset    = RESET_GPIO_NUM;
  // PSRAM detected → full JPEG quality
  // No PSRAM   → grayscale + tiny frame to fit in internal DMA RAM
  if (psramFound()) {
    config.xclk_freq_hz = 20000000;
    config.pixel_format = PIXFORMAT_JPEG;
    config.frame_size   = FRAMESIZE_SVGA;  // 800x600
    config.jpeg_quality = 10;
    config.fb_count     = 2;
  } else {
    // Minimal config — internal RAM only, no PSRAM
    config.xclk_freq_hz = 8000000;         // 8MHz — lowest stable XCLK
    config.pixel_format = PIXFORMAT_JPEG;   // JPEG = compressed output, less RAM
    config.frame_size   = FRAMESIZE_QQVGA;  // 160x120
    config.jpeg_quality = 63;               // Max compression = smallest buffer
    config.fb_count     = 1;
    config.fb_location  = CAMERA_FB_IN_DRAM; // Force internal RAM allocation
    config.grab_mode    = CAMERA_GRAB_LATEST;
  }

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("[CAM] Init error: 0x%x\n", err);
    return false;
  }

  // Fine-tune sensor for bin interior
  sensor_t* s = esp_camera_sensor_get();
  s->set_brightness(s,    1);  // Slightly brighter
  s->set_saturation(s,   -1);  // Less saturation — better for waste classification
  s->set_whitebal(s,      1);  // Auto white balance ON
  s->set_awb_gain(s,      1);  // AWB gain ON
  s->set_exposure_ctrl(s, 1);  // Auto exposure ON
  s->set_gain_ctrl(s,     1);  // Auto gain ON

  return true;
}
