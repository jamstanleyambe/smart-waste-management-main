/*
📸 ESP32-CAM Smart Waste Management System
🎯 Function: Capture images and send to Django backend
🌐 Branch: test-v3-cam
*/

#include "esp_camera.h"
#include "esp_timer.h"
#include "img_converters.h"
#include "Arduino.h"
#include "fb_gfx.h"
#include "soc/soc.h"
#include "soc/rtc_cntl_reg.h"
#include "esp_http_server.h"
#include "WiFi.h"
#include "HTTPClient.h"
#include "ArduinoJson.h"

// ESP32-CAM Pin Configuration
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    22
#define XCLK_GPIO_NUM     0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM       5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     17

// WiFi Configuration
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// Server Configuration
const char* serverUrl = "http://192.168.1.116:8000";
const char* imageEndpoint = "/api/camera/upload/";

// Camera Settings
int captureInterval = 30000;  // 30 seconds
int imageQuality = 10;        // JPEG quality
int frameSize = FRAMESIZE_VGA; // 640x480

// Status variables
bool wifiConnected = false;
unsigned long lastCaptureTime = 0;
int imageCounter = 0;

void setup() {
  Serial.begin(115200);
  Serial.println("📸 ESP32-CAM Starting...");
  
  // Initialize camera
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.frame_size = frameSize;
  config.pixel_format = PIXFORMAT_JPEG;
  config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
  config.fb_location = CAMERA_FB_IN_PSRAM;
  config.jpeg_quality = imageQuality;
  config.fb_count = 2;
  
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("❌ Camera init failed: 0x%x", err);
    return;
  }
  Serial.println("✅ Camera initialized");
  
  connectToWiFi();
  lastCaptureTime = millis();
  Serial.println("🚀 ESP32-CAM ready!");
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("❌ WiFi disconnected, reconnecting...");
    connectToWiFi();
  }
  
  if (millis() - lastCaptureTime >= captureInterval) {
    captureAndSendImage();
    lastCaptureTime = millis();
  }
  
  delay(1000);
}

void connectToWiFi() {
  Serial.print("🔌 Connecting to WiFi: ");
  Serial.println(ssid);
  
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    wifiConnected = true;
    Serial.println();
    Serial.println("✅ WiFi connected!");
    Serial.print("📡 IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println();
    Serial.println("❌ WiFi failed!");
    wifiConnected = false;
  }
}

void captureAndSendImage() {
  if (!wifiConnected) {
    Serial.println("❌ WiFi not connected");
    return;
  }
  
  Serial.println("📸 Capturing image...");
  
  camera_fb_t * fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("❌ Camera capture failed");
    return;
  }
  
  Serial.printf("✅ Image: %dx%d %db\n", fb->width, fb->height, fb->len);
  
  if (sendImageToServer(fb)) {
    Serial.println("✅ Image sent successfully");
    imageCounter++;
  } else {
    Serial.println("❌ Failed to send image");
  }
  
  esp_camera_fb_return(fb);
}

bool sendImageToServer(camera_fb_t * fb) {
  HTTPClient http;
  String url = String(serverUrl) + String(imageEndpoint);
  
  Serial.print("🌐 Sending to: ");
  Serial.println(url);
  
  http.begin(url);
  http.addHeader("Content-Type", "image/jpeg");
  http.addHeader("X-Camera-ID", "ESP32_CAM_001");
  http.addHeader("X-Capture-Time", String(millis()));
  
  int httpResponseCode = http.POST(fb->buf, fb->len);
  
  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.printf("✅ HTTP: %d\n", httpResponseCode);
    Serial.printf("📨 Response: %s\n", response.c_str());
    http.end();
    return true;
  } else {
    Serial.printf("❌ HTTP Error: %d\n", httpResponseCode);
    http.end();
    return false;
  }
}
