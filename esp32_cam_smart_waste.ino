/*
 * ESP32-CAM Smart Waste Management System
 * 
 * This code captures images from the ESP32-CAM and sends them to the
 * Smart Waste Management Django backend for analysis and storage.
 * 
 * Features:
 * - WiFi connectivity
 * - Image capture and compression
 * - HTTP POST to Django backend
 * - Automatic retry on failure
 * - Deep sleep mode for power saving
 * - LED status indicators
 * 
 * Hardware: ESP32-CAM module
 * 
 * Author: Smart Waste Management System
 * Version: 1.0
 * Date: 2025
 */

#include "esp_camera.h"
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include "esp_sleep.h"
#include "esp_wifi.h"

// ============================================================================
// CONFIGURATION - UPDATE THESE VALUES
// ============================================================================

// WiFi Configuration
const char* ssid = "YOUR_WIFI_NETWORK_NAME";        // ← Replace with your WiFi network name
const char* password = "YOUR_WIFI_PASSWORD";         // ← Replace with your WiFi password

// Server Configuration
const char* server_url = "http://192.168.1.116:8000";  // ← Updated with correct Django server IP
const char* upload_endpoint = "/api/camera-images/";
const char* camera_id = "ESP32_CAM_001";              // ← Unique camera identifier

// Camera Configuration
#define CAMERA_MODEL_AI_THINKER
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define Y1_GPIO_NUM        4
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

// System Configuration
const int CAPTURE_INTERVAL = 30000;  // 30 seconds between captures
const int MAX_RETRIES = 3;           // Maximum retry attempts
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
// CAMERA INITIALIZATION
// ============================================================================

bool initCamera() {
  Serial.println("📸 Initializing camera...");
  
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
  config.pixel_format = PIXFORMAT_JPEG;
  
  // Frame size and quality settings
  if(psramFound()){
    config.frame_size = FRAMESIZE_UXGA; // 1600x1200
    config.jpeg_quality = 10;           // High quality
    config.fb_count = 2;
  } else {
    config.frame_size = FRAMESIZE_SVGA; // 800x600
    config.jpeg_quality = 12;           // Medium quality
    config.fb_count = 1;
  }
  
  // Initialize camera
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("❌ Camera init failed with error 0x%x\n", err);
    return false;
  }
  
  // Get camera sensor and adjust settings
  sensor_t * s = esp_camera_sensor_get();
  if (s->id.PID == OV3660_PID) {
    s->set_vflip(s, 1);        // Flip it back
    s->set_brightness(s, 1);   // Increase brightness
    s->set_saturation(s, -2);  // Decrease saturation
    s->set_special_effect(s, 0); // No effect
    s->set_whitebal(s, 1);     // Enable white balance
    s->set_awb_gain(s, 1);     // Enable AWB gain
    s->set_wb_mode(s, 0);      // Auto white balance
    s->set_exposure_ctrl(s, 1); // Enable exposure control
    s->set_aec2(s, 0);         // Disable AEC2
    s->set_ae_level(s, 0);     // Auto exposure level
    s->set_aec_value(s, 300);  // AEC value
    s->set_gain_ctrl(s, 1);    // Enable gain control
    s->set_agc_gain(s, 0);     // AGC gain
    s->set_gainceiling(s, (gainceiling_t)0); // Gain ceiling
    s->set_bpc(s, 0);          // Disable black pixel correction
    s->set_wpc(s, 1);          // Enable white pixel correction
    s->set_raw_gma(s, 1);      // Enable raw gamma
    s->set_lenc(s, 1);         // Enable lens correction
    s->set_hmirror(s, 0);      // Disable horizontal mirror
    s->set_vflip(s, 0);        // Disable vertical flip
    s->set_dcw(s, 1);          // Enable DCW
    s->set_colorbar(s, 0);     // Disable color bar
  }
  
  Serial.println("✅ Camera initialized successfully!");
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
  
  // Upload image
  bool uploadSuccess = uploadImage(fb->buf, fb->len);
  
  // Release frame buffer
  esp_camera_fb_return(fb);
  
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
  http.addHeader("Content-Type", "image/jpeg");
  http.addHeader("X-Camera-ID", camera_id);
  http.addHeader("X-Camera-Type", "ESP32-CAM");
  http.addHeader("X-Analysis-Type", "WASTE_DETECTION");
  
  // Add metadata
  String metadata = "{\"camera_name\":\"" + String(camera_id) + "\",\"analysis_type\":\"WASTE_DETECTION\"}";
  http.addHeader("X-Metadata", metadata);
  
  int retries = 0;
  int httpResponseCode = 0;
  
  while (retries < MAX_RETRIES) {
    Serial.println("🔄 Upload attempt " + String(retries + 1) + "/" + String(MAX_RETRIES));
    
    httpResponseCode = http.POST(imageData, imageSize);
    
    if (httpResponseCode > 0) {
      String response = http.getString();
      Serial.println("📡 HTTP Response Code: " + String(httpResponseCode));
      Serial.println("📡 Response: " + response);
      
      if (httpResponseCode == 201) {
        Serial.println("✅ Image uploaded successfully!");
        http.end();
        return true;
      } else if (httpResponseCode == 400) {
        Serial.println("⚠️ Bad request - check server configuration");
        break; // Don't retry on bad request
      } else {
        Serial.println("⚠️ Upload failed with code: " + String(httpResponseCode));
      }
    } else {
      Serial.println("❌ HTTP request failed: " + String(httpResponseCode));
    }
    
    retries++;
    if (retries < MAX_RETRIES) {
      Serial.println("⏳ Waiting 5 seconds before retry...");
      delay(5000);
    }
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

void printSystemInfo() {
  Serial.println("\n📊 System Information:");
  Serial.println("======================");
  Serial.println("Chip Model: " + String(ESP.getChipModel()));
  Serial.println("Chip Revision: " + String(ESP.getChipRevision()));
  Serial.println("CPU Frequency: " + String(ESP.getCpuFreqMHz()) + " MHz");
  Serial.println("Flash Size: " + String(ESP.getFlashChipSize() / 1024 / 1024) + " MB");
  Serial.println("Free Heap: " + String(ESP.getFreeHeap()) + " bytes");
  Serial.println("PSRAM: " + String(psramFound() ? "Available" : "Not Available"));
  Serial.println("======================\n");
}

// ============================================================================
// DEEP SLEEP FUNCTION (Optional - for power saving)
// ============================================================================

void enterDeepSleep(int sleepTimeSeconds) {
  Serial.println("😴 Entering deep sleep for " + String(sleepTimeSeconds) + " seconds...");
  
  // Disconnect WiFi to save power
  WiFi.disconnect(true);
  WiFi.mode(WIFI_OFF);
  
  // Configure wake up source
  esp_sleep_enable_timer_wakeup(sleepTimeSeconds * 1000000ULL);
  
  // Enter deep sleep
  esp_deep_sleep_start();
}

// ============================================================================
// ERROR HANDLING
// ============================================================================

void handleError(String errorMessage) {
  Serial.println("❌ ERROR: " + errorMessage);
  blinkLED(20, 100); // Long error indicator
  
  // Optional: Enter deep sleep on critical error
  // enterDeepSleep(300); // Sleep for 5 minutes
}

// ============================================================================
// END OF CODE
// ============================================================================
