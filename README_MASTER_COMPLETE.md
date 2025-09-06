# 🚀 Smart Waste Management System - Complete Documentation

## 📋 Table of Contents
1. [System Overview](#system-overview)
2. [Features](#features)
3. [Architecture](#architecture)
4. [Installation & Setup](#installation--setup)
5. [ESP32-CAM Integration](#esp32-cam-integration)
6. [API Documentation](#api-documentation)
7. [Dashboard Usage](#dashboard-usage)
8. [Deployment](#deployment)
9. [Troubleshooting](#troubleshooting)
10. [Contributing](#contributing)

---

## 🎯 System Overview

The Smart Waste Management System is a comprehensive IoT solution that combines:
- **Real-time waste bin monitoring** with ultrasonic sensors
- **Visual monitoring** with ESP32-CAM integration
- **Interactive dashboard** with live data visualization
- **Admin panel** for system management
- **RESTful API** for data access and integration

### 🏗️ Technology Stack
- **Backend**: Django 5.2.3 with Django REST Framework
- **Frontend**: Streamlit with interactive maps
- **Database**: SQLite (development) / PostgreSQL (production)
- **IoT Hardware**: ESP32, ESP32-CAM, Ultrasonic sensors
- **Visualization**: Folium maps, real-time charts
- **Deployment**: Docker-ready with production configurations

---

## ✨ Features

### 🗑️ Waste Management
- **Real-time fill level monitoring** for waste bins
- **Organic waste percentage tracking**
- **Location-based bin management**
- **Automated collection scheduling**
- **Historical data analysis**

### 📸 Camera Integration
- **ESP32-CAM image capture** and upload
- **Gallery system** for viewing captured images
- **Bulk image upload** via admin panel
- **Image classification** support (waste detection, security monitoring)
- **Thumbnail generation** for efficient storage

### 📊 Dashboard Features
- **Interactive map** with bin locations and status
- **Real-time data updates** every second
- **Search and filter** functionality
- **Truck tracking** and route optimization
- **Camera gallery** with 4x4 grid layout
- **Responsive design** for all devices

### 🔧 Admin Features
- **User management** with role-based access
- **Bin management** with CRUD operations
- **Camera management** with bulk upload
- **Data export** and reporting
- **System monitoring** and logs

---

## 🏛️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   ESP32 Sensors │    │   ESP32-CAM     │    │   Web Dashboard │
│                 │    │                 │    │                 │
│ • Ultrasonic    │    │ • Image Capture │    │ • Streamlit     │
│ • WiFi          │    │ • WiFi Upload   │    │ • Real-time UI  │
│ • HTTP POST     │    │ • HTTP POST     │    │ • Interactive   │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │     Django Backend        │
                    │                           │
                    │ • REST API                │
                    │ • Database Management     │
                    │ • Image Processing        │
                    │ • Admin Interface         │
                    │ • Authentication          │
                    └───────────────────────────┘
```

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.12+
- Node.js (for frontend dependencies)
- Git
- ESP32 development environment (Arduino IDE)

### 1. Clone Repository
```bash
git clone https://github.com/jamstanleyambe/smart-waste-management-main.git
cd smart-waste-management-main
```

### 2. Python Environment Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements_camera.txt  # For camera features
```

### 3. Database Setup
```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Seed initial data (optional)
python manage.py seed_bins
python manage.py seed_trucks
python manage.py seed_dumpingspots
```

### 4. Start Development Servers
```bash
# Terminal 1: Django API Server
python manage.py runserver 0.0.0.0:8000

# Terminal 2: Streamlit Dashboard
streamlit run route_dashboard.py --server.port 8502 --server.address 0.0.0.0
```

### 5. Access Applications
- **Django Admin**: http://localhost:8000/admin/
- **API Documentation**: http://localhost:8000/api/
- **Streamlit Dashboard**: http://localhost:8502/

---

## 📸 ESP32-CAM Integration

### Hardware Requirements
- ESP32-CAM module (AI-Thinker or similar)
- MicroSD card (optional, for storage)
- Power supply (5V, 2A recommended)
- WiFi network access

### Software Setup

#### 1. Arduino IDE Configuration
```bash
# Install ESP32 board support
# File → Preferences → Additional Board Manager URLs:
https://dl.espressif.com/dl/package_esp32_index.json

# Install ESP32 board package
# Tools → Board → Boards Manager → Search "ESP32" → Install
```

#### 2. Code Upload
Choose the appropriate ESP32-CAM code file:

- **`esp32_cam_perfect.ino`** - Production-ready with robust error handling
- **`esp32_cam_simple.ino`** - Simplified version for testing
- **`esp32_cam_smart_waste.ino`** - Full-featured version
- **`esp32_cam_code.ino`** - Basic version

#### 3. Configuration
Update the following in your chosen `.ino` file:

```cpp
// WiFi Configuration
const char* ssid = "YOUR_WIFI_NAME";
const char* password = "YOUR_WIFI_PASSWORD";

// Server Configuration
const char* server_url = "http://YOUR_SERVER_IP:8000";
const char* camera_id = "ESP32_CAM_001";  // Unique identifier
```

#### 4. Upload Process
1. Select **ESP32 Wrover Module** board
2. Set **Partition Scheme** to "Huge APP (3MB No OTA/1MB SPIFFS)"
3. Set **Flash Size** to "4MB (32Mb)"
4. Upload the code to your ESP32-CAM

### Quick Start Guide
For a 5-minute setup, see: [ESP32_CAM_QUICK_START.md](ESP32_CAM_QUICK_START.md)

For detailed setup, see: [ESP32_CAM_SETUP_GUIDE.md](ESP32_CAM_SETUP_GUIDE.md)

---

## 📡 API Documentation

### Base URL
```
http://localhost:8000/api/
```

### Authentication
Most endpoints require authentication. Use Django's session authentication or token authentication.

### Endpoints

#### 🗑️ Bin Management
```http
GET    /api/bin-data/           # Get all bins
POST   /api/bin-data/           # Create new bin
GET    /api/bin-data/{id}/      # Get specific bin
PUT    /api/bin-data/{id}/      # Update bin
DELETE /api/bin-data/{id}/      # Delete bin
```

#### 📸 Camera Management
```http
GET    /api/camera-images/      # Get all camera images
POST   /api/camera-images/      # Upload new image
GET    /api/camera-images/{id}/ # Get specific image
PUT    /api/camera-images/{id}/ # Update image metadata
DELETE /api/camera-images/{id}/ # Delete image
```

#### 🚛 ESP32-CAM Upload
```http
POST   /api/esp32-cam-upload/   # Direct ESP32-CAM upload
```

**Headers Required:**
```
Content-Type: image/jpeg
X-Camera-ID: ESP32_CAM_001
X-Camera-Type: ESP32-CAM
X-Analysis-Type: WASTE_CLASSIFICATION
```

#### 🚛 Truck Management
```http
GET    /api/trucks/             # Get all trucks
POST   /api/trucks/             # Create new truck
GET    /api/trucks/{id}/        # Get specific truck
PUT    /api/trucks/{id}/        # Update truck
DELETE /api/trucks/{id}/        # Delete truck
```

#### 📍 Dumping Spots
```http
GET    /api/dumping-spots/      # Get all dumping spots
POST   /api/dumping-spots/      # Create new dumping spot
GET    /api/dumping-spots/{id}/ # Get specific dumping spot
PUT    /api/dumping-spots/{id}/ # Update dumping spot
DELETE /api/dumping-spots/{id}/ # Delete dumping spot
```

### Example API Calls

#### Upload Image from ESP32-CAM
```bash
curl -X POST http://localhost:8000/api/esp32-cam-upload/ \
  -H "Content-Type: image/jpeg" \
  -H "X-Camera-ID: ESP32_CAM_001" \
  -H "X-Camera-Type: ESP32-CAM" \
  -H "X-Analysis-Type: WASTE_CLASSIFICATION" \
  --data-binary @image.jpg
```

#### Get Bin Data
```bash
curl -X GET http://localhost:8000/api/bin-data/ \
  -H "Authorization: Token YOUR_TOKEN"
```

---

## 📊 Dashboard Usage

### Navigation
The Streamlit dashboard provides several sections:

1. **🗺️ Map View** - Interactive map with bin locations
2. **📊 Data Tables** - Tabular view of all data
3. **📸 Camera Gallery** - Image gallery from ESP32-CAM
4. **🔍 Search & Filter** - Find specific bins or data

### Features

#### Interactive Map
- **Real-time updates** every second
- **Color-coded bins** by fill level
- **Click to view details** of each bin
- **Search and zoom** to specific locations
- **Truck tracking** with routes

#### Camera Gallery
- **4x4 grid layout** for optimal viewing
- **Image previews** with thumbnails
- **Metadata display** (timestamp, camera ID, analysis type)
- **Responsive design** for all screen sizes

#### Data Management
- **Live data updates** from sensors
- **Export functionality** for reports
- **Filtering options** by location, fill level, etc.
- **Historical data** visualization

---

## 🚀 Deployment

### Development Deployment
```bash
# Start both servers
python manage.py runserver 0.0.0.0:8000 &
streamlit run route_dashboard.py --server.port 8502 --server.address 0.0.0.0 &
```

### Production Deployment
Use the provided deployment script:

```bash
chmod +x deploy_master.sh
./deploy_master.sh
```

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up -d
```

### Environment Variables
Create a `.env` file with:
```env
DEBUG=False
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:pass@localhost/dbname
ALLOWED_HOSTS=your-domain.com,localhost
```

---

## 🔧 Troubleshooting

### Common Issues

#### Django Server Won't Start
```bash
# Check for syntax errors
python -m py_compile core/views.py

# Check migrations
python manage.py showmigrations

# Reset database (development only)
rm db.sqlite3
python manage.py migrate
```

#### ESP32-CAM Connection Issues
1. **Check WiFi credentials** in the code
2. **Verify server IP address** is correct
3. **Ensure Django server** is running on 0.0.0.0:8000
4. **Check firewall settings** on server
5. **Monitor serial output** for error messages

#### Streamlit Dashboard Issues
```bash
# Check Streamlit configuration
cat .streamlit/config.toml

# Clear Streamlit cache
streamlit cache clear

# Check port availability
lsof -i :8502
```

#### Image Upload Problems
1. **Check file permissions** in media directory
2. **Verify PIL/Pillow** installation
3. **Check disk space** for image storage
4. **Monitor Django logs** for errors

### Log Files
- **Django logs**: `logs/django.log`
- **Streamlit logs**: Check terminal output
- **ESP32-CAM logs**: Serial monitor output

### Performance Optimization
1. **Enable database indexing** for large datasets
2. **Use CDN** for static files in production
3. **Implement caching** for frequently accessed data
4. **Optimize image sizes** for ESP32-CAM uploads

---

## 🤝 Contributing

### Development Workflow
1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/new-feature`
3. **Make changes** and test thoroughly
4. **Commit changes**: `git commit -m "Add new feature"`
5. **Push to branch**: `git push origin feature/new-feature`
6. **Create pull request**

### Code Standards
- **Python**: Follow PEP 8 guidelines
- **JavaScript**: Use ES6+ features
- **Documentation**: Update README for new features
- **Testing**: Add tests for new functionality

### Branch Structure
- **`master`** - Production-ready code
- **`main`** - Development branch
- **`feature/*`** - Feature development
- **`hotfix/*`** - Critical bug fixes

---

## 📞 Support

### Documentation
- **Quick Start**: [ESP32_CAM_QUICK_START.md](ESP32_CAM_QUICK_START.md)
- **Setup Guide**: [ESP32_CAM_SETUP_GUIDE.md](ESP32_CAM_SETUP_GUIDE.md)
- **Integration Plan**: [CAMERA_INTEGRATION_PLAN.md](CAMERA_INTEGRATION_PLAN.md)

### Contact
- **Issues**: Create GitHub issues for bugs or feature requests
- **Discussions**: Use GitHub Discussions for questions
- **Email**: [Your contact email]

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🎉 Acknowledgments

- **Django** - Web framework
- **Streamlit** - Dashboard framework
- **ESP32** - IoT hardware platform
- **Folium** - Interactive maps
- **Open source community** - For inspiration and support

---

## 📈 Roadmap

### Version 2.0 (Planned)
- [ ] **Machine Learning** integration for waste classification
- [ ] **Mobile app** for field workers
- [ ] **Advanced analytics** and reporting
- [ ] **Multi-tenant** support
- [ ] **Real-time notifications** system

### Version 3.0 (Future)
- [ ] **AI-powered** route optimization
- [ ] **Predictive maintenance** for sensors
- [ ] **Blockchain** integration for data integrity
- [ ] **IoT device management** platform
- [ ] **Advanced security** features

---

**🚀 Ready to revolutionize waste management with IoT and AI!**
