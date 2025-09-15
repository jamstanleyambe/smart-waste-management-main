# 📡 Smart Waste Management System - API Documentation

## 🔗 Base URL
```
http://localhost:8000/api/
```

## 🔐 Authentication

### Session Authentication (Default)
```python
# For web-based clients
session = requests.Session()
session.get('http://localhost:8000/api/bin-data/')
```

### Token Authentication
```python
# For API clients
headers = {'Authorization': 'Token YOUR_TOKEN_HERE'}
requests.get('http://localhost:8000/api/bin-data/', headers=headers)
```

### Anonymous Access
Some endpoints allow anonymous access for dashboard functionality:
- `GET /api/bin-data/`
- `GET /api/trucks/`
- `POST /api/esp32-cam-upload/`

---

## 🗑️ Bin Management API

### Get All Bins
```http
GET /api/bin-data/
```

**Response:**
```json
[
  {
    "id": 1,
    "bin_id": "BIN001",
    "fill_level": 75.5,
    "latitude": 4.0511,
    "longitude": 9.7679,
    "organic_percentage": 60.0,
    "last_updated": "2025-09-06T10:30:00Z",
    "status": "active"
  }
]
```

### Create New Bin
```http
POST /api/bin-data/
Content-Type: application/json
```

**Request Body:**
```json
{
  "bin_id": "BIN002",
  "fill_level": 0.0,
  "latitude": 4.0520,
  "longitude": 9.7680,
  "organic_percentage": 0.0
}
```

**Response:** `201 Created`
```json
{
  "id": 2,
  "bin_id": "BIN002",
  "fill_level": 0.0,
  "latitude": 4.0520,
  "longitude": 9.7680,
  "organic_percentage": 0.0,
  "last_updated": "2025-09-06T10:35:00Z",
  "status": "active"
}
```

### Get Specific Bin
```http
GET /api/bin-data/{id}/
```

### Update Bin
```http
PUT /api/bin-data/{id}/
Content-Type: application/json
```

### Delete Bin
```http
DELETE /api/bin-data/{id}/
```

---

## 📸 Camera Management API

### Get All Camera Images
```http
GET /api/camera-images/
```

**Query Parameters:**
- `camera_id` - Filter by camera ID
- `analysis_type` - Filter by analysis type
- `date_from` - Filter from date (YYYY-MM-DD)
- `date_to` - Filter to date (YYYY-MM-DD)

**Response (fields match `CameraImageSerializer`):**
```json
[
  {
    "id": 1,
    "camera": 1,
    "camera_name": "Camera ESP32_CAM_001",
    "camera_type": "ESP32_CAM",
    "image": "/media/camera_images/2025/09/15/image_ESP32_CAM_001_20250915_150109.jpg",
    "image_url": "/media/camera_images/2025/09/15/image_ESP32_CAM_001_20250915_150109.jpg",
    "thumbnail_url": "/media/camera_thumbnails/2025/09/15/thumb_image_ESP32_CAM_001_20250915_150109.jpg",
    "analysis_type": "WASTE_CLASSIFICATION",
    "confidence_score": null,
    "detected_objects": {},
    "analysis_result": {},
    "metadata": {
      "file_size": 12847
    },
    "is_analyzed": false,
    "created_at": "2025-09-15T15:01:10Z",
    "file_size_mb": 0.13,
    "dimensions": "1600 x 1200"
  }
]
```

### Upload New Image (multipart form)
```http
POST /api/camera-images/
Content-Type: multipart/form-data
```

**Form Data:**
- `image` - Image file (JPEG/PNG)
- `X-Camera-ID` header can be provided instead of form field; backend links to the camera automatically
- `analysis_type` - Optional analysis tag

### ESP32-CAM Direct Upload (raw JPEG body)
```http
POST /api/esp32-cam-upload/
Content-Type: image/jpeg
X-Camera-ID: ESP32_CAM_001
X-Camera-Type: ESP32-CAM
X-Analysis-Type: WASTE_CLASSIFICATION
```

**Request Body:** Raw binary image data

**Response:** `201 Created`
```json
{
  "id": 2,
  "camera": 1,
  "camera_name": "Camera ESP32_CAM_001",
  "camera_type": "ESP32_CAM",
  "image": "/media/camera_images/2025/09/15/image_ESP32_CAM_001_20250915_150109.jpg",
  "image_url": "/media/camera_images/2025/09/15/image_ESP32_CAM_001_20250915_150109.jpg",
  "thumbnail_url": "/media/camera_thumbnails/2025/09/15/thumb_image_ESP32_CAM_001_20250915_150109.jpg",
  "analysis_type": "WASTE_CLASSIFICATION",
  "metadata": { "file_size": 12847 },
  "is_analyzed": false,
  "created_at": "2025-09-15T15:01:10Z",
  "file_size_mb": 0.13,
  "dimensions": "1600 x 1200"
}
```

### Get Specific Image
```http
GET /api/camera-images/{id}/
```

### Update Image Metadata
```http
PUT /api/camera-images/{id}/
Content-Type: application/json
```

### Delete Image
```http
DELETE /api/camera-images/{id}/
```

---

## 🚛 Truck Management API

### Get All Trucks
```http
GET /api/trucks/
```

**Response:**
```json
[
  {
    "id": 1,
    "truck_id": "TRUCK001",
    "driver_name": "John Doe",
    "capacity": 5000.0,
    "current_location": {
      "latitude": 4.0511,
      "longitude": 9.7679
    },
    "status": "available",
    "last_updated": "2025-09-06T10:30:00Z"
  }
]
```

### Create New Truck
```http
POST /api/trucks/
Content-Type: application/json
```

**Request Body:**
```json
{
  "truck_id": "TRUCK002",
  "driver_name": "Jane Smith",
  "capacity": 7500.0,
  "current_location": {
    "latitude": 4.0520,
    "longitude": 9.7680
  }
}
```

---

## 📍 Dumping Spots API

### Get All Dumping Spots
```http
GET /api/dumping-spots/
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "Central Dumping Site",
    "latitude": 4.0600,
    "longitude": 9.7700,
    "capacity": 10000.0,
    "current_load": 2500.0,
    "status": "active",
    "last_updated": "2025-09-06T10:30:00Z"
  }
]
```

---

## 📊 Sensor Data API

### Get Sensor Data
```http
GET /api/sensor-data/
```

**Query Parameters:**
- `bin_id` - Filter by bin ID
- `date_from` - Filter from date
- `date_to` - Filter to date
- `limit` - Limit number of results

**Response:**
```json
[
  {
    "id": 1,
    "bin": {
      "id": 1,
      "bin_id": "BIN001"
    },
    "fill_level": 75.5,
    "organic_percentage": 60.0,
    "temperature": 25.3,
    "humidity": 45.2,
    "timestamp": "2025-09-06T10:30:00Z"
  }
]
```

### Submit Sensor Data
```http
POST /api/sensor-data/
Content-Type: application/json
```

**Request Body:**
```json
{
  "bin_id": "BIN001",
  "fill_level": 80.0,
  "organic_percentage": 65.0,
  "temperature": 26.1,
  "humidity": 47.8
}
```

---

## 🔍 Search and Filter API

### Search Bins
```http
GET /api/bin-data/?search=main
```

### Filter by Fill Level
```http
GET /api/bin-data/?fill_level_min=50&fill_level_max=100
```

### Filter by Location
```http
GET /api/bin-data/?latitude_min=4.05&latitude_max=4.06&longitude_min=9.76&longitude_max=9.77
```

### Filter by Date Range
```http
GET /api/camera-images/?date_from=2025-09-01&date_to=2025-09-30
```

---

## 📈 Analytics API

### Get Bin Statistics
```http
GET /api/analytics/bins/
```

**Response:**
```json
{
  "total_bins": 25,
  "active_bins": 23,
  "full_bins": 5,
  "average_fill_level": 45.2,
  "total_organic_percentage": 58.7,
  "last_updated": "2025-09-06T10:30:00Z"
}
```

### Get Collection Statistics
```http
GET /api/analytics/collections/
```

**Response:**
```json
{
  "total_collections": 150,
  "collections_today": 8,
  "average_collection_time": 45.5,
  "total_waste_collected": 12500.0,
  "efficiency_rating": 87.5
}
```

---

## 🚨 Error Handling

### Standard Error Response
```json
{
  "error": "Error message",
  "details": "Detailed error information",
  "code": "ERROR_CODE",
  "timestamp": "2025-09-06T10:30:00Z"
}
```

### HTTP Status Codes
- `200 OK` - Request successful
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Access denied
- `404 Not Found` - Resource not found
- `405 Method Not Allowed` - HTTP method not allowed
- `415 Unsupported Media Type` - Invalid content type
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

### Common Error Codes
- `INVALID_DATA` - Request data validation failed
- `RESOURCE_NOT_FOUND` - Requested resource doesn't exist
- `PERMISSION_DENIED` - Insufficient permissions
- `RATE_LIMIT_EXCEEDED` - Too many requests
- `UPLOAD_FAILED` - File upload failed
- `PROCESSING_ERROR` - Image processing failed

---

## 🔒 Rate Limiting

### Default Limits
- **Authenticated users**: 1000 requests/hour
- **Anonymous users**: 100 requests/hour
- **ESP32 sensors**: 500 requests/hour

### Rate Limit Headers
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1630929600
```

---

## 📝 Example Usage

### Python Examples

#### Upload Image from ESP32-CAM
```python
import requests

url = "http://localhost:8000/api/esp32-cam-upload/"
headers = {
    "Content-Type": "image/jpeg",
    "X-Camera-ID": "ESP32_CAM_001",
    "X-Camera-Type": "ESP32-CAM",
    "X-Analysis-Type": "WASTE_CLASSIFICATION"
}

with open("image.jpg", "rb") as f:
    response = requests.post(url, data=f, headers=headers)
    print(response.json())
```

#### Get Bin Data
```python
import requests

url = "http://localhost:8000/api/bin-data/"
response = requests.get(url)
bins = response.json()

for bin in bins:
    print(f"Bin {bin['bin_id']}: {bin['fill_level']}% full")
```

#### Submit Sensor Data
```python
import requests
import json

url = "http://localhost:8000/api/sensor-data/"
data = {
    "bin_id": "BIN001",
    "fill_level": 75.5,
    "organic_percentage": 60.0,
    "temperature": 25.3,
    "humidity": 45.2
}

response = requests.post(url, json=data)
print(response.status_code)
```

### JavaScript Examples

#### Fetch Bin Data
```javascript
fetch('http://localhost:8000/api/bin-data/')
  .then(response => response.json())
  .then(data => {
    console.log('Bins:', data);
    data.forEach(bin => {
      console.log(`Bin ${bin.bin_id}: ${bin.fill_level}% full`);
    });
  })
  .catch(error => console.error('Error:', error));
```

#### Upload Image
```javascript
const formData = new FormData();
formData.append('image', fileInput.files[0]);
formData.append('camera_id', 'ESP32_CAM_001');
formData.append('analysis_type', 'WASTE_CLASSIFICATION');

fetch('http://localhost:8000/api/camera-images/', {
  method: 'POST',
  body: formData
})
.then(response => response.json())
.then(data => console.log('Upload successful:', data))
.catch(error => console.error('Upload failed:', error));
```

### cURL Examples

#### Get All Bins
```bash
curl -X GET http://localhost:8000/api/bin-data/ \
  -H "Accept: application/json"
```

#### Upload Image (ESP32-CAM raw)
```bash
curl -X POST http://localhost:8000/api/esp32-cam-upload/ \
  -H "Content-Type: image/jpeg" \
  -H "X-Camera-ID: ESP32_CAM_001" \
  -H "X-Camera-Type: ESP32-CAM" \
  -H "X-Analysis-Type: WASTE_CLASSIFICATION" \
  --data-binary @image.jpg
```

#### Upload Image (multipart form)
```bash
curl -X POST http://localhost:8000/api/camera-images/ \
  -H "X-Camera-ID: ESP32_CAM_001" \
  -F image=@image.jpg
```

#### Create New Bin
```bash
curl -X POST http://localhost:8000/api/bin-data/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_TOKEN" \
  -d '{
    "bin_id": "BIN003",
    "fill_level": 0.0,
    "latitude": 4.0530,
    "longitude": 9.7690,
    "organic_percentage": 0.0
  }'
```

---

## 🔧 Testing

### Test Endpoints
```bash
# Test API connectivity
curl -I http://localhost:8000/api/bin-data/

# Test image upload
python test_camera_api.py

# Test sensor data submission
curl -X POST http://localhost:8000/api/sensor-data/ \
  -H "Content-Type: application/json" \
  -d '{"bin_id": "BIN001", "fill_level": 50.0}'
```

### API Testing Tools
- **Postman** - GUI-based API testing
- **Insomnia** - Alternative to Postman
- **curl** - Command-line testing
- **Python requests** - Programmatic testing

---

## 📚 Additional Resources

- **Django REST Framework**: https://www.django-rest-framework.org/
- **Streamlit**: https://streamlit.io/
- **ESP32-CAM**: https://github.com/espressif/arduino-esp32
- **Folium Maps**: https://python-visualization.github.io/folium/

---

**🚀 Happy coding with the Smart Waste Management API!**
