/*
 * =====================================================================
 * SMART WASTE MANAGEMENT SYSTEM
 * Module: ESP32-CAM — Waste Dataset Capture
 * Board:  AI Thinker ESP32-CAM
 *
 * ── TRANSPORT PRIORITY ──────────────────────────────────────────────
 * On startup the firmware waits 4 seconds for the Mac's
 * serial_bridge.py to send "BRIDGE_READY".
 *
 * USB MODE (bridge running):
 *   - Fill level is read from Serial JSON sent by serial_bridge.py
 *     (which already got it from the ultrasonic sensor bridge).
 *   - OR the CAM polls Django via WiFi for fill level but uploads
 *     images over WiFi (JPEG binary cannot go over serial text).
 *   - The "USB mode" here means fill-level data flows over USB;
 *     image uploads still use WiFi because JPEG is binary.
 *
 * WIFI MODE (no bridge, fallback):
 *   - Polls Django GET /api/bin-data/ for fill level via WiFi.
 *   - Uploads images via WiFi POST /api/esp32-cam-upload/.
 *
 * ── NOTE ON ESP32-CAM USB ────────────────────────────────────────────
 * The AI Thinker ESP32-CAM does NOT have a native USB-Serial chip
 * on the camera module itself — it uses an external FTDI/CH340 adapter.
 * Because of this, GPIO0 must be connected to GND to flash, then
 * disconnected to run.  Serial is available for debug output.
 *
 * ── ENDPOINTS USED ───────────────────────────────────────────────────
 *   GET  /api/bin-data/?bin_id=BIN001  → get current fill level
 *   POST /api/esp32-cam-upload/        → upload photo + metadata
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
const char* WIFI_SSID       = "Orange-6B05";
const char* WIFI_PASSWORD   = "GbYMLNLq7h4";
const char* MAC_HOSTNAME    = "Jams-MacBook-Pro.local";
const char* FILL_ENDPOINT   = "/api/bin-data/";
const char* UPLOAD_ENDPOINT = "/api/esp32-cam-upload/";
String      SERVER_URL      = "";  // Resolved from hostname at runtime

// =====================================================================
// SECTION 2: BIN IDENTITY
// =====================================================================
const char* CAMERA_ID = "ESP32_CAM_001";
const char* BIN_ID    = "BIN001";

// =====================================================================
// SECTION 3: CAPTURE SETTINGS
// =====================================================================
const float          FILL_CHANGE_THRESHOLD = 1.0;   // Photo if fill changes >= 1%
const unsigned long  POLL_INTERVAL         = 500;   // Poll for fill level every 500ms
const unsigned long  USB_WAIT_MS           = 4000;  // Wait for bridge handshake

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
// GLOBAL STATE
// =====================================================================
bool          USB_MODE           = false;   // true = fill level arrives via Serial
float         lastPhotoFillLevel = -999.0;  // -999 forces first photo on boot
unsigned long lastPollTime       = 0;
int           photoCount         = 0;

// USB-mode: fill level sent by bridge via Serial JSON
float usbFillLevel = -1.0;

// =====================================================================
// FORWARD DECLARATIONS
// =====================================================================
void  connectWiFi();
float fetchFillLevelWiFi();
float fetchFillLevelUSB();
void  captureAndUpload(float fillLevel);
bool  uploadImage(uint8_t* data, size_t len, float fillLevel);
bool  initCamera();

// =====================================================================
// SETUP
// =====================================================================
void setup() {
  Serial.begin(115200);
  delay(1000);

  pinMode(FLASH_PIN, OUTPUT);
  digitalWrite(FLASH_PIN, LOW);

  Serial.println(F("===================================="));
  Serial.println(F("  Smart Waste — ESP32-CAM Dataset  "));
  Serial.println(F("  >>> CODE VERSION 3.0 <<<          "));
  Serial.println(F("===================================="));
  Serial.print(F("[SYS] PSRAM: "));
  Serial.println(psramFound() ? "FOUND" : "NOT FOUND");
  Serial.print(F("Camera ID : ")); Serial.println(CAMERA_ID);
  Serial.print(F("Bin ID    : ")); Serial.println(BIN_ID);

  // Initialize camera FIRST — must happen before WiFi to get DMA memory
  if (!initCamera()) {
    Serial.println(F("[CAM] FATAL: Camera init failed!"));
    while (true) {
      digitalWrite(FLASH_PIN, HIGH); delay(100);
      digitalWrite(FLASH_PIN, LOW);  delay(100);
    }
  }
  Serial.println(F("[CAM] Camera ready."));

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
    Serial.println(F("[USB] ✅ Bridge detected! Running in USB+WiFi hybrid mode."));
    Serial.println(F("[USB] Fill level → USB Serial | Images → WiFi"));
    // Connect WiFi too — needed for image uploads even in USB mode
    connectWiFi();
  } else {
    Serial.println(F("[WiFi] No bridge found — falling back to full WiFi mode."));
    connectWiFi();
  }

  Serial.println(F("[SYS] Starting capture loop..."));
}

// =====================================================================
// MAIN LOOP
// =====================================================================
void loop() {
  // Reconnect WiFi if dropped (needed for image uploads in both modes)
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println(F("[WiFi] Lost — reconnecting..."));
    connectWiFi();
  }

  // Poll fill level every POLL_INTERVAL ms
  if (millis() - lastPollTime >= POLL_INTERVAL) {
    lastPollTime = millis();

    float currentFill;

    if (USB_MODE) {
      // In USB mode: read fill level sent by the bridge over Serial
      // The bridge forwards JSON lines that start with '{'
      currentFill = fetchFillLevelUSB();
      if (currentFill < 0) {
        // Bridge hasn't sent data yet — fall back to WiFi fetch
        currentFill = fetchFillLevelWiFi();
      }
    } else {
      currentFill = fetchFillLevelWiFi();
    }

    if (currentFill < 0) {
      return;  // Fetch error — skip this cycle
    }

    float change = abs(currentFill - lastPhotoFillLevel);

    Serial.print(F("[FILL] "));
    Serial.print(currentFill, 1);
    Serial.print(F("% | last photo: "));
    Serial.print(lastPhotoFillLevel == -999.0 ? 0 : lastPhotoFillLevel, 1);
    Serial.print(F("% | delta: "));
    Serial.print(change, 1);
    Serial.println(F("%"));

    if (change >= FILL_CHANGE_THRESHOLD) {
      Serial.println(F("[CAM] Change detected — capturing photo..."));
      captureAndUpload(currentFill);
      lastPhotoFillLevel = currentFill;
    }
  }
}

// =====================================================================
// FUNCTION: Get fill level from Serial (USB bridge mode)
// Reads any JSON line printed by the ultrasonic sensor bridge
// =====================================================================
float fetchFillLevelUSB() {
  while (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();
    if (!line.startsWith("{")) continue;

    DynamicJsonDocument doc(512);
    DeserializationError err = deserializeJson(doc, line);
    if (err) continue;

    if (doc.containsKey("fill_level")) {
      float fl = doc["fill_level"].as<float>();
      Serial.print(F("[USB] Fill from bridge: ")); Serial.print(fl, 1); Serial.println(F("%"));
      return fl;
    }
  }
  return -1.0;  // nothing available yet
}

// =====================================================================
// FUNCTION: GET fill level from Django via WiFi
// =====================================================================
float fetchFillLevelWiFi() {
  WiFiClient client;
  HTTPClient http;
  String url = SERVER_URL + String(FILL_ENDPOINT) + "?bin_id=" + String(BIN_ID);

  Serial.print(F("[HTTP] Fetching fill: ")); Serial.println(url);

  http.begin(client, url);
  http.setFollowRedirects(HTTPC_STRICT_FOLLOW_REDIRECTS);
  http.setTimeout(3000);

  int code = http.GET();
  if (code != 200) {
    Serial.print(F("[HTTP] Fill fetch failed — code: ")); Serial.println(code);
    if (code > 0) Serial.println("[HTTP] Response: " + http.getString());
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
  }

  return fillLevel;
}

// =====================================================================
// FUNCTION: Capture photo + upload to Django
// =====================================================================
void captureAndUpload(float fillLevel) {
  digitalWrite(FLASH_PIN, HIGH);
  delay(150);

  camera_fb_t* fb = esp_camera_fb_get();
  digitalWrite(FLASH_PIN, LOW);

  if (!fb) {
    Serial.println(F("[CAM] Capture failed — no frame buffer."));
    return;
  }

  photoCount++;
  Serial.printf("[CAM] Photo #%d | %dx%d | %d bytes | fill=%.1f%%\n",
                photoCount, fb->width, fb->height, fb->len, fillLevel);

  bool ok = uploadImage(fb->buf, fb->len, fillLevel);
  esp_camera_fb_return(fb);

  Serial.println(ok ? F("[HTTP] Upload OK.") : F("[HTTP] Upload FAILED."));
}

// =====================================================================
// FUNCTION: POST JPEG image to Django
// =====================================================================
bool uploadImage(uint8_t* data, size_t len, float fillLevel) {
  WiFiClient client;
  HTTPClient http;
  String url = SERVER_URL + String(UPLOAD_ENDPOINT);

  Serial.print(F("[HTTP] Uploading to: ")); Serial.println(url);

  http.begin(client, url);
  http.setFollowRedirects(HTTPC_STRICT_FOLLOW_REDIRECTS);
  http.setTimeout(10000);

  http.addHeader("Content-Type", "image/jpeg");
  http.addHeader("X-Camera-ID",  CAMERA_ID);
  http.addHeader("X-Bin-ID",     BIN_ID);

  char fillStr[10];
  dtostrf(fillLevel, 1, 1, fillStr);
  http.addHeader("X-Fill-Level", String(fillStr));

  Serial.println(F("[HTTP] Executing POST..."));
  int code = http.POST(data, len);

  if (code == 200 || code == 201) {
    http.end();
    return true;
  }

  Serial.print(F("[HTTP] Upload code: ")); Serial.println(code);
  if (code > 0) Serial.println("[HTTP] Response: " + http.getString());
  http.end();
  return false;
}

// =====================================================================
// FUNCTION: Connect to WiFi + resolve Mac via mDNS
// =====================================================================
void connectWiFi() {
  Serial.print(F("[WiFi] Connecting to ")); Serial.print(WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 40) {
    delay(500); Serial.print("."); attempts++;
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

  if (psramFound()) {
    config.xclk_freq_hz = 20000000;
    config.pixel_format = PIXFORMAT_JPEG;
    config.frame_size   = FRAMESIZE_SVGA;  // 800x600
    config.jpeg_quality = 10;
    config.fb_count     = 2;
  } else {
    config.xclk_freq_hz = 8000000;
    config.pixel_format = PIXFORMAT_JPEG;
    config.frame_size   = FRAMESIZE_QQVGA;  // 160x120
    config.jpeg_quality = 63;
    config.fb_count     = 1;
    config.fb_location  = CAMERA_FB_IN_DRAM;
    config.grab_mode    = CAMERA_GRAB_LATEST;
  }

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("[CAM] Init error: 0x%x\n", err);
    return false;
  }

  // Fine-tune sensor for bin interior
  sensor_t* s = esp_camera_sensor_get();
  s->set_brightness(s,    1);
  s->set_saturation(s,   -1);
  s->set_whitebal(s,      1);
  s->set_awb_gain(s,      1);
  s->set_exposure_ctrl(s, 1);
  s->set_gain_ctrl(s,     1);

  return true;
}
