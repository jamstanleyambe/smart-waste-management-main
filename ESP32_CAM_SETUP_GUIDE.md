# ESP32-CAM Setup Guide for Smart Waste Management

## 📋 Hardware Requirements

### ESP32-CAM Module
- **Model**: AI-Thinker ESP32-CAM
- **Camera**: OV2640 (2MP)
- **Flash**: 4MB (minimum)
- **PSRAM**: 8MB (recommended for better performance)

### Additional Components
- **MicroSD Card**: 8GB+ (optional, for local storage)
- **Power Supply**: 5V/2A (for stable operation)
- **USB-to-Serial Adapter**: For programming
- **Breadboard and Jumper Wires**: For connections

## 🔧 Hardware Connections

### Programming Mode (for initial setup)
```
ESP32-CAM    →    USB-Serial Adapter
GND          →    GND
5V           →    5V
U0R          →    TX
U0T          →    RX
GPIO0        →    GND (for programming mode)
```

### Normal Operation
```
ESP32-CAM    →    Power Supply
GND          →    GND
5V           →    5V
GPIO0        →    Leave floating (normal mode)
```

## 💻 Software Setup

### 1. Install Arduino IDE
- Download from: https://www.arduino.cc/en/software
- Install ESP32 board package:
  - Go to File → Preferences
  - Add to Additional Board Manager URLs:
    ```
    https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
    ```
  - Go to Tools → Board → Boards Manager
  - Search for "ESP32" and install "ESP32 by Espressif Systems"

### 2. Install Required Libraries
- **ArduinoJson**: Tools → Manage Libraries → Search "ArduinoJson" → Install
- **HTTPClient**: Already included with ESP32 package

### 3. Board Configuration
- **Board**: "ESP32 Wrover Module"
- **Upload Speed**: "115200"
- **CPU Frequency**: "240MHz (WiFi/BT)"
- **Flash Frequency**: "80MHz"
- **Flash Mode**: "QIO"
- **Flash Size**: "4MB (32Mb)"
- **Partition Scheme**: "Huge APP (3MB No OTA/1MB SPIFFS)"
- **PSRAM**: "Enabled" (if available)

## ⚙️ Configuration

### 1. Update WiFi Credentials
```cpp
const char* ssid = "YOUR_WIFI_NETWORK_NAME";        // ← Replace with your WiFi network name
const char* password = "YOUR_WIFI_PASSWORD";         // ← Replace with your WiFi password
```

### 2. Update Server Configuration
```cpp
const char* server_url = "http://192.168.1.100:8000";  // ← Replace with your Django server IP
const char* camera_id = "ESP32_CAM_001";              // ← Unique camera identifier
```

### 3. Adjust Capture Settings
```cpp
const int CAPTURE_INTERVAL = 30000;  // 30 seconds between captures (adjust as needed)
const int MAX_RETRIES = 3;           // Maximum retry attempts
```

## 📤 Upload Process

### 1. First Upload
1. Connect ESP32-CAM to USB-Serial adapter
2. Hold down the RESET button
3. Connect GPIO0 to GND
4. Release RESET button
5. Upload the code
6. Disconnect GPIO0 from GND
7. Press RESET button

### 2. Subsequent Uploads
- The ESP32-CAM will automatically enter programming mode when you upload
- No need to manually connect GPIO0 to GND

## 🔍 Troubleshooting

### Common Issues

#### 1. Upload Failed
- **Solution**: Check connections, ensure GPIO0 is connected to GND during upload
- **Alternative**: Try different USB-Serial adapter or cable

#### 2. Camera Initialization Failed
- **Solution**: Check camera module connections, ensure proper power supply
- **Check**: Verify camera model in code matches hardware

#### 3. WiFi Connection Failed
- **Solution**: Verify WiFi credentials, check signal strength
- **Check**: Ensure 2.4GHz network (ESP32 doesn't support 5GHz)

#### 4. Image Upload Failed
- **Solution**: Check server URL, ensure Django server is running
- **Check**: Verify network connectivity between ESP32 and server

### Debug Information
The code includes comprehensive serial output for debugging:
- WiFi connection status
- Camera initialization
- Image capture details
- Upload progress and errors

## 📊 Performance Optimization

### 1. Image Quality Settings
```cpp
// For high quality (requires PSRAM)
config.frame_size = FRAMESIZE_UXGA; // 1600x1200
config.jpeg_quality = 10;           // High quality

// For lower memory usage
config.frame_size = FRAMESIZE_SVGA; // 800x600
config.jpeg_quality = 12;           // Medium quality
```

### 2. Power Management
- Use deep sleep mode for battery operation
- Adjust capture intervals based on requirements
- Monitor power consumption

### 3. Network Optimization
- Use stable WiFi connection
- Consider WiFi signal strength
- Implement retry logic for failed uploads

## 🔒 Security Considerations

### 1. Network Security
- Use WPA2/WPA3 WiFi encryption
- Consider VPN for remote access
- Implement HTTPS for production

### 2. Device Security
- Change default camera IDs
- Implement authentication if needed
- Regular firmware updates

## 📱 Integration with Smart Waste System

### 1. Django Backend
- Preferred endpoint for ESP32-CAM is raw JPEG upload: `/api/esp32-cam-upload/`
- Headers to include:
  - `X-Camera-ID: <your_camera_id>`
  - `X-Camera-Type: ESP32-CAM`
  - `Content-Type: image/jpeg`
- Thumbnails are generated automatically (best-effort)
- Images are stored under `/media/camera_images/YYYY/MM/DD/`

### 2. Bulk Upload Support
- Multiple ESP32-CAMs can upload simultaneously
- Each camera should have a unique ID
- Images are organized by camera and timestamp

### 3. Analysis Integration
- Images are tagged with analysis type
- Ready for AI/ML processing
- Metadata includes camera information

## 🚀 Advanced Features

### 1. Motion Detection
- Add PIR sensor for motion-triggered captures
- Reduce power consumption
- Capture only when needed

### 2. Local Storage
- Save images to microSD card
- Upload when WiFi is available
- Backup for network failures

### 3. Remote Configuration
- OTA updates for firmware
- Remote parameter adjustment
- Status monitoring

## 📞 Support

For technical support or questions:
1. Check the serial monitor output
2. Verify hardware connections
3. Test with simple WiFi connection first
4. Ensure Django server is accessible
5. Test endpoint with cURL from a laptop:
```bash
curl -X POST http://<server>:8000/api/esp32-cam-upload/ \
  -H "Content-Type: image/jpeg" \
  -H "X-Camera-ID: ESP32_CAM_001" \
  --data-binary @image.jpg
```

## 🧩 Arduino Upload Snippet (Raw JPEG)
```cpp
// Assumes fb = esp_camera_fb_get(); already captured
WiFiClient client;
if (!client.connect(server_ip, 8000)) {
  Serial.println("Connection failed");
  return;
}

String path = "/api/esp32-cam-upload/";
String host = String(server_ip) + ":8000";
String cameraId = "ESP32_CAM_001";

client.print(String("POST ") + path + " HTTP/1.1\r\n");
client.print("Host: " + host + "\r\n");
client.print("User-Agent: esp32-cam\r\n");
client.print("X-Camera-ID: " + cameraId + "\r\n");
client.print("X-Camera-Type: ESP32-CAM\r\n");
client.print("Content-Type: image/jpeg\r\n");
client.print(String("Content-Length: ") + fb->len + "\r\n");
client.print("Connection: close\r\n\r\n");
client.write(fb->buf, fb->len);
client.flush();
esp_camera_fb_return(fb);

// Optional: read HTTP status
String statusLine = client.readStringUntil('\n');
Serial.println(statusLine);
```

## 🔄 Updates

Keep the ESP32-CAM firmware updated:
1. Monitor for new versions
2. Test updates in development environment
3. Backup working configurations
4. Document any changes

---

**Note**: This guide assumes basic familiarity with Arduino IDE and ESP32 development. For beginners, consider starting with simpler ESP32 projects before implementing the camera functionality.
