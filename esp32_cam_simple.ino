/*
 * ESP32-CAM Simple Smart Waste Management System
 * 
 * Fixed version with memory optimization for camera initialization
 * 
 * Features:
 * - WiFi connectivity
 * - Image capture and upload
 * - HTTP POST to Django backend
 * - Simple error handling
 * - LED status indicators
 * 
 * Hardware: ESP32-CAM module (AI-Thinker or similar)
 * 
 * Author: Smart Waste Management System
 * Version: 1.2 (Memory Optimized)
 * Date: 2025
 */

#include "esp_camera.h"
#include <WiFi.h>
#include <HTTPClient.h>

// ============================================================================
// CONFIGURATION - UPDATE THESE VALUES
// ============================================================================

// WiFi Configuration
const char* ssid = "Orange-6B05";
const char* password = "GbYMLNLq7h4";

// Server Configuration
const char* server_url = "http://192.168.1.116:8000";  // ← Updated with correct Django server IP
const char* upload_endpoint = "/api/esp32-cam-upload/"; // ← Custom endpoint for ESP32-CAM
const char* camera_id = "ESP32_CAM_001";              // ← Unique camera identifier

// System Configuration
const int CAPTURE_INTERVAL = 30000;  // 30 seconds between captures
const int LED_PIN = 4;               // Built-in LED pin
const int FLASH_PIN = 2;             // Flash LED pin

// ============================================================================
// GLOBAL VARIABLES
// ============================================================================

bool wifiConnected = false;
int captureCount = 0;
unsigned long lastCaptureTime = 0;

// ============================================================================
// SETUP FUNCTION
// ============================================================================

void setup() {
  Serial.begin(115200);
  Serial.println("\n🚀 ESP32-CAM Smart Waste Management System Starting...");
  
  // Print memory info
  Serial.printf("📊 Free heap: %d bytes\n", ESP.getFreeHeap());
  Serial.printf("📊 PSRAM found: %s\n", psramFound() ? "Yes" : "No");
  if (psramFound()) {
    Serial.printf("📊 Free PSRAM: %d bytes\n", ESP.getFreePsram());
  }
  
  // Initialize LED pins
  pinMode(LED_PIN, OUTPUT);
  pinMode(FLASH_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  digitalWrite(FLASH_PIN, LOW);
  
  // Initialize camera
  if (!initCamera()) {
    Serial.println("❌ Camera initialization failed!");
    blinkLED(10, 100); // Error indicator
    return;
  }
  
  // Connect to WiFi
  connectToWiFi();
  
  // First capture after setup
  if (wifiConnected) {
    captureAndUpload();
  }
  
  Serial.println("✅ Setup completed successfully!");
}

// ============================================================================
// MAIN LOOP
// ============================================================================

void loop() {
  unsigned long currentTime = millis();
  
  // Check WiFi connection
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("⚠️ WiFi disconnected, attempting to reconnect...");
    connectToWiFi();
  }
  
  // Capture and upload at intervals
  if (wifiConnected && (currentTime - lastCaptureTime >= CAPTURE_INTERVAL)) {
    captureAndUpload();
    lastCaptureTime = currentTime;
  }
  
  // Small delay to prevent watchdog reset
  delay(1000);
}

// ============================================================================
// CAMERA INITIALIZATION (Memory Optimized)
// ============================================================================

bool initCamera() {
  Serial.println("📸 Initializing camera...");
  
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = 5;
  config.pin_d1 = 18;
  config.pin_d2 = 19;
  config.pin_d3 = 21;
  config.pin_d4 = 36;
  config.pin_d5 = 39;
  config.pin_d6 = 34;
  config.pin_d7 = 35;
  config.pin_xclk = 0;
  config.pin_pclk = 22;
  config.pin_vsync = 25;
  config.pin_href = 23;
  config.pin_sscb_sda = 26;
  config.pin_sscb_scl = 27;
  config.pin_pwdn = 32;
  config.pin_reset = -1;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
  
  // MEMORY-OPTIMIZED SETTINGS
  if(psramFound()) {
    Serial.println("📊 PSRAM detected - using higher quality settings");
    config.frame_size = FRAMESIZE_SVGA;     // 800x600 (reduced from UXGA)
    config.jpeg_quality = 10;               // High quality
    config.fb_count = 2;                    // Double buffering
    config.fb_location = CAMERA_FB_IN_PSRAM; // Use PSRAM
  } else {
    Serial.println("📊 No PSRAM - using conservative settings");
    config.frame_size = FRAMESIZE_VGA;      // 640x480 (smaller)
    config.jpeg_quality = 15;               // Medium quality
    config.fb_count = 1;                    // Single buffer
    config.fb_location = CAMERA_FB_IN_DRAM;  // Use internal RAM
  }
  
  // Print configuration
  Serial.printf("📊 Frame size: %d, Quality: %d, FB count: %d\n", 
                config.frame_size, config.jpeg_quality, config.fb_count);
  
  // Initialize camera
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("❌ Camera init failed with error 0x%x\n", err);
    
    // Try even more conservative settings
    Serial.println("🔄 Trying ultra-conservative settings...");
    config.frame_size = FRAMESIZE_QVGA;     // 320x240
    config.jpeg_quality = 20;               // Lower quality
    config.fb_count = 1;                    // Single buffer
    config.fb_location = CAMERA_FB_IN_DRAM;
    
    err = esp_camera_init(&config);
    if (err != ESP_OK) {
      Serial.printf("❌ Camera init still failed with error 0x%x\n", err);
      return false;
    }
  }
  
  // Get sensor handle for additional settings
  sensor_t * s = esp_camera_sensor_get();
  if (s) {
    // Additional optimizations
    s->set_brightness(s, 0);     // -2 to 2
    s->set_contrast(s, 0);       // -2 to 2
    s->set_saturation(s, 0);     // -2 to 2
    s->set_special_effect(s, 0); // 0 to 6 (0 - No Effect)
    s->set_whitebal(s, 1);       // 0 = disable , 1 = enable
    s->set_awb_gain(s, 1);       // 0 = disable , 1 = enable
    s->set_wb_mode(s, 0);        // 0 to 4 - if awb_gain enabled
    s->set_exposure_ctrl(s, 1);  // 0 = disable , 1 = enable
    s->set_aec2(s, 0);           // 0 = disable , 1 = enable
    s->set_ae_level(s, 0);       // -2 to 2
    s->set_aec_value(s, 300);    // 0 to 1200
    s->set_gain_ctrl(s, 1);      // 0 = disable , 1 = enable
    s->set_agc_gain(s, 0);       // 0 to 30
    s->set_gainceiling(s, (gainceiling_t)0);  // 0 to 6
    s->set_bpc(s, 0);            // 0 = disable , 1 = enable
    s->set_wpc(s, 1);            // 0 = disable , 1 = enable
    s->set_raw_gma(s, 1);        // 0 = disable , 1 = enable
    s->set_lenc(s, 1);           // 0 = disable , 1 = enable
    s->set_hmirror(s, 0);        // 0 = disable , 1 = enable
    s->set_vflip(s, 0);          // 0 = disable , 1 = enable
    s->set_dcw(s, 1);            // 0 = disable , 1 = enable
    s->set_colorbar(s, 0);       // 0 = disable , 1 = enable
  }
  
  Serial.println("✅ Camera initialized successfully!");
  Serial.printf("📊 Free heap after init: %d bytes\n", ESP.getFreeHeap());
  return true;
}

// ============================================================================
// WIFI CONNECTION
// ============================================================================

void connectToWiFi() {
  Serial.println("📶 Connecting to WiFi...");
  digitalWrite(LED_PIN, HIGH); // Turn on LED during connection
  
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    wifiConnected = true;
    digitalWrite(LED_PIN, LOW);
    Serial.println("\n✅ WiFi connected successfully!");
    Serial.print("📡 IP Address: ");
    Serial.println(WiFi.localIP());
    Serial.print("📡 Signal Strength: ");
    Serial.print(WiFi.RSSI());
    Serial.println(" dBm");
  } else {
    wifiConnected = false;
    digitalWrite(LED_PIN, HIGH);
    Serial.println("\n❌ WiFi connection failed!");
    blinkLED(5, 200); // Error indicator
  }
}

// ============================================================================
// IMAGE CAPTURE AND UPLOAD
// ============================================================================

void captureAndUpload() {
  if (!wifiConnected) {
    Serial.println("⚠️ WiFi not connected, skipping capture");
    return;
  }
  
  captureCount++;
  Serial.println("\n📸 Starting image capture #" + String(captureCount));
  Serial.printf("📊 Free heap before capture: %d bytes\n", ESP.getFreeHeap());
  
  // Turn on flash for better image quality
  digitalWrite(FLASH_PIN, HIGH);
  delay(100);
  
  // Capture image
  camera_fb_t * fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("❌ Camera capture failed");
    digitalWrite(FLASH_PIN, LOW);
    return;
  }
  
  // Turn off flash
  digitalWrite(FLASH_PIN, LOW);
  
  Serial.printf("📊 Image captured: %dx%d, %d bytes\n", 
                fb->width, fb->height, fb->len);
  Serial.printf("📊 Free heap after capture: %d bytes\n", ESP.getFreeHeap());
  
  // Upload image
  bool uploadSuccess = uploadImage(fb->buf, fb->len);
  
  // Release frame buffer
  esp_camera_fb_return(fb);
  Serial.printf("📊 Free heap after release: %d bytes\n", ESP.getFreeHeap());
  
  if (uploadSuccess) {
    Serial.println("✅ Image uploaded successfully!");
    blinkLED(3, 100); // Success indicator
  } else {
    Serial.println("❌ Image upload failed!");
    blinkLED(10, 50); // Error indicator
  }
}

// ============================================================================
// IMAGE UPLOAD TO SERVER
// ============================================================================

bool uploadImage(uint8_t* imageData, size_t imageSize) {
  HTTPClient http;
  String url = String(server_url) + String(upload_endpoint);
  
  Serial.println("📤 Uploading image to: " + url);
  
  http.begin(url);
  http.addHeader("X-Camera-ID", camera_id);
  http.addHeader("X-Camera-Type", "ESP32-CAM");
  http.addHeader("X-Analysis-Type", "WASTE_CLASSIFICATION");
  http.addHeader("Content-Type", "image/jpeg");
  http.addHeader("Content-Length", String(imageSize));
  http.setTimeout(30000); // 30 second timeout
  
  Serial.println("🔍 Sending raw binary image data, size: " + String(imageSize));
  
  int httpResponseCode = http.POST(imageData, imageSize);
  
  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.println("📡 HTTP Response Code: " + String(httpResponseCode));
    Serial.println("📡 Response: " + response.substring(0, 200));
    
    if (httpResponseCode == 201 || httpResponseCode == 200) {
      Serial.println("✅ Image uploaded successfully!");
      http.end();
      return true;
    } else {
      Serial.println("⚠️ Upload failed with code: " + String(httpResponseCode));
    }
  } else {
    Serial.println("❌ HTTP request failed: " + String(httpResponseCode));
  }
  
  http.end();
  return false;
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

void blinkLED(int times, int delayMs) {
  for (int i = 0; i < times; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(delayMs);
    digitalWrite(LED_PIN, LOW);
    delay(delayMs);
  }
}

// ============================================================================
// END OF CODE
// ============================================================================