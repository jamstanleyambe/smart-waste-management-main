#!/usr/bin/env python3
"""
Real-Time Bin Data Updater
Continuously fetches data from Django API every second to keep all bins updated with live data.
"""

import requests
import time
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bin_updater.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RealTimeBinUpdater:
    """
    Real-time updater that continuously fetches bin data from Django API
    and updates the local database every second.
    """
    
    def __init__(self, api_base_url: str = "http://localhost:8000/api", update_interval: float = 1.0):
        self.api_base_url = api_base_url.rstrip('/')
        self.update_interval = update_interval
        self.running = False
        self.update_thread = None
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SmartWaste-BinUpdater/1.0',
            'Accept': 'application/json'
        })
        
        # API endpoints
        self.bins_endpoint = f"{self.api_base_url}/bin-data/"
        self.sensor_data_endpoint = f"{self.api_base_url}/sensor-data/"
        
        # Statistics
        self.stats = {
            'total_updates': 0,
            'successful_updates': 0,
            'failed_updates': 0,
            'last_update': None,
            'start_time': datetime.now()
        }
        
        logger.info(f"RealTimeBinUpdater initialized with API: {self.api_base_url}")
        logger.info(f"Update interval: {self.update_interval} seconds")
    
    def start(self):
        """Start the real-time update service"""
        if self.running:
            logger.warning("Updater is already running!")
            return
        
        self.running = True
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()
        logger.info("🚀 Real-time bin updater started!")
    
    def stop(self):
        """Stop the real-time update service"""
        if not self.running:
            logger.warning("Updater is not running!")
            return
        
        self.running = False
        if self.update_thread:
            self.update_thread.join(timeout=5)
        logger.info("🛑 Real-time bin updater stopped!")
    
    def _update_loop(self):
        """Main update loop that runs continuously"""
        logger.info("🔄 Starting update loop...")
        
        while self.running:
            try:
                start_time = time.time()
                
                # Fetch and update all bins
                self._update_all_bins()
                
                # Calculate sleep time to maintain exact interval
                elapsed = time.time() - start_time
                sleep_time = max(0, self.update_interval - elapsed)
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    
            except Exception as e:
                logger.error(f"❌ Error in update loop: {str(e)}")
                time.sleep(self.update_interval)
    
    def _update_all_bins(self):
        """Fetch all bins from API and update local data"""
        try:
            # Fetch current bin data
            response = self.session.get(self.bins_endpoint, timeout=5)
            
            if response.status_code == 200:
                bins_data = response.json()
                self.stats['total_updates'] += 1
                self.stats['last_update'] = datetime.now()
                
                logger.info(f"📡 Fetched {len(bins_data)} bins from API")
                
                # Process each bin
                for bin_data in bins_data:
                    self._process_bin_update(bin_data)
                
                self.stats['successful_updates'] += 1
                
                # Log statistics every 10 updates
                if self.stats['total_updates'] % 10 == 0:
                    self._log_statistics()
                    
            else:
                logger.error(f"❌ API request failed: {response.status_code} - {response.text}")
                self.stats['failed_updates'] += 1
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Network error: {str(e)}")
            self.stats['failed_updates'] += 1
        except Exception as e:
            logger.error(f"❌ Unexpected error: {str(e)}")
            self.stats['failed_updates'] += 1
    
    def _process_bin_update(self, bin_data: Dict):
        """Process individual bin update"""
        try:
            bin_id = bin_data.get('bin_id')
            fill_level = bin_data.get('fill_level', 0)
            latitude = bin_data.get('latitude', 0)
            longitude = bin_data.get('longitude', 0)
            
            # Log significant changes
            if fill_level > 80:
                logger.warning(f"⚠️ Bin {bin_id} is {fill_level}% full!")
            elif fill_level > 60:
                logger.info(f"📦 Bin {bin_id} is {fill_level}% full")
            
            # You can add additional processing here
            # For example, sending notifications, updating dashboards, etc.
            
        except Exception as e:
            logger.error(f"❌ Error processing bin {bin_data.get('bin_id', 'Unknown')}: {str(e)}")
    
    def _log_statistics(self):
        """Log current statistics"""
        uptime = datetime.now() - self.stats['start_time']
        success_rate = (self.stats['successful_updates'] / self.stats['total_updates'] * 100) if self.stats['total_updates'] > 0 else 0
        
        logger.info(f"📊 Update Statistics:")
        logger.info(f"   Total Updates: {self.stats['total_updates']}")
        logger.info(f"   Successful: {self.stats['successful_updates']}")
        logger.info(f"   Failed: {self.stats['failed_updates']}")
        logger.info(f"   Success Rate: {success_rate:.1f}%")
        logger.info(f"   Uptime: {uptime}")
        logger.info(f"   Last Update: {self.stats['last_update']}")
    
    def get_statistics(self) -> Dict:
        """Get current statistics"""
        return self.stats.copy()
    
    def is_running(self) -> bool:
        """Check if updater is running"""
        return self.running

def main():
    """Main function to run the updater"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Real-Time Bin Data Updater')
    parser.add_argument('--api-url', default='http://localhost:8000/api', 
                       help='Django API base URL')
    parser.add_argument('--interval', type=float, default=1.0,
                       help='Update interval in seconds')
    parser.add_argument('--log-level', default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Logging level')
    
    args = parser.parse_args()
    
    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level.upper()))
    
    # Create and start updater
    updater = RealTimeBinUpdater(
        api_base_url=args.api_url,
        update_interval=args.interval
    )
    
    try:
        updater.start()
        
        # Keep main thread alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("🛑 Received interrupt signal, shutting down...")
        updater.stop()
        logger.info("✅ Shutdown complete!")

if __name__ == "__main__":
    main()
