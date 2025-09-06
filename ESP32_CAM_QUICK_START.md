# ESP32-CAM Quick Start Guide

## 🚀 Quick Setup (5 Minutes)

### 1. **Update Configuration**
Open `esp32_cam_simple.ino` and update these lines:

```cpp
// WiFi Configuration
const char* ssid = "YOUR_WIFI_NETWORK_NAME";        // ← Replace with your WiFi
const char* password = "YOUR_WIFI_PASSWORD";         // ← Replace with your password

// Server Configuration  
const char* server_url = "http://192.168.1.100:8000";  // ← Replace with your Django server IP
const char* camera_id = "ESP32_CAM_001";              // ← Unique camera identifier
```

### 2. **Arduino IDE Setup**
- **Board**: "ESP32 Wrover Module"
- **Upload Speed**: "115200"
- **Flash Size**: "4MB (32Mb)"
- **PSRAM**: "Enabled" (if available)

### 3. **Upload Process**
1. Connect ESP32-CAM to USB-Serial adapter
2. Hold RESET button
3. Connect GPIO0 to GND
4. Release RESET button
5. Upload code
6. Disconnect GPIO0 from GND
7. Press RESET button

### 4. **Monitor Output**
Open Serial Monitor (115200 baud) to see:
- WiFi connection status
- Image capture progress
- Upload results

## 🔧 Hardware Connections

### Programming Mode
```
ESP32-CAM    →    USB-Serial Adapter
GND          →    GND
5V           →    5V
U0R          →    TX
U0T          →    RX
GPIO0        →    GND (for programming)
```

### Normal Operation
```
ESP32-CAM    →    Power Supply
GND          →    GND
5V           →    5V
GPIO0        →    Leave floating
```

## 📱 What Happens Next

1. **ESP32-CAM connects to WiFi**
2. **Captures image every 30 seconds**
3. **Uploads to Django backend**
4. **Images appear in Streamlit gallery**
5. **Thumbnails generated automatically**

## 🐛 Troubleshooting

### Upload Failed
- Check connections
- Ensure GPIO0 connected to GND during upload
- Try different USB-Serial adapter

### WiFi Connection Failed
- Verify WiFi credentials
- Check 2.4GHz network (not 5GHz)
- Check signal strength

### Image Upload Failed
- Check server URL
- Ensure Django server is running
- Check network connectivity

## 📊 Expected Output

```
🚀 ESP32-CAM Smart Waste Management System Starting...
📸 Initializing camera...
✅ Camera initialized successfully!
📶 Connecting to WiFi...
✅ WiFi connected successfully!
📡 IP Address: 192.168.1.150
📡 Signal Strength: -45 dBm
✅ Setup completed successfully!

📸 Starting image capture #1
📊 Image captured: 1600x1200, 45678 bytes
📤 Uploading image to: http://192.168.1.100:8000/api/camera-images/
📡 HTTP Response Code: 201
✅ Image uploaded successfully!
```

## 🎯 Integration

- **Images automatically appear in Streamlit dashboard**
- **Thumbnails generated for gallery view**
- **Multiple cameras supported with unique IDs**
- **Bulk upload compatible**

---

**Ready to go!** Your ESP32-CAM will start capturing and uploading images to your smart waste management system. 🎉
