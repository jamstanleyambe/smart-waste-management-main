#!/bin/bash

# Smart Waste Management - Live Bin Updater Background Service
# This script starts the real-time bin data updater service in the background

echo "🚀 Starting Smart Waste Management Live Bin Updater (Background Mode)..."
echo "====================================================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run 'python -m venv venv' first."
    exit 1
fi

# Check if updater is already running
PID_FILE="live_updater.pid"
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo "⚠️  Live updater is already running (PID: $PID)"
        echo "💡 To stop it, run: ./stop_live_updater.sh"
        exit 1
    else
        echo "🧹 Cleaning up stale PID file..."
        rm -f "$PID_FILE"
    fi
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if required packages are installed
echo "📦 Checking required packages..."
if ! python -c "import requests" 2>/dev/null; then
    echo "❌ 'requests' package not found. Installing..."
    pip install requests
fi

# Start the live updater in background
echo "🚀 Starting live bin updater in background..."
echo "   - Updates every 1 second"
echo "   - API: http://localhost:8000/api"
echo "   - Log file: live_updater.log"
echo "   - PID file: $PID_FILE"
echo ""

# Run the Django management command in background
nohup python manage.py start_live_updater --interval 1.0 --api-url http://localhost:8000/api --log-level INFO > live_updater.log 2>&1 &

# Save the PID
echo $! > "$PID_FILE"
PID=$(cat "$PID_FILE")

echo "✅ Live updater started successfully!"
echo "   - Process ID: $PID"
echo "   - Running in background"
echo "   - Check logs: tail -f live_updater.log"
echo "   - Stop service: ./stop_live_updater.sh"
echo ""

# Wait a moment and check if it's running
sleep 2
if ps -p $PID > /dev/null 2>&1; then
    echo "✅ Service is running and healthy!"
else
    echo "❌ Service failed to start. Check logs: cat live_updater.log"
    rm -f "$PID_FILE"
    exit 1
fi
