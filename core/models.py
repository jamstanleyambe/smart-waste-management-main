from django.db import models
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError

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
    bin_id = models.CharField(
        max_length=50, 
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[A-Z0-9_-]+$',
                message='Bin ID must contain only uppercase letters, numbers, hyphens, and underscores.'
            )
        ]
    )
    fill_level = models.FloatField(
        validators=[
            MinValueValidator(0.0, message='Fill level cannot be negative'),
            MaxValueValidator(100.0, message='Fill level cannot exceed 100%')
        ]
    )
    latitude = models.FloatField(
        validators=[
            MinValueValidator(-90.0, message='Latitude must be between -90 and 90'),
            MaxValueValidator(90.0, message='Latitude must be between -90 and 90')
        ]
    )
    longitude = models.FloatField(
        validators=[
            MinValueValidator(-180.0, message='Longitude must be between -180 and 180'),
            MaxValueValidator(180.0, message='Longitude must be between -180 and 180')
        ]
    )
    organic_percentage = models.FloatField(
        validators=[
            MinValueValidator(0.0, message='Organic percentage cannot be negative'),
            MaxValueValidator(100.0, message='Organic percentage cannot exceed 100%')
        ]
    )
    plastic_percentage = models.FloatField(
        validators=[
            MinValueValidator(0.0, message='Plastic percentage cannot be negative'),
            MaxValueValidator(100.0, message='Plastic percentage cannot exceed 100%')
        ]
    )
    metal_percentage = models.FloatField(
        validators=[
            MinValueValidator(0.0, message='Metal percentage cannot be negative'),
            MaxValueValidator(100.0, message='Metal percentage cannot exceed 100%')
        ]
    )
    last_updated = models.DateTimeField(auto_now=True)

    def clean(self):
        """Validate that percentages sum to 100%"""
        total_percentage = self.organic_percentage + self.plastic_percentage + self.metal_percentage
        if abs(total_percentage - 100.0) > 0.01:  # Allow small floating point errors
            raise ValidationError(
                f'Percentages must sum to 100%. Current sum: {total_percentage:.2f}%'
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

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

class SensorData(models.Model):
    """
    Real-time sensor data from ESP32 devices
    """
    SENSOR_STATUS_CHOICES = [
        ('ONLINE', 'Online'),
        ('OFFLINE', 'Offline'),
        ('ERROR', 'Error'),
        ('MAINTENANCE', 'Maintenance'),
    ]
    
    # Sensor identification
    sensor_id = models.CharField(max_length=50, help_text="Unique identifier for the sensor device")
    bin_id = models.CharField(max_length=50, help_text="Associated bin ID")
    
    # Real-time measurements
    fill_level = models.FloatField(
        validators=[
            MinValueValidator(0.0, message='Fill level cannot be negative'),
            MaxValueValidator(100.0, message='Fill level cannot exceed 100%')
        ],
        help_text="Current fill level percentage"
    )
    
    # Location data
    latitude = models.FloatField(
        validators=[
            MinValueValidator(-90.0, message='Latitude must be between -90 and 90'),
            MaxValueValidator(90.0, message='Latitude must be between -90 and 90')
        ]
    )
    longitude = models.FloatField(
        validators=[
            MinValueValidator(-180.0, message='Longitude must be between -180 and 180'),
            MaxValueValidator(180.0, message='Longitude must be between -180 and 180')
        ]
    )
    
    # Waste composition (from sensor analysis or estimation)
    organic_percentage = models.FloatField(
        validators=[
            MinValueValidator(0.0, message='Organic percentage cannot be negative'),
            MaxValueValidator(100.0, message='Organic percentage cannot exceed 100%')
        ],
        default=40.0
    )
    plastic_percentage = models.FloatField(
        validators=[
            MinValueValidator(0.0, message='Plastic percentage cannot be negative'),
            MaxValueValidator(100.0, message='Plastic percentage cannot exceed 100%')
        ],
        default=35.0
    )
    metal_percentage = models.FloatField(
        validators=[
            MinValueValidator(0.0, message='Metal percentage cannot be negative'),
            MaxValueValidator(100.0, message='Metal percentage cannot exceed 100%')
        ],
        default=25.0
    )
    
    # Sensor status and metadata
    sensor_status = models.CharField(
        max_length=20, 
        choices=SENSOR_STATUS_CHOICES, 
        default='ONLINE',
        help_text="Current status of the sensor device"
    )
    battery_level = models.FloatField(
        validators=[
            MinValueValidator(0.0, message='Battery level cannot be negative'),
            MaxValueValidator(100.0, message='Battery level cannot exceed 100%')
        ],
        null=True, 
        blank=True,
        help_text="Battery level percentage (if available)"
    )
    signal_strength = models.IntegerField(
        null=True, 
        blank=True,
        help_text="WiFi signal strength in dBm (if available)"
    )
    
    # Timestamps
    timestamp = models.DateTimeField(auto_now_add=True, help_text="When this reading was received")
    last_updated = models.DateTimeField(auto_now=True, help_text="Last time this record was updated")
    
    # Additional sensor data
    temperature = models.FloatField(
        null=True, 
        blank=True,
        help_text="Temperature reading in Celsius (if available)"
    )
    humidity = models.FloatField(
        null=True, 
        blank=True,
        help_text="Humidity reading in percentage (if available)"
    )
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Sensor Data"
        verbose_name_plural = "Sensor Data"
        indexes = [
            models.Index(fields=['sensor_id', 'timestamp']),
            models.Index(fields=['bin_id', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
        # Allow multiple readings from the same sensor, but ensure timestamp uniqueness
        unique_together = [['sensor_id', 'timestamp']]
    
    def clean(self):
        """Validate that percentages sum to 100%"""
        total_percentage = self.organic_percentage + self.plastic_percentage + self.metal_percentage
        if abs(total_percentage - 100.0) > 0.01:  # Allow small floating point errors
            raise ValidationError(
                f'Percentages must sum to 100%. Current sum: {total_percentage:.2f}%'
            )
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Sensor {self.sensor_id} - Bin {self.bin_id} ({self.timestamp})"
    
    def get_fill_status(self):
        """Get human-readable fill status"""
        if self.fill_level > 80:
            return "Critical - Nearly Full"
        elif self.fill_level > 70:
            return "High - Needs Attention"
        elif self.fill_level > 50:
            return "Moderate"
        elif self.fill_level > 20:
            return "Low"
        else:
            return "Empty"
    
    def get_sensor_health(self):
        """Get sensor health status"""
        if self.sensor_status == 'ONLINE' and self.battery_level and self.battery_level > 20:
            return "Healthy"
        elif self.sensor_status == 'ONLINE':
            return "Online"
        elif self.sensor_status == 'OFFLINE':
            return "Offline"
        elif self.sensor_status == 'ERROR':
            return "Error"
        else:
            return "Maintenance"
    
    def is_recent(self, minutes=5):
        """Check if sensor data is recent (within specified minutes)"""
        from django.utils import timezone
        from datetime import timedelta
        return self.timestamp > timezone.now() - timedelta(minutes=minutes) 

class Camera(models.Model):
    """Camera device model for ESP32-CAM and other cameras"""
    CAMERA_TYPES = [
        ('ESP32_CAM', 'ESP32-CAM'),
        ('USB', 'USB Camera'),
        ('IP', 'IP Camera'),
        ('RASPBERRY_PI', 'Raspberry Pi Camera'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('MAINTENANCE', 'Maintenance'),
        ('OFFLINE', 'Offline'),
        ('ERROR', 'Error'),
    ]
    
    camera_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    camera_type = models.CharField(max_length=20, choices=CAMERA_TYPES, default='ESP32_CAM')
    location = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    rtsp_url = models.URLField(null=True, blank=True)
    last_maintenance = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Camera"
        verbose_name_plural = "Cameras"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.camera_id})"
    
    def get_status_color(self):
        """Get color for status display"""
        status_colors = {
            'ACTIVE': 'green',
            'MAINTENANCE': 'orange',
            'OFFLINE': 'red',
            'ERROR': 'darkred',
        }
        return status_colors.get(self.status, 'gray')

class CameraImage(models.Model):
    """Model for storing camera captured images"""
    ANALYSIS_TYPES = [
        ('WASTE_CLASSIFICATION', 'Waste Classification'),
        ('SECURITY', 'Security Monitoring'),
        ('COLLECTION', 'Collection Verification'),
        ('GENERAL', 'General Monitoring'),
    ]
    
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='camera_images/%Y/%m/%d/')
    thumbnail = models.ImageField(upload_to='camera_thumbnails/%Y/%m/%d/', null=True, blank=True)
    analysis_type = models.CharField(max_length=20, choices=ANALYSIS_TYPES, default='GENERAL')
    confidence_score = models.FloatField(null=True, blank=True)
    detected_objects = models.JSONField(default=dict, blank=True)
    analysis_result = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    is_analyzed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Camera Image"
        verbose_name_plural = "Camera Images"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['camera', 'created_at']),
            models.Index(fields=['analysis_type', 'created_at']),
            models.Index(fields=['is_analyzed', 'created_at']),
        ]
    
    def __str__(self):
        return f"Image from {self.camera.name} at {self.created_at}"
    
    def get_image_url(self):
        """Get full image URL"""
        if self.image:
            return self.image.url
        return None
    
    def get_thumbnail_url(self):
        """Get thumbnail URL"""
        if self.thumbnail:
            return self.thumbnail.url
        return self.image.url if self.image else None
    
    def get_file_size_mb(self):
        """Get image file size in MB"""
        if self.image:
            return round(self.image.size / (1024 * 1024), 2)
        return 0
    
    def get_dimensions(self):
        """Get image dimensions"""
        if self.image:
            try:
                from PIL import Image
                with Image.open(self.image.path) as img:
                    return f"{img.width} x {img.height}"
            except:
                return "Unknown"
        return "Unknown"
    
    def save(self, *args, **kwargs):
        """Override save to create thumbnail"""
        super().save(*args, **kwargs)
        if self.image and not self.thumbnail:
            self.create_thumbnail()
    
    def create_thumbnail(self):
        """Create thumbnail from main image"""
        try:
            from PIL import Image
            from io import BytesIO
            from django.core.files import File
            
            # Open the image
            with Image.open(self.image.path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Create thumbnail
                img.thumbnail((300, 300), Image.Resampling.LANCZOS)
                
                # Save thumbnail
                thumb_io = BytesIO()
                img.save(thumb_io, format='JPEG', quality=85)
                thumb_io.seek(0)
                
                # Generate thumbnail filename
                thumb_name = f"thumb_{self.image.name.split('/')[-1]}"
                
                # Save thumbnail
                self.thumbnail.save(thumb_name, File(thumb_io), save=False)
                self.save(update_fields=['thumbnail'])
                
        except Exception as e:
            print(f"Error creating thumbnail: {e}") 