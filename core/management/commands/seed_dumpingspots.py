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

from core.models import DumpingSpot

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
    help = 'Seeds the database with at most 5 random dumping spots.'

    def handle(self, *args, **options):
        self.stdout.write('Clearing existing dumping spots...')
        DumpingSpot.objects.all().delete()
        self.stdout.write('Existing dumping spots cleared.')

        # Center coordinates for Douala 5 (same as bins)
        center_lat = 4.0511
        center_lon = 9.7679
        radius_km = 5.0  # Match bins radius
        num_dumping_spots = 5

        self.stdout.write(f'Creating {num_dumping_spots} random dumping spots...')

        for i in range(num_dumping_spots):
            lat, lon = generate_random_location(center_lat, center_lon, radius_km)
            
            # Generate random total capacity and initial fill level
            total_capacity = random.uniform(1000, 5000) # Random capacity
            initial_fill_level_percentage = random.uniform(0, 50) # Dumping spots start partially filled
            initial_total_content = (initial_fill_level_percentage / 100) * total_capacity
            
            # Distribute initial content randomly among waste types
            organic_ratio = random.uniform(0, 1)
            plastic_ratio = random.uniform(0, 1 - organic_ratio)
            metal_ratio = 1 - organic_ratio - plastic_ratio
            
            organic_content = initial_total_content * organic_ratio
            plastic_content = initial_total_content * plastic_ratio
            metal_content = initial_total_content * metal_ratio

            DumpingSpot.objects.create(
                spot_id=f"DS{i+1:02d}",
                latitude=lat,
                longitude=lon,
                total_capacity=total_capacity,
                organic_content=organic_content,
                plastic_content=plastic_content,
                metal_content=metal_content,
            )
            self.stdout.write(f'Created Dumping Spot DS{i+1:02d}')

        self.stdout.write(f'Successfully seeded {num_dumping_spots} dumping spots.') 