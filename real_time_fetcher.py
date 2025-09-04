#!/usr/bin/env python3
"""
Real-Time Sensor Data Fetcher
Continuously fetches data from sensors and updates bin information every second
"""

import time
import requests
import json
import logging
from datetime import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Bin, SensorData

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sensor_fetcher.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RealTimeSensorFetcher:
    """
    Real-time sensor data fetcher that updates bin information every second
    """
    
    def __init__(self, api_base_url="http://192.168.1.116:8000"):
        self.api_base_url = api_base_url
        self.sensor_data_url = f"{api_base_url}/api/sensor-data/"
        self.bin_data_url = f"{api_base_url}/api/bin-data/"
        self.session = requests.Session()
        self.session.timeout = 5
        
    def fetch_sensor_data(self):
        """Fetch latest sensor data from the API"""
        try:
            response = self.session.get(self.sensor_data_url)
            if response.status_code == 200:
                data = response.json()
                return data.get('results', [])
            else:
                logger.warning(f"Failed to fetch sensor data: {response.status_code}")
                return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching sensor data: {e}")
            return []
    
    def fetch_bin_data(self):
        """Fetch current bin data from the API"""
        try:
            response = self.session.get(self.bin_data_url)
            if response.status_code == 200:
                data = response.json()
                return data
            else:
                logger.warning(f"Failed to fetch bin data: {response.status_code}")
                return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching bin data: {e}")
            return []
    
    def update_bin_from_sensor(self, sensor_data):
        """Update bin information based on latest sensor data"""
        try:
            bin_id = sensor_data.get('bin_id')
            if not bin_id:
                return False
                
            # Get the bin instance
            try:
                bin_instance = Bin.objects.get(bin_id=bin_id)
            except Bin.DoesNotExist:
                logger.warning(f"Bin {bin_id} not found, creating new bin...")
                bin_instance = Bin(
                    bin_id=bin_id,
                    fill_level=sensor_data.get('fill_level', 0),
                    latitude=sensor_data.get('latitude', 0),
                    longitude=sensor_data.get('longitude', 0),
                    organic_percentage=sensor_data.get('organic_percentage', 40),
                    plastic_percentage=sensor_data.get('plastic_percentage', 35),
                    metal_percentage=sensor_data.get('metal_percentage', 25)
                )
            
            # Update bin with sensor data
            bin_instance.fill_level = sensor_data.get('fill_level', bin_instance.fill_level)
            bin_instance.latitude = sensor_data.get('latitude', bin_instance.latitude)
            bin_instance.longitude = sensor_data.get('longitude', bin_instance.longitude)
            bin_instance.organic_percentage = sensor_data.get('organic_percentage', bin_instance.organic_percentage)
            bin_instance.plastic_percentage = sensor_data.get('plastic_percentage', bin_instance.plastic_percentage)
            bin_instance.metal_percentage = sensor_data.get('metal_percentage', bin_instance.metal_percentage)
            bin_instance.last_updated = timezone.now()
            
            bin_instance.save()
            logger.info(f"✅ Bin {bin_id} updated: Fill level {bin_instance.fill_level}%, Location ({bin_instance.latitude}, {bin_instance.longitude})")
            return True
            
        except Exception as e:
            logger.error(f"Error updating bin {bin_id}: {e}")
            return False
    
    def process_sensor_data(self, sensor_data_list):
        """Process all sensor data and update bins"""
        updated_bins = 0
        for sensor_data in sensor_data_list:
            if self.update_bin_from_sensor(sensor_data):
                updated_bins += 1
        
        if updated_bins > 0:
            logger.info(f"🔄 Updated {updated_bins} bins with sensor data")
        return updated_bins
    
    def run_continuous_fetch(self, interval_seconds=1):
        """Run continuous data fetching every specified interval"""
        logger.info(f"🚀 Starting real-time sensor data fetcher (every {interval_seconds} second)")
        logger.info(f"📡 API Base URL: {self.api_base_url}")
        
        try:
            while True:
                start_time = time.time()
                
                # Fetch latest sensor data
                sensor_data = self.fetch_sensor_data()
                
                if sensor_data:
                    # Process and update bins
                    updated_count = self.process_sensor_data(sensor_data)
                    
                    # Log status
                    current_time = datetime.now().strftime("%H:%M:%S")
                    logger.info(f"⏰ {current_time} - Fetched {len(sensor_data)} sensor readings, updated {updated_count} bins")
                else:
                    logger.warning("⚠️ No sensor data received")
                
                # Calculate sleep time to maintain interval
                elapsed = time.time() - start_time
                sleep_time = max(0, interval_seconds - elapsed)
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    
        except KeyboardInterrupt:
            logger.info("🛑 Real-time fetcher stopped by user")
        except Exception as e:
            logger.error(f"❌ Fatal error in real-time fetcher: {e}")
            raise

def main():
    """Main function to run the real-time fetcher"""
    import os
    import django
    
    # Setup Django environment
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'waste_management.settings')
    django.setup()
    
    # Create and run the fetcher
    fetcher = RealTimeSensorFetcher()
    
    # You can adjust the interval here (1 second = real-time, 5 seconds = near real-time)
    fetcher.run_continuous_fetch(interval_seconds=1)

if __name__ == "__main__":
    main()
