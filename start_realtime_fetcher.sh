#!/bin/bash

# Real-Time Sensor Data Fetcher Startup Script
# This script starts the Django management command to fetch sensor data every second

echo "🚀 Starting Real-Time Sensor Data Fetcher..."
echo "📡 Will fetch data every 1 second and update bins automatically"
echo "⏰ Started at: $(date)"
echo ""

# Change to project directory
cd /Applications/smart-waste-management

# Activate virtual environment
source venv/bin/activate

# Start the real-time fetcher in the background
echo "🔄 Starting continuous data fetching..."
python manage.py fetch_sensor_data --continuous --interval 1 &

# Get the process ID
FETCHER_PID=$!
echo "✅ Real-time fetcher started with PID: $FETCHER_PID"
echo "📝 Logs will be written to: logs/sensor_fetcher.log"
echo ""
echo "🛑 To stop the fetcher, run: kill $FETCHER_PID"
echo "📊 To check status, run: ps aux | grep fetch_sensor_data"
echo ""

# Save PID to file for easy management
echo $FETCHER_PID > .sensor_fetcher.pid
echo "💾 Process ID saved to .sensor_fetcher.pid"

# Wait a moment to see initial output
sleep 3

echo "🎯 Real-time fetcher is now running in the background!"
echo "🌐 Your Streamlit dashboard will show live updates every second"
echo "📱 ESP32 sensors will automatically update bin information"
