#!/usr/bin/env python3
"""
Real-Time Bin Monitor
Shows live updates of bin fill levels and sensor data
"""

import time
import requests
import json
from datetime import datetime
import os
import sys

def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def fetch_bin_data(api_url="http://localhost:8000"):
    """Fetch current bin data"""
    try:
        response = requests.get(f"{api_url}/api/bin-data/", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return []
    except:
        return []

def fetch_sensor_data(api_url="http://localhost:8000"):
    """Fetch latest sensor data"""
    try:
        response = requests.get(f"{api_url}/api/sensor-data/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get('results', [])
        else:
            return []
    except:
        return []

def get_status_color(fill_level):
    """Get color code for fill level status"""
    if fill_level >= 80:
        return "🔴"  # Critical
    elif fill_level >= 70:
        return "🟠"  # High
    elif fill_level >= 50:
        return "🟡"  # Moderate
    elif fill_level >= 20:
        return "🟢"  # Low
    else:
        return "⚪"  # Empty

def display_bin_status(bins, sensors):
    """Display current bin status"""
    clear_screen()
    
    print("🚮 SMART WASTE MANAGEMENT - REAL-TIME MONITOR")
    print("=" * 60)
    print(f"⏰ Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 Total Bins: {len(bins)} | 📡 Active Sensors: {len(sensors)}")
    print("=" * 60)
    print()
    
    if not bins:
        print("⚠️  No bin data available")
        return
    
    # Display bin status
    print("📦 BIN STATUS:")
    print("-" * 60)
    for bin_data in bins[:10]:  # Show first 10 bins
        bin_id = bin_data.get('bin_id', 'Unknown')
        fill_level = bin_data.get('fill_level', 0)
        lat = bin_data.get('latitude', 0)
        lon = bin_data.get('longitude', 0)
        last_updated = bin_data.get('last_updated', 'Unknown')
        
        status_icon = get_status_color(fill_level)
        
        print(f"{status_icon} {bin_id:8} | Fill: {fill_level:5.1f}% | Location: ({lat:.4f}, {lon:.4f}) | Updated: {last_updated[:19]}")
    
    if len(bins) > 10:
        print(f"... and {len(bins) - 10} more bins")
    
    print()
    print("📡 LATEST SENSOR READINGS:")
    print("-" * 60)
    
    if sensors:
        for sensor in sensors[:5]:  # Show latest 5 sensor readings
            sensor_id = sensor.get('sensor_id', 'Unknown')
            bin_id = sensor.get('bin_id', 'Unknown')
            fill_level = sensor.get('fill_level', 0)
            timestamp = sensor.get('timestamp', 'Unknown')
            
            status_icon = get_status_color(fill_level)
            
            print(f"📡 {sensor_id:15} | Bin: {bin_id:8} | Fill: {fill_level:5.1f}% | Time: {timestamp[:19]}")
    else:
        print("⚠️  No sensor data available")
    
    print()
    print("🔄 Auto-refreshing every 2 seconds... Press Ctrl+C to stop")
    print("=" * 60)

def main():
    """Main monitoring loop"""
    api_url = "http://localhost:8000"
    
    print("🚀 Starting Real-Time Bin Monitor...")
    print(f"📡 Connecting to: {api_url}")
    print("⏳ Initializing...")
    
    try:
        while True:
            # Fetch data
            bins = fetch_bin_data(api_url)
            sensors = fetch_sensor_data(api_url)
            
            # Display status
            display_bin_status(bins, sensors)
            
            # Wait before next update
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped by user")
        print("👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("🔧 Please check if the Django server is running")

if __name__ == "__main__":
    main()
