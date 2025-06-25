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

from core.models import Bin

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

def generate_waste_composition():
    # Generate random percentages that sum to 100%
    organic = random.uniform(30, 40)  # 30-40% organic
    plastic = random.uniform(30, 40)  # 30-40% plastic
    metal = 100 - organic - plastic   # Remaining percentage for metal
    
    # Ensure metal is not negative
    if metal < 0:
        # Adjust organic and plastic to ensure metal is positive
        excess = abs(metal)
        organic -= excess * 0.5
        plastic -= excess * 0.5
        metal = 0
    
    # Ensure percentages are non-negative after adjustment
    organic = max(0, organic)
    plastic = max(0, plastic)
    metal = max(0, metal)
    
    # Re-normalize to 100% if necessary after adjustments
    total = organic + plastic + metal
    if total > 0:
        organic = (organic / total) * 100
        plastic = (plastic / total) * 100
        metal = (metal / total) * 100

    return organic, plastic, metal

class Command(BaseCommand):
    help = 'Seeds the database with bins and dumping spots.'

    def handle(self, *args, **options):
        self.stdout.write('Clearing existing bins...')
        Bin.objects.all().delete()
        self.stdout.write('Existing bins cleared.')

        # Center coordinates for Douala 5
        center_lat = 4.0511
        center_lon = 9.7679
        radius_km = 5.0  # Increased to 5km radius
    
        # Create bins with specific fill level distributions
        bin_distributions = [
            (5, 0, 49),    # 5 bins below 50%
            (10, 50, 79),  # 10 bins between 50-79%
            (10, 80, 99),  # 10 bins between 80-99%
            (10, 100, 100) # 10 bins at 100%
        ]
        bin_count = 0
        for num_bins, min_fill, max_fill in bin_distributions:
            for i in range(num_bins):
                lat, lon = generate_random_location(center_lat, center_lon, radius_km)
                organic, plastic, metal = generate_waste_composition()
                fill_level = random.uniform(min_fill, max_fill)
                Bin.objects.create(
                    bin_id=f"BIN{bin_count+1:03d}",
                    fill_level=fill_level,
                    latitude=lat,
                    longitude=lon,
                    organic_percentage=organic,
                    plastic_percentage=plastic,
                    metal_percentage=metal
                )
                bin_count += 1
        # Add 5 technical support bins, each with a different/creative issue
        tech_bin_ids = []
        # 1. Negative fill
        lat, lon = generate_random_location(center_lat, center_lon, radius_km)
        organic, plastic, metal = generate_waste_composition()
        bin1 = Bin.objects.create(
            bin_id=f"BIN{bin_count+1:03d}",
            fill_level=-20,
            latitude=lat,
            longitude=lon,
            organic_percentage=organic,
            plastic_percentage=plastic,
            metal_percentage=metal
        )
        tech_bin_ids.append(bin1.id)
        bin_count += 1
        # 2. Overfilled
        lat, lon = generate_random_location(center_lat, center_lon, radius_km)
        organic, plastic, metal = generate_waste_composition()
        bin2 = Bin.objects.create(
            bin_id=f"BIN{bin_count+1:03d}",
            fill_level=150,
            latitude=lat,
            longitude=lon,
            organic_percentage=organic,
            plastic_percentage=plastic,
            metal_percentage=metal
        )
        tech_bin_ids.append(bin2.id)
        bin_count += 1
        # 3. Old timestamp (simulate 'No Signal')
        lat, lon = generate_random_location(center_lat, center_lon, radius_km)
        organic, plastic, metal = generate_waste_composition()
        bin3 = Bin.objects.create(
            bin_id=f"BIN{bin_count+1:03d}",
            fill_level=60,
            latitude=lat,
            longitude=lon,
            organic_percentage=organic,
            plastic_percentage=plastic,
            metal_percentage=metal
        )
        tech_bin_ids.append(bin3.id)
        bin_count += 1
        # 4. fill_level=-999 (simulate 'Sensor Error' or 'Poor Data Format')
        lat, lon = generate_random_location(center_lat, center_lon, radius_km)
        organic, plastic, metal = generate_waste_composition()
        bin4 = Bin.objects.create(
            bin_id=f"BIN{bin_count+1:03d}",
            fill_level=-999,
            latitude=lat,
            longitude=lon,
            organic_percentage=organic,
            plastic_percentage=plastic,
            metal_percentage=metal
        )
        tech_bin_ids.append(bin4.id)
        bin_count += 1
        # 5. fill_level=9999 (simulate '404' or 'Unreachable')
        lat, lon = generate_random_location(center_lat, center_lon, radius_km)
        organic, plastic, metal = generate_waste_composition()
        bin5 = Bin.objects.create(
            bin_id=f"BIN{bin_count+1:03d}",
            fill_level=9999,
            latitude=lat,
            longitude=lon,
            organic_percentage=organic,
            plastic_percentage=plastic,
            metal_percentage=metal
        )
        tech_bin_ids.append(bin5.id)
        bin_count += 1

        # Set the last_updated for the 'No Signal' bin (bin3) to a very old date
        from django.utils import timezone
        import datetime
        old_time = timezone.now() - datetime.timedelta(days=2)  # 2 days ago
        bin3.last_updated = old_time
        bin3.save(update_fields=["last_updated"])

        self.stdout.write(f'Successfully seeded {bin_count} bins with specified fill level distribution and technical support cases!')

if __name__ == '__main__':
    Command().handle() 