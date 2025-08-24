from django.db import models
from django.core.validators import RegexValidator

class Role(models.Model):
    ROLE_CHOICES = [
        ('ADMIN', 'Administrator'),
        ('MANAGER', 'Manager'),
        ('DRIVER', 'Driver'),
        ('OPERATOR', 'Operator'),
        ('VIEWER', 'Viewer'),
    ]
    
    name = models.CharField(max_length=20, choices=ROLE_CHOICES, unique=True)
    description = models.TextField(blank=True)
    permissions = models.JSONField(default=dict, help_text="JSON object containing permissions")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.get_name_display()
    
    class Meta:
        ordering = ['name']

class Bin(models.Model):
    bin_id = models.CharField(max_length=50, unique=True)
    fill_level = models.FloatField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    organic_percentage = models.FloatField()
    plastic_percentage = models.FloatField()
    metal_percentage = models.FloatField()
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Bin {self.bin_id}"

    def get_status(self):
        if self.fill_level > 70:
            return "full"
        elif self.fill_level < 30:
            return "empty"
        return "moderate"

    def get_marker_color(self):
        if self.fill_level > 70:
            return "red"
        elif self.fill_level < 30:
            return "green"
        return "orange" 

class DumpingSpot(models.Model):
    spot_id = models.CharField(max_length=50, unique=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    total_capacity = models.FloatField(help_text="Total capacity in arbitrary units, e.g., volume or weight")
    organic_content = models.FloatField(default=0.0, help_text="Current organic waste content")
    plastic_content = models.FloatField(default=0.0, help_text="Current plastic waste content")
    metal_content = models.FloatField(default=0.0, help_text="Current metal waste content")

    def __str__(self):
        return f"Dumping Spot {self.spot_id}"
    
    def current_fill_level(self):
        total_content = self.organic_content + self.plastic_content + self.metal_content
        if self.total_capacity == 0:
            return 0.0
        return (total_content / self.total_capacity) * 100

    def organic_percentage(self):
        total_content = self.organic_content + self.plastic_content + self.metal_content
        if total_content == 0:
            return 0.0
        return (self.organic_content / total_content) * 100

    def plastic_percentage(self):
        total_content = self.organic_content + self.plastic_content + self.metal_content
        if total_content == 0:
            return 0.0
        return (self.plastic_content / total_content) * 100

    def metal_percentage(self):
        total_content = self.organic_content + self.plastic_content + self.metal_content
        if total_content == 0:
            return 0.0
        return (self.metal_content / total_content) * 100 

class Truck(models.Model):
    TRUCK_STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("IDLE", "Idle"),
        ("MAINTENANCE", "Maintenance"),
    ]
    truck_id = models.CharField(max_length=50, unique=True)
    driver_name = models.CharField(max_length=100, default="")
    current_latitude = models.FloatField(default=0.0)
    current_longitude = models.FloatField(default=0.0)
    fuel_level = models.FloatField(default=0.0)
    status = models.CharField(max_length=20, choices=TRUCK_STATUS_CHOICES, default="IDLE")
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Truck {self.truck_id}" 