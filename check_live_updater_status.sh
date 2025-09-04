#!/bin/bash

# Smart Waste Management - Check Live Bin Updater Status
# This script checks the status of the background real-time bin data updater service

echo "📊 Smart Waste Management Live Bin Updater Status"
echo "================================================"

PID_FILE="live_updater.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "❌ Status: NOT RUNNING"
    echo "   - PID file not found"
    echo "   - To start: ./start_live_updater_background.sh"
    exit 1
fi

PID=$(cat "$PID_FILE")

if ! ps -p $PID > /dev/null 2>&1; then
    echo "⚠️  Status: CRASHED"
    echo "   - PID file exists but process is dead"
    echo "   - PID: $PID"
    echo "   - Cleaning up stale PID file..."
    rm -f "$PID_FILE"
    echo "   - To restart: ./start_live_updater_background.sh"
    exit 1
fi

# Get process info
PROCESS_INFO=$(ps -p $PID -o pid,ppid,etime,pcpu,pmem,command --no-headers 2>/dev/null)

if [ $? -eq 0 ]; then
    echo "✅ Status: RUNNING"
    echo "   - PID: $PID"
    echo "   - Process Info: $PROCESS_INFO"
    
    # Check log file
    if [ -f "live_updater.log" ]; then
        echo "   - Log file: live_updater.log"
        echo "   - Last 5 log lines:"
        tail -5 live_updater.log | sed 's/^/     /'
    else
        echo "   - Log file: Not found"
    fi
    
    echo ""
    echo "💡 To stop: ./stop_live_updater.sh"
    echo "💡 To restart: ./stop_live_updater.sh && ./start_live_updater_background.sh"
else
    echo "❌ Status: UNKNOWN"
    echo "   - PID: $PID"
    echo "   - Cannot get process info"
fi
