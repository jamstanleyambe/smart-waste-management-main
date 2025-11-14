# Smart Waste Management - Configuration Guide

## Server Configuration

### Default URLs
The application is configured to use `localhost:8000` by default for development. For production or different environments, update the following files:

#### Python Files
- `core/management/commands/fetch_sensor_data.py` - Line 24
- `real_time_fetcher.py` - Line 32
- `monitor_bins.py` - Lines 18, 29, 109

#### ESP32 Camera Code
- `esp32_cam_perfect.ino` - Line 37
- `esp32_cam_simple.ino` - Line 33
- `esp32_cam_smart_waste.ino` - Line 38
- `esp32_cam_code.ino` - Line 42

### Environment Variables
You can also use environment variables to configure the server:

```bash
export DJANGO_ALLOWED_HOSTS="localhost,127.0.0.1,your-server-ip"
export DJANGO_DEBUG="True"  # or "False" for production
```

### Django Settings
The main configuration is in `waste_management/settings.py`:
- `ALLOWED_HOSTS` - Line 17
- `CSRF_TRUSTED_ORIGINS` - Line 90

## Network Configuration

### For Local Development
- Server URL: `http://localhost:8000`
- ESP32 should connect to the same WiFi network
- Update ESP32 code with your computer's IP address

### For Production
- Update all hardcoded URLs to your production server
- Configure proper CORS settings
- Set up SSL certificates for HTTPS

## Troubleshooting

### Connection Issues
If you see "No route to host" errors:
1. Check if the Django server is running on the correct port
2. Verify the IP address in ESP32 code matches your server
3. Ensure firewall allows connections on port 8000

### ESP32 Connection Issues
1. Verify WiFi credentials in ESP32 code
2. Check if ESP32 and server are on the same network
3. Test server accessibility from ESP32's network
