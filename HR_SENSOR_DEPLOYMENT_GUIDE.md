# ESP32 HR (Ultrasonic) Sensor Deployment Guide

## 🎯 Complete Setup Instructions

### **📋 Hardware Requirements**

- **ESP32 Development Board** (ESP32-WROOM-32 or similar)
- **HC-SR04 Ultrasonic Sensor**
- **Jumper Wires**
- **Breadboard** (optional)
- **Power Supply** (USB cable or battery)

### **🔌 Hardware Connections**

```
ESP32 Pin    →    HC-SR04 Pin    →    Description
GPIO 5       →    TRIG           →    Trigger pin
GPIO 18      →    ECHO           →    Echo pin
3.3V         →    VCC            →    Power supply
GND          →    GND            →    Ground
```

**⚠️ Important:** HC-SR04 operates at 5V, but ESP32 GPIO pins are 3.3V. Use a voltage divider for the ECHO pin if needed.

### **📱 Software Setup**

#### **1. Install Arduino IDE**
- Download from [arduino.cc](https://www.arduino.cc/en/software)
- Install ESP32 board support package

#### **2. Install Required Libraries**
Open Arduino IDE → Tools → Manage Libraries → Install:
- **ArduinoJson** (by Benoit Blanchon)
- **WiFi** (built-in)
- **HTTPClient** (built-in)

#### **3. Configure ESP32 Board**
- Tools → Board → ESP32 Arduino → ESP32 Dev Module
- Tools → Port → Select your ESP32 port
- Tools → Upload Speed → 115200

### **⚙️ Configuration**

#### **Update Configuration Values**

In the Arduino code, update these values:

```cpp
// WiFi Configuration
const char* ssid = "YOUR_WIFI_SSID";           // ← Your WiFi name
const char* password = "YOUR_WIFI_PASSWORD";   // ← Your WiFi password

// Server Configuration
const char* server_url = "http://172.20.10.6:8000";  // ← Your Django server IP

// Sensor Configuration
String sensorId = "ESP32_HR_SENSOR_001";     // ← Unique ID for each sensor
String binId = "BIN001";                      // ← Bin ID this sensor monitors
float binLatitude = 4.0725;                   // ← Actual bin latitude
float binLongitude = 9.7634;                  // ← Actual bin longitude
```

#### **Sensor ID Mapping**

Create unique sensor IDs for each bin:

| Bin ID  | Sensor ID              | Location |
|---------|------------------------|----------|
| BIN001  | ESP32_HR_SENSOR_001    | Update coordinates |
| BIN002  | ESP32_HR_SENSOR_002    | Update coordinates |
| BIN003  | ESP32_HR_SENSOR_003    | Update coordinates |
| BIN004  | ESP32_HR_SENSOR_004    | Update coordinates |
| ...     | ...                    | ...      |

### **🚀 Deployment Process**

#### **Step 1: Upload Code**
1. Open Arduino IDE
2. Load the sensor code
3. Update configuration values
4. Click Upload button
5. Wait for "Done uploading" message

#### **Step 2: Test Connection**
1. Open Serial Monitor (Tools → Serial Monitor)
2. Set baud rate to 115200
3. Reset ESP32 (press reset button)
4. Watch for startup messages

#### **Step 3: Verify Data Transmission**
Check Serial Monitor for:
```
🚀 ESP32 HR Sensor Starting...
📋 Configuration:
   Sensor ID: ESP32_HR_SENSOR_001
   Bin ID: BIN001
   Server: http://172.20.10.6:8000
📡 Connecting to WiFi: YOUR_WIFI_SSID
✅ WiFi connected successfully!
📡 IP Address: 192.168.1.100
📡 Signal Strength: -45 dBm
✅ Setup completed!
🔄 Starting main loop...
📏 Reading fill level...
📏 Distance: 25.5 cm, Fill Level: 87.5%
📤 Sending sensor data...
📊 Data to send:
{"sensor_id":"ESP32_HR_SENSOR_001","bin_id":"BIN001","fill_level":87.5,...}
🌐 Sending to: http://172.20.10.6:8000/api/sensor-data/
✅ Success! Response Code: 201
```

### **🔧 Calibration**

#### **Distance Calibration**
Adjust these values based on your bin dimensions:

```cpp
const int MAX_DISTANCE = 200;  // Empty bin distance (cm)
const int MIN_DISTANCE = 5;    // Full bin distance (cm)
```

#### **Fill Level Calculation**
The sensor uses linear interpolation:
- **0%** = MAX_DISTANCE (empty bin)
- **100%** = MIN_DISTANCE (full bin)
- **50%** = (MAX_DISTANCE + MIN_DISTANCE) / 2

### **📊 Data Format**

The sensor sends JSON data in this format:

```json
{
  "sensor_id": "ESP32_HR_SENSOR_001",
  "bin_id": "BIN001",
  "fill_level": 87.5,
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

### **🔄 Timing Configuration**

#### **Send Interval**
```cpp
const unsigned long SEND_INTERVAL = 30000; // Send every 30 seconds
```

#### **Retry Logic**
- **Max Retries**: 3 attempts
- **Retry Delay**: 5 seconds
- **Timeout**: 10 seconds per request

### **🔋 Power Management**

#### **Battery Monitoring** (Optional)
```cpp
const bool ENABLE_BATTERY_MONITORING = true;
const int BATTERY_PIN = A0; // Battery voltage reading pin
```

#### **Deep Sleep** (Optional)
```cpp
const bool ENABLE_DEEP_SLEEP = true;
const unsigned long DEEP_SLEEP_TIME = 300000; // 5 minutes
```

### **🚨 Troubleshooting**

#### **WiFi Issues**
- **Problem**: WiFi connection failed
- **Solution**: Check SSID and password
- **Note**: ESP32 only supports 2.4GHz WiFi

#### **Sensor Reading Issues**
- **Problem**: No echo received
- **Solution**: Check connections, ensure sensor is not too close/far
- **Default**: Uses 50% fill level if no echo

#### **Server Connection Issues**
- **Problem**: HTTP error codes
- **Solution**: Verify Django server is running and IP is correct
- **Check**: Firewall settings

#### **Upload Issues**
- **Problem**: Upload failed
- **Solution**: Hold BOOT button while uploading
- **Check**: Correct COM port selected

### **📈 Expected Behavior**

#### **Normal Operation**
- LED blinks 3 times on startup
- Data sent every 30 seconds
- LED blinks once on successful transmission
- LED blinks twice on transmission error
- Serial output shows fill level readings

#### **Error Handling**
- Automatic WiFi reconnection
- Retry logic for failed transmissions
- Deep sleep mode if no WiFi connection
- Default values for sensor failures

### **🎯 Success Indicators**

#### **Serial Monitor Output**
```
✅ WiFi connected successfully!
📡 IP Address: 192.168.1.100
📏 Distance: 25.5 cm, Fill Level: 87.5%
✅ Success! Response Code: 201
```

#### **Django Admin Panel**
- New sensor data entries appear
- Bin fill levels update in real-time
- Sensor status shows "ONLINE"

#### **Frontend Dashboard**
- Bin markers update with new fill levels
- Real-time data visualization
- Sensor status indicators

### **🔧 Advanced Configuration**

#### **Custom Send Intervals**
```cpp
const unsigned long SEND_INTERVAL = 10000; // Send every 10 seconds
```

#### **Custom Fill Level Calculation**
```cpp
// Adjust these values based on your bin dimensions
const int MAX_DISTANCE = 200;  // Empty bin distance
const int MIN_DISTANCE = 5;    // Full bin distance
```

#### **Error Handling**
```cpp
const int MAX_RETRIES = 3;                  // Maximum retry attempts
const unsigned long RETRY_DELAY = 5000;     // Retry delay on failure
```

### **📋 Deployment Checklist**

- [ ] WiFi credentials updated
- [ ] Server IP address correct
- [ ] Unique sensor ID assigned
- [ ] Bin ID matches database
- [ ] Coordinates updated
- [ ] Hardware connections verified
- [ ] Code uploaded successfully
- [ ] Serial monitor shows successful connection
- [ ] Data appears in Django admin panel
- [ ] Frontend dashboard shows real-time updates

### **🚀 Production Deployment**

#### **Enclosure**
- Use weatherproof enclosure for outdoor deployment
- Ensure proper ventilation
- Protect from direct sunlight

#### **Power Supply**
- Use 3.7V Li-ion battery for portable operation
- Add voltage divider for battery monitoring
- Consider solar panel for long-term deployment

#### **Mounting**
- Mount sensor at appropriate height
- Ensure clear line of sight to bin contents
- Avoid obstructions that could affect readings

#### **Network**
- Ensure stable WiFi connection
- Consider WiFi range extenders if needed
- Monitor signal strength regularly

## 🎉 Success!

Once deployed, your HR sensors will:
- ✅ Connect to WiFi automatically
- ✅ Send real-time fill level data every 30 seconds
- ✅ Update bin data in your Django database
- ✅ Show live data on your frontend dashboard
- ✅ Display sensor status as "ONLINE"
- ✅ Handle errors gracefully with retry logic
- ✅ Optimize power usage with deep sleep mode

Your smart waste management system is now ready for real-time monitoring! 🚀
