# ESP32 Sensor Deployment Guide

## 🚀 Quick Setup Instructions

### 1. **Update Configuration**

For each sensor, update these values in the Arduino code:

```cpp
// WiFi Configuration
const char* ssid = "YOUR_WIFI_SSID";           // ← Your WiFi name
const char* password = "YOUR_WIFI_PASSWORD";   // ← Your WiFi password

// Server Configuration
const char* server_url = "http://172.20.10.6:8000";  // ← Your Django server IP

// Sensor Configuration
String sensorId = "ESP32_SENSOR_001";         // ← Unique ID for each sensor
String binId = "BIN001";                      // ← Bin ID this sensor monitors
float binLatitude = 4.0725;                   // ← Actual bin coordinates
float binLongitude = 9.7634;                  // ← Actual bin coordinates
```

### 2. **Hardware Connections**

```
ESP32 Pin    →    HC-SR04 Pin
GPIO 5       →    TRIG
GPIO 18      →    ECHO
3.3V         →    VCC
GND          →    GND
```

### 3. **Sensor ID Mapping**

Create unique sensor IDs for each bin:

| Bin ID  | Sensor ID        | Location |
|---------|------------------|----------|
| BIN001  | ESP32_SENSOR_001 | Update coordinates |
| BIN002  | ESP32_SENSOR_002 | Update coordinates |
| BIN003  | ESP32_SENSOR_003 | Update coordinates |
| ...     | ...              | ...      |

### 4. **Upload Process**

1. Open Arduino IDE
2. Install required libraries:
   - WiFi (built-in)
   - HTTPClient (built-in)
   - ArduinoJson (install from Library Manager)
3. Select ESP32 board
4. Update configuration values
5. Upload to ESP32

### 5. **Testing**

After upload, check Serial Monitor for:
- ✅ WiFi connection
- ✅ IP address assignment
- ✅ Sensor data transmission
- ✅ Server response

### 6. **Troubleshooting**

**WiFi Issues:**
- Check SSID and password
- Ensure WiFi is 2.4GHz (ESP32 doesn't support 5GHz)
- Check signal strength

**Server Connection Issues:**
- Verify Django server is running
- Check IP address is correct
- Ensure firewall allows connections

**Sensor Reading Issues:**
- Check ultrasonic sensor connections
- Verify sensor is not too close/far from bin contents
- Test with Serial Monitor output

### 7. **Expected Behavior**

- LED blinks 3 times on startup
- Data sent every 30 seconds
- LED blinks once on successful transmission
- LED blinks twice on transmission error
- Serial output shows fill level readings

### 8. **Data Format**

The sensor sends JSON data in this format:

```json
{
  "sensor_id": "ESP32_SENSOR_001",
  "bin_id": "BIN001",
  "fill_level": 75.5,
  "latitude": 4.0725,
  "longitude": 9.7634,
  "organic_percentage": 42.3,
  "plastic_percentage": 35.7,
  "metal_percentage": 22.0,
  "sensor_status": "ONLINE",
  "battery_level": 95.0,
  "signal_strength": -45,
  "temperature": 25.5,
  "humidity": 55.0
}
```

### 9. **Power Management**

- Use 3.7V Li-ion battery for portable operation
- Add voltage divider for battery monitoring
- Consider deep sleep mode for battery optimization

### 10. **Deployment Checklist**

- [ ] WiFi credentials updated
- [ ] Server IP address correct
- [ ] Unique sensor ID assigned
- [ ] Bin ID matches database
- [ ] Coordinates updated
- [ ] Hardware connections verified
- [ ] Code uploaded successfully
- [ ] Serial monitor shows successful connection
- [ ] Data appears in Django admin panel

## 🎯 Success Indicators

When everything is working correctly, you should see:

1. **Serial Monitor:**
   ```
   🚀 ESP32 Smart Waste Sensor Starting...
   📡 Connecting to WiFi...
   ✅ WiFi connected!
   📡 IP: 192.168.1.100
   ✅ Setup completed!
   📏 Fill Level: 75.5%
   📤 Sending sensor data...
   ✅ Success! Response: 201
   ```

2. **Django Admin Panel:**
   - New sensor data entries appear
   - Bin fill levels update in real-time
   - Sensor status shows "ONLINE"

3. **Frontend Dashboard:**
   - Bin markers update with new fill levels
   - Real-time data visualization
   - Sensor status indicators

## 🔧 Advanced Configuration

### Custom Send Intervals
```cpp
const unsigned long SEND_INTERVAL = 10000; // Send every 10 seconds
```

### Custom Fill Level Calculation
```cpp
// Adjust these values based on your bin dimensions
const int MAX_DISTANCE = 200;  // Empty bin distance
const int MIN_DISTANCE = 5;    // Full bin distance
```

### Error Handling
The code includes automatic retry logic:
- 3 retry attempts on failure
- 5-second delay between retries
- Longer delay after max retries reached
