# 🚀 Smart Waste Management System

A comprehensive, professional-grade waste management system built with Django and Streamlit, featuring real-time monitoring, ESP32-CAM integration, route optimization, and interactive analytics.

## 🌟 Features

### 🗺️ Interactive Dashboard
- **Real-time Map Visualization** - Interactive Folium map showing all waste bins, trucks, and dumping spots
- **Color-coded Markers** - Visual indicators for fill levels and status
- **Route Planning** - Smart truck routing with nearest neighbor algorithm
- **Live Data Updates** - Real-time data from Django REST API
- **Camera Gallery** - 4x4 grid layout for ESP32-CAM images
- **Search & Filter** - Advanced search and filtering capabilities

### 📸 ESP32-CAM Integration
- **Image Capture & Upload** - Direct ESP32-CAM integration with binary upload
- **Gallery System** - Professional image gallery with thumbnails
- **Bulk Upload** - Admin panel support for multiple image uploads
- **Image Classification** - Support for waste detection, security monitoring
- **Real-time Processing** - Automatic thumbnail generation and metadata extraction

### 📊 Analytics & Reporting
- **Comprehensive Statistics** - Total bins, trucks, dumping spots, and users
- **Waste Composition Analysis** - Organic, plastic, and metal content breakdown
- **Fill Level Monitoring** - Real-time bin capacity tracking
- **Performance Metrics** - Route efficiency and collection statistics
- **Historical Data** - Trend analysis and reporting

### 🔐 Admin Management
- **Professional Admin Interface** - Custom styled Django admin with modern UI
- **User Management** - Role-based access control (RBAC)
- **CRUD Operations** - Add, edit, delete all entities
- **Security Features** - Authentication, authorization, and audit logging
- **Dashboard Statistics** - Real-time admin dashboard with key metrics

### 🚛 Fleet Management
- **Truck Tracking** - Real-time GPS coordinates and status
- **Fuel Monitoring** - Fuel level tracking and alerts
- **Driver Management** - Driver assignment and information
- **Maintenance Scheduling** - Vehicle maintenance status tracking

### 🗑️ Waste Collection
- **Bin Management** - Complete waste bin lifecycle management
- **Fill Level Monitoring** - Automatic capacity tracking
- **Waste Classification** - Organic, plastic, and metal content analysis
- **Collection Scheduling** - Optimized pickup routes

### 📍 Dumping Spot Management
- **Location Tracking** - GPS coordinates for all dumping spots
- **Capacity Management** - Total capacity and current usage
- **Content Analysis** - Waste composition at each location
- **Environmental Monitoring** - Impact assessment and reporting

## 🛠️ Technology Stack

### Backend
- **Django 5.2.3** - Robust web framework
- **Django REST Framework** - API development
- **SQLite** - Database (production-ready for PostgreSQL)
- **Python 3.12** - Programming language
- **PIL/Pillow** - Image processing and thumbnail generation

### Frontend
- **Streamlit** - Interactive web application
- **Folium** - Interactive maps
- **Altair** - Statistical visualizations
- **Pandas** - Data manipulation and analysis

### IoT Hardware
- **ESP32** - IoT sensor platform
- **ESP32-CAM** - Camera module for image capture
- **Arduino IDE** - ESP32 development environment

### Security
- **Django-Axes** - Login attempt monitoring
- **Custom Authentication Backend** - Enhanced security
- **CSRF Protection** - Cross-site request forgery prevention
- **Rate Limiting** - API request throttling
- **Session Security** - Secure session management

### Development Tools
- **Git** - Version control
- **GitHub** - Code repository
- **Django Debug Toolbar** - Development debugging
- **Comprehensive Logging** - System monitoring

## 📦 Installation

### Prerequisites
- Python 3.12 or higher
- pip (Python package installer)
- Git

### Clone Repository
```bash
git clone https://github.com/jamstanleyambe/smart-waste-management-main.git
cd smart-waste-management-main
```

### Install Dependencies
```bash
pip install -r requirements.txt
pip install -r requirements_camera.txt  # For ESP32-CAM features
```

### Database Setup
```bash
python manage.py migrate
python manage.py createsuperuser
```

### Seed Data (Optional)
```bash
python manage.py seed_bins
python manage.py seed_trucks
python manage.py seed_dumpingspots
python manage.py seed_roles
```

## 🚀 Running the Application

### Start Django Backend
```bash
python manage.py runserver
```
- **Admin Interface**: http://localhost:8000/admin/
- **API Endpoints**: http://localhost:8000/api/

### Start Streamlit Dashboard
```bash
streamlit run route_dashboard.py --server.port 8502 --server.address 0.0.0.0
```
- **Dashboard**: http://localhost:8502/
- **ESP32-CAM Upload**: http://localhost:8000/api/esp32-cam-upload/

## 📡 API Endpoints

