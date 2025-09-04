# 🚀 Smart Waste Management System - MASTER BRANCH

## 🎯 Production-Ready Deployment Repository

This is the **MASTER BRANCH** - the final, production-ready version of the Smart Waste Management System.

## ✨ Features

### 🔧 Core Functionality
- **Real-time Sensor Integration**: ESP32 sensor data ingestion and processing
- **Interactive Dashboard**: Streamlit-based real-time monitoring interface
- **Smart Analytics**: Waste composition analysis and trend visualization
- **Route Optimization**: Intelligent waste collection route planning
- **Admin Management**: Comprehensive Django admin interface

### 🗺️ Dashboard Features
- **Interactive Maps**: Real-time bin, truck, and dumping spot visualization
- **Live Data Updates**: Second-by-second data refresh from sensors
- **Search & Highlight**: Advanced search functionality with map integration
- **Responsive Design**: 20%/80% layout with zero-margin optimization
- **Technical Support Monitoring**: Automated issue detection and reporting

### 🔌 API Endpoints
- `/api/bin-data/` - Bin information and status
- `/api/trucks/` - Truck fleet management
- `/api/dumping-spots/` - Waste disposal locations
- `/api/sensor-data/` - ESP32 sensor data ingestion

## 🚀 Deployment

### Prerequisites
- Python 3.13+
- PostgreSQL/MySQL (production database)
- Redis (for caching and background tasks)
- Nginx (reverse proxy)
- SSL Certificate

### Quick Start
```bash
# Clone the repository
git clone https://github.com/jamstanleyambe/smart-waste-management-main.git
cd smart-waste-management-main

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements_production.txt

# Set environment variables
export DJANGO_SETTINGS_MODULE=waste_management.settings_production
export SECRET_KEY="your-secure-secret-key"
export DEBUG=False
export DATABASE_URL="your-database-url"

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic

# Start services
python manage.py runserver 0.0.0.0:8000 &
streamlit run route_dashboard.py --server.port 8502 --server.headless true &
```

## 🔒 Security Features

- **Django Axes**: Brute force protection
- **CSRF Protection**: Cross-site request forgery prevention
- **Rate Limiting**: API request throttling
- **Authentication**: Role-based access control
- **Input Validation**: Comprehensive data sanitization

## 📊 System Architecture

```
ESP32 Sensors → Django API → Database → Streamlit Dashboard
     ↓              ↓           ↓           ↓
  Real-time    REST API    PostgreSQL   Interactive
   Data       Endpoints     Storage      Interface
```

## 🛠️ Management Commands

```bash
# Start real-time data updater
python manage.py start_live_updater

# Seed sample data
python manage.py seed_bins
python manage.py seed_trucks
python manage.py seed_dumpingspots

# Monitor system status
python manage.py check --deploy
```

## 📱 ESP32 Integration

### Sensor Code Requirements
- WiFi connectivity
- HTTP client capabilities
- JSON data formatting
- Real-time data transmission

### Data Format
```json
{
  "sensor_id": "ESP32_001",
  "bin_id": "BIN001",
  "fill_level": 75.5,
  "latitude": 4.0511,
  "longitude": 9.7679,
  "organic_percentage": 40.0,
  "plastic_percentage": 35.0,
  "metal_percentage": 25.0
}
```

## 🔧 Configuration

### Environment Variables
```bash
DJANGO_SETTINGS_MODULE=waste_management.settings_production
SECRET_KEY=your-secure-secret-key
DEBUG=False
DATABASE_URL=postgresql://user:password@localhost/dbname
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
CSRF_TRUSTED_ORIGINS=https://your-domain.com
```

### Production Settings
- `DEBUG = False`
- `SECURE_SSL_REDIRECT = True`
- `SESSION_COOKIE_SECURE = True`
- `CSRF_COOKIE_SECURE = True`

## 📈 Performance

- **API Response Time**: < 100ms
- **Dashboard Refresh**: Real-time (1-second intervals)
- **Database Queries**: Optimized with proper indexing
- **Caching**: Redis-based caching for improved performance

## 🚨 Monitoring & Alerts

- **System Health**: Automated health checks
- **Error Logging**: Comprehensive error tracking
- **Performance Metrics**: Real-time system monitoring
- **Alert System**: Automated notifications for critical issues

## 📋 API Documentation

### Authentication
Most endpoints require authentication. Use Django admin or create API tokens.

### Rate Limits
- **Anonymous**: 100 requests/hour
- **Authenticated**: 1000 requests/hour
- **Sensor Data**: 1000 requests/hour

## 🆘 Support

For technical support or deployment assistance:
- Check the logs in `/logs/` directory
- Review Django admin interface
- Monitor system health via dashboard
- Contact development team

## 📄 License

This project is proprietary software. All rights reserved.

---

**Version**: 1.0.0  
**Last Updated**: September 4, 2025  
**Branch**: MASTER (Production Ready)  
**Status**: ✅ DEPLOYMENT READY
