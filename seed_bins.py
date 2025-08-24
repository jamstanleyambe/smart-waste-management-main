import os
import django
import random
import math

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
    
    return organic, plastic, metal

def seed_bins():
    # Center coordinates for Douala 5
    center_lat = 4.0511
    center_lon = 9.7679
    radius_km = 5.0  # Increased to 5km radius
    
    # Clear existing bins
    Bin.objects.all().delete()
    
    # Create 25 bins with random fill levels between 0 and 100
    bin_distributions = [
        (25, 0, 100),  # 25 bins with fill levels between 0% and 100%
    ]
    
    bin_count = 0
    for num_bins, min_fill, max_fill in bin_distributions:
        for i in range(num_bins):
            lat, lon = generate_random_location(center_lat, center_lon, radius_km)
            
            # Generate waste composition
            organic, plastic, metal = generate_waste_composition()
            
            # Generate fill level within the specified range
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
    
    # Add 5 more bins with 100% fill level
    for i in range(5):
        lat, lon = generate_random_location(center_lat, center_lon, radius_km)
        organic, plastic, metal = generate_waste_composition()
        Bin.objects.create(
            bin_id=f"BIN{bin_count+1:03d}",
            fill_level=100.0,
            latitude=lat,
            longitude=lon,
            organic_percentage=organic,
            plastic_percentage=plastic,
            metal_percentage=metal
        )
        bin_count += 1
    
    print(f"Successfully seeded {bin_count} bins with specified fill level and waste composition distribution!")

if __name__ == '__main__':
    seed_bins() 