#!/bin/bash

# Smart Waste Management - Live Bin Updater Startup Script
# This script starts the real-time bin data updater service

echo "🚀 Starting Smart Waste Management Live Bin Updater..."
echo "=================================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run 'python -m venv venv' first."
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if Django server is running
echo "🔍 Checking if Django server is running..."
if ! curl -s http://localhost:8000/api/ > /dev/null; then
    echo "⚠️  Django server doesn't seem to be running on localhost:8000"
    echo "💡 Please start Django server first with: python manage.py runserver 0.0.0.0:8000"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Aborted."
        exit 1
    fi
fi

# Check if required packages are installed
echo "📦 Checking required packages..."
if ! python -c "import requests" 2>/dev/null; then
    echo "❌ 'requests' package not found. Installing..."
    pip install requests
fi

# Start the live updater
echo "🚀 Starting live bin updater..."
echo "   - Updates every 1 second"
echo "   - API: http://localhost:8000/api"
echo "   - Press Ctrl+C to stop"
echo ""

# Run the Django management command
python manage.py start_live_updater --interval 1.0 --api-url http://localhost:8000/api --log-level INFO

echo ""
echo "✅ Live updater stopped."