### Authentication
- `POST /admin/login/` - Admin login
- `POST /admin/logout/` - Admin logout

### Waste Management
- `GET /api/bin-data/` - Get all waste bins
- `POST /api/bin-data/` - Create new waste bin
- `GET /api/dumping-spots/` - Get all dumping spots
- `POST /api/dumping-spots/` - Create new dumping spot
- `GET /api/trucks/` - Get all trucks
- `POST /api/trucks/` - Create new truck

### Camera Management
- `GET /api/camera-images/` - Get all camera images
- `POST /api/camera-images/` - Upload new image
- `POST /api/esp32-cam-upload/` - Direct ESP32-CAM upload

### User Management
- `GET /api/roles/` - Get all user roles
- `POST /api/roles/` - Create new role
- `GET /api/users/` - Get all users
- `POST /api/users/` - Create new user

## 🗂️ Project Structure

```
smart-waste-management/
├── core/                          # Main Django app
│   ├── models.py                  # Database models
│   ├── views.py                   # API views and logic
│   ├── serializers.py             # API serializers
│   ├── urls.py                    # URL routing
│   ├── admin.py                   # Admin interface
│   ├── auth_backends.py           # Custom authentication
│   └── management/commands/       # Custom Django commands
│       ├── seed_bins.py
│       ├── seed_trucks.py
│       ├── seed_dumpingspots.py
│       └── seed_roles.py
├── waste_management/              # Django project settings
│   ├── settings.py                # Project configuration
│   ├── urls.py                    # Main URL routing
│   └── wsgi.py                    # WSGI configuration
├── templates/                     # HTML templates
│   ├── admin/                     # Custom admin templates
│   │   ├── base_site.html
│   │   └── index.html
│   └── index.html                 # Main template
├── route_dashboard.py             # Streamlit dashboard
├── requirements.txt               # Python dependencies
├── manage.py                      # Django management script
├── db.sqlite3                     # SQLite database
├── style.css                      # Custom styling
└── README.md                      # This file
```

## 🗄️ Database Models

### Bin
- `bin_id` - Unique identifier
- `latitude`, `longitude` - GPS coordinates
- `fill_level` - Current capacity percentage
- `organic_content`, `plastic_content`, `metal_content` - Waste composition
- `last_updated` - Timestamp of last update

### Truck
- `truck_id` - Unique identifier
- `driver_name` - Driver information
- `current_latitude`, `current_longitude` - GPS coordinates
- `fuel_level` - Current fuel percentage
- `status` - Vehicle status (IDLE, MAINTENANCE, etc.)
- `last_updated` - Timestamp of last update

### DumpingSpot
- `spot_id` - Unique identifier
- `latitude`, `longitude` - GPS coordinates
- `total_capacity` - Maximum capacity
- `organic_content`, `plastic_content`, `metal_content` - Current waste content

### Role
- `name` - Role name
- `description` - Role description
- `permissions` - Associated permissions

### CustomUser
- `username` - User login name
- `email` - User email
- `role` - Associated role
- `is_active` - Account status

## 🎨 UI/UX Features

### Professional Design
- **Modern Color Scheme** - Gray, white, black, and sky blue
- **Responsive Layout** - Works on all device sizes
- **Clean Typography** - Professional font choices
- **Intuitive Navigation** - Easy-to-use interface

### Interactive Elements
- **Hover Effects** - Smooth transitions and feedback
- **Real-time Updates** - Live data refresh
- **Interactive Maps** - Clickable markers and popups
- **Dynamic Charts** - Responsive visualizations

### Admin Interface
- **Custom Styling** - Professional admin dashboard
- **Statistics Cards** - Real-time metrics display
- **Quick Actions** - Easy access to common tasks
- **Responsive Design** - Mobile-friendly admin

## 🔒 Security Features

### Authentication & Authorization
- **Role-Based Access Control** - Granular permissions
- **Custom Authentication Backend** - Enhanced security
- **Session Management** - Secure session handling
- **Password Validation** - Strong password requirements

### API Security
- **Rate Limiting** - Request throttling
- **CSRF Protection** - Cross-site request forgery prevention
- **Input Validation** - Data sanitization
- **Error Handling** - Secure error responses

### Monitoring & Logging
- **Login Attempt Monitoring** - Failed login tracking
- **Audit Logging** - User action tracking
- **Security Headers** - HTTP security headers
- **Activity Monitoring** - System activity tracking

## 📈 Performance Features

### Route Optimization
- **Nearest Neighbor Algorithm** - Efficient route planning
- **Distance Calculation** - GPS-based distance computation
- **Fuel Optimization** - Fuel-efficient routing
- **Time Estimation** - Route time calculations

### Data Management
- **Pagination** - Efficient data loading
- **Caching** - Performance optimization
- **Database Indexing** - Fast query execution
- **Memory Management** - Efficient resource usage

### Real-time Updates
- **Live Data Refresh** - Automatic updates
- **WebSocket Support** - Real-time communication
- **Background Tasks** - Asynchronous processing
- **Event-driven Updates** - Responsive system

## 🚀 Deployment

### Development
- **Local Development** - Easy local setup
- **Hot Reloading** - Automatic code reload
- **Debug Tools** - Development debugging
- **Testing Environment** - Isolated testing

### Production Ready
- **Environment Variables** - Secure configuration
- **Database Migration** - Schema management
- **Static Files** - Optimized asset serving
- **Security Headers** - Production security

### Cloud Deployment
- **Docker Support** - Containerization ready
- **Environment Configuration** - Flexible deployment
- **Database Support** - PostgreSQL ready
- **Load Balancing** - Scalable architecture

## 🧪 Testing

### API Testing
- **Endpoint Testing** - All API endpoints tested
- **Authentication Testing** - Security validation
- **Data Validation** - Input/output testing
- **Error Handling** - Exception testing

### Integration Testing
- **Database Integration** - Data persistence testing
- **Frontend Integration** - UI/UX testing
- **API Integration** - End-to-end testing
- **Performance Testing** - Load testing

## 📊 Monitoring & Analytics

### System Monitoring
- **Performance Metrics** - System performance tracking
- **Error Tracking** - Exception monitoring
- **User Activity** - Usage analytics
- **Resource Usage** - System resource monitoring

### Business Intelligence
- **Waste Analytics** - Waste composition analysis
- **Route Efficiency** - Route optimization metrics
- **Cost Analysis** - Operational cost tracking
- **Environmental Impact** - Sustainability metrics

## 🔧 Configuration

### Environment Variables
```bash
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
```

### Database Configuration
- **Development**: SQLite (default)
- **Production**: PostgreSQL (recommended)
- **Backup**: Automated backup system
- **Migration**: Schema version control

### Security Configuration
- **Session Timeout**: 1 hour
- **Password Policy**: Minimum 8 characters
- **Rate Limiting**: 100 requests per minute
- **CSRF Protection**: Enabled

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Code Standards
- **PEP 8** - Python code style
- **Django Best Practices** - Framework guidelines
- **Security First** - Security-focused development
- **Documentation** - Comprehensive documentation

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Django Community** - Excellent web framework
- **Streamlit Team** - Interactive web app framework
- **Folium Developers** - Interactive mapping library
- **Open Source Community** - All contributing libraries

## 📞 Support

For support and questions:
- **GitHub Issues** - Bug reports and feature requests
- **Documentation** - Comprehensive documentation
- **Community** - Active development community

## 🎯 Roadmap

### Future Features
- **Mobile App** - Native mobile application
- **IoT Integration** - Smart sensor integration
- **Machine Learning** - Predictive analytics
- **Blockchain** - Transparent waste tracking
- **AI Optimization** - Advanced route optimization

### Performance Improvements
- **Caching Layer** - Redis integration
- **CDN Integration** - Content delivery optimization
- **Database Optimization** - Query optimization
- **Load Balancing** - Horizontal scaling

## 📚 Comprehensive Documentation

### 📖 Complete Documentation Suite
- **[Master README](README_MASTER_COMPLETE.md)** - Comprehensive system overview and setup guide
- **[API Documentation](API_DOCUMENTATION.md)** - Complete API reference with examples
- **[Deployment Guide](DEPLOYMENT_GUIDE.md)** - Production deployment instructions
- **[Changelog](CHANGELOG.md)** - Version history and release notes

### 📸 ESP32-CAM Integration
- **[Quick Start Guide](ESP32_CAM_QUICK_START.md)** - 5-minute ESP32-CAM setup
- **[Setup Guide](ESP32_CAM_SETUP_GUIDE.md)** - Detailed hardware and software setup
- **[Integration Plan](CAMERA_INTEGRATION_PLAN.md)** - Complete integration roadmap

### 🔧 ESP32-CAM Code Files
- **`esp32_cam_perfect.ino`** - Production-ready code with robust error handling
- **`esp32_cam_simple.ino`** - Simplified version for testing
- **`esp32_cam_smart_waste.ino`** - Full-featured version
- **`esp32_cam_code.ino`** - Basic version

## 🚀 Production Ready

The system includes:
- **Docker deployment** configurations
- **Production settings** for Django and Streamlit
- **Nginx configuration** with SSL support
- **Database optimization** and caching
- **Security hardening** and monitoring
- **Backup and recovery** procedures

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines and submit pull requests for any improvements.

## 📞 Support

- **Issues**: Create GitHub issues for bugs or feature requests
- **Discussions**: Use GitHub Discussions for questions
- **Documentation**: Check the comprehensive documentation files

---

**🚀 Ready to revolutionize waste management with IoT and AI!**

*Last updated: September 6, 2025* 

