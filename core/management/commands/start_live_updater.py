from django.core.management.base import BaseCommand
from django.conf import settings
import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(project_root)

from real_time_updater import RealTimeBinUpdater
import time
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Start the real-time bin data updater service'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=float,
            default=1.0,
            help='Update interval in seconds (default: 1.0)'
        )
        parser.add_argument(
            '--api-url',
            type=str,
            default='http://localhost:8000/api',
            help='Django API base URL (default: http://localhost:8000/api)'
        )
        parser.add_argument(
            '--log-level',
            type=str,
            default='INFO',
            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
            help='Logging level (default: INFO)'
        )
    
    def handle(self, *args, **options):
        interval = options['interval']
        api_url = options['api_url']
        log_level = options['log_level']
        
        # Set log level
        logging.getLogger().setLevel(getattr(logging, log_level.upper()))
        
        self.stdout.write(
            self.style.SUCCESS(
                f'🚀 Starting Real-Time Bin Updater...\n'
                f'   API URL: {api_url}\n'
                f'   Update Interval: {interval} seconds\n'
                f'   Log Level: {log_level}'
            )
        )
        
        # Create and start updater
        updater = RealTimeBinUpdater(
            api_base_url=api_url,
            update_interval=interval
        )
        
        try:
            updater.start()
            
            self.stdout.write(
                self.style.SUCCESS('✅ Real-time updater started successfully!')
            )
            self.stdout.write(
                self.style.WARNING('Press Ctrl+C to stop the service')
            )
            
            # Keep the command running
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING('\n🛑 Stopping real-time updater...')
            )
            updater.stop()
            self.stdout.write(
                self.style.SUCCESS('✅ Real-time updater stopped successfully!')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error: {str(e)}')
            )
            updater.stop()
            sys.exit(1)
