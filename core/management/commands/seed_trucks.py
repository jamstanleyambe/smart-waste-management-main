import os
import django
import random
import math
from django.core.management.base import BaseCommand
from django.conf import settings

# Ensure Django settings are configured
if not settings.configured:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'waste_management.settings')
    django.setup()

from core.models import Truck

def generate_random_location(center_lat, center_lon, radius_km):
    # Convert radius from km to degrees (approximate)
    radius_deg = radius_km / 111.32
    
    # Generate random angle and distance
    angle = random.uniform(0, 2 * math.pi)
    distance = random.uniform(0, radius_deg)
    
    # Calculate new coordinates
    lat = center_lat + distance * math.cos(angle)
    lon = center_lon + distance * math.sin(angle)
    
    return lat, lon

class Command(BaseCommand):
    help = 'Seeds the database with 4 random trucks.'

    def handle(self, *args, **options):
        self.stdout.write('Clearing existing trucks...')
        Truck.objects.all().delete()
        self.stdout.write('Existing trucks cleared.')

        center_lat = 4.0511
        center_lon = 9.7679
        radius_km = 5.0  # Match bins/dumping spots radius
        num_trucks = 4

        self.stdout.write(f'Creating {num_trucks} random trucks...')

        for i in range(num_trucks):
            lat, lon = generate_random_location(center_lat, center_lon, radius_km)
            Truck.objects.create(
                truck_id=f"TRUCK{i+1:02d}",
                driver_name=f"Driver {i+1}",
                current_latitude=lat,
                current_longitude=lon,
                fuel_level=round(random.uniform(10, 100), 2),
                status=random.choice(["ACTIVE", "IDLE", "MAINTENANCE"])
            )
            self.stdout.write(f'Created Truck TRUCK{i+1:02d}')

        self.stdout.write(f'Successfully seeded {num_trucks} trucks.') 