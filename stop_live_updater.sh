#!/bin/bash

# Smart Waste Management - Stop Live Bin Updater Service
# This script stops the background real-time bin data updater service

echo "🛑 Stopping Smart Waste Management Live Bin Updater..."
echo "====================================================="

PID_FILE="live_updater.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "❌ PID file not found. Service may not be running."
    exit 1
fi

PID=$(cat "$PID_FILE")

if ! ps -p $PID > /dev/null 2>&1; then
    echo "⚠️  Process $PID is not running. Cleaning up PID file..."
    rm -f "$PID_FILE"
    exit 1
fi

echo "🔍 Found running process: PID $PID"
echo "🛑 Stopping service..."

# Try graceful shutdown first
kill $PID

# Wait for graceful shutdown
sleep 3

# Check if still running
if ps -p $PID > /dev/null 2>&1; then
    echo "⚠️  Graceful shutdown failed. Force killing..."
    kill -9 $PID
    sleep 1
fi

# Final check
if ps -p $PID > /dev/null 2>&1; then
    echo "❌ Failed to stop process $PID"
    exit 1
else
    echo "✅ Live updater stopped successfully!"
    rm -f "$PID_FILE"
    echo "🧹 PID file cleaned up"
fi

echo ""
echo "📊 Service Status:"
echo "   - Live updater: STOPPED"
echo "   - To restart: ./start_live_updater_background.sh"
