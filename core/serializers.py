from rest_framework import serializers
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from .models import Bin, DumpingSpot, Truck, Role, SensorData, Camera, CameraImage
from django.utils import timezone

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

    def validate_name(self, value):
        """Validate role name"""
        if len(value) < 2:
            raise serializers.ValidationError("Role name must be at least 2 characters long")
        return value.upper()

class BinSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bin
        fields = '__all__'
        read_only_fields = ['last_updated']

    def validate(self, data):
        """Validate that percentages sum to 100%"""
        organic = data.get('organic_percentage', 0)
        plastic = data.get('plastic_percentage', 0)
        metal = data.get('metal_percentage', 0)
        
        total = organic + plastic + metal
        if abs(total - 100.0) > 0.01:  # Allow small floating point errors
            raise serializers.ValidationError(
                f'Percentages must sum to 100%. Current sum: {total:.2f}%'
            )
        return data

    def validate_fill_level(self, value):
        """Validate fill level"""
        if value < 0 or value > 100:
            raise serializers.ValidationError("Fill level must be between 0 and 100")
        return value

    def validate_latitude(self, value):
        """Validate latitude"""
        if value < -90 or value > 90:
            raise serializers.ValidationError("Latitude must be between -90 and 90")
        return value

    def validate_longitude(self, value):
        """Validate longitude"""
        if value < -180 or value > 180:
            raise serializers.ValidationError("Longitude must be between -180 and 180")
        return value

class DumpingSpotSerializer(serializers.ModelSerializer):
    class Meta:
        model = DumpingSpot
        fields = '__all__'
        read_only_fields = ['last_updated']

    def validate_latitude(self, value):
        """Validate latitude"""
        if value < -90 or value > 90:
            raise serializers.ValidationError("Latitude must be between -90 and 90")
        return value

    def validate_longitude(self, value):
        """Validate longitude"""
        if value < -180 or value > 180:
            raise serializers.ValidationError("Longitude must be between -180 and 180")
        return value

    def validate_total_capacity(self, value):
        """Validate total capacity"""
        if value <= 0:
            raise serializers.ValidationError("Total capacity must be positive")
        return value

class TruckSerializer(serializers.ModelSerializer):
    class Meta:
        model = Truck
        fields = '__all__'
        read_only_fields = ['last_updated']

    def validate_latitude(self, value):
        """Validate latitude"""
        if value < -90 or value > 90:
            raise serializers.ValidationError("Latitude must be between -90 and 90")
        return value

    def validate_longitude(self, value):
        """Validate longitude"""
        if value < -180 or value > 180:
            raise serializers.ValidationError("Longitude must be between -180 and 180")
        return value

    def validate_fuel_level(self, value):
        """Validate fuel level"""
        if value < 0 or value > 100:
            raise serializers.ValidationError("Fuel level must be between 0 and 100")
        return value

    def validate_driver_name(self, value):
        """Validate driver name"""
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Driver name must be at least 2 characters long")
        return value.strip()

class SensorDataSerializer(serializers.ModelSerializer):
    """
    Serializer for real-time sensor data from ESP32 devices
    """
    class Meta:
        model = SensorData
        fields = '__all__'
        read_only_fields = ['timestamp', 'last_updated']

    def validate(self, data):
        """Validate that percentages sum to 100%"""
        organic = data.get('organic_percentage', 0)
        plastic = data.get('plastic_percentage', 0)
        metal = data.get('metal_percentage', 0)
        
        total = organic + plastic + metal
        if abs(total - 100.0) > 0.01:  # Allow small floating point errors
            raise serializers.ValidationError(
                f'Percentages must sum to 100%. Current sum: {total:.2f}%'
            )
        return data

    def validate_fill_level(self, value):
        """Validate fill level"""
        if value < 0 or value > 100:
            raise serializers.ValidationError("Fill level must be between 0 and 100")
        return value

    def validate_latitude(self, value):
        """Validate latitude"""
        if value < -90 or value > 90:
            raise serializers.ValidationError("Latitude must be between -90 and 90")
        return value

    def validate_longitude(self, value):
        """Validate longitude"""
        if value < -180 or value > 180:
            raise serializers.ValidationError("Longitude must be between -180 and 180")
        return value

    def validate_battery_level(self, value):
        """Validate battery level"""
        if value is not None and (value < 0 or value > 100):
            raise serializers.ValidationError("Battery level must be between 0 and 100")
        return value

    def validate_signal_strength(self, value):
        """Validate signal strength (typically negative dBm values)"""
        if value is not None and value > 0:
            raise serializers.ValidationError("Signal strength should typically be negative (dBm)")
        return value

    def to_representation(self, instance):
        """Custom representation with additional computed fields"""
        data = super().to_representation(instance)
        data['fill_status'] = instance.get_fill_status()
        data['sensor_health'] = instance.get_sensor_health()
        data['is_recent'] = instance.is_recent()
        return data 

class CameraSerializer(serializers.ModelSerializer):
    """Serializer for Camera model"""
    status_color = serializers.ReadOnlyField(source='get_status_color')
    total_images = serializers.SerializerMethodField()
    last_image_date = serializers.SerializerMethodField()
    
    class Meta:
        model = Camera
        fields = [
            'id', 'camera_id', 'name', 'camera_type', 'location', 'status',
            'status_color', 'ip_address', 'rtsp_url', 'last_maintenance',
            'created_at', 'updated_at', 'total_images', 'last_image_date'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_total_images(self, obj):
        """Get total number of images from this camera"""
        return obj.images.count()
    
    def get_last_image_date(self, obj):
        """Get date of last image from this camera"""
        last_image = obj.images.order_by('-created_at').first()
        return last_image.created_at if last_image else None

class CameraImageSerializer(serializers.ModelSerializer):
    """Serializer for CameraImage model"""
    camera_name = serializers.ReadOnlyField(source='camera.name')
    camera_type = serializers.ReadOnlyField(source='camera.camera_type')
    image_url = serializers.ReadOnlyField(source='get_image_url')
    thumbnail_url = serializers.ReadOnlyField(source='get_thumbnail_url')
    file_size_mb = serializers.ReadOnlyField(source='get_file_size_mb')
    dimensions = serializers.ReadOnlyField(source='get_dimensions')
    
    class Meta:
        model = CameraImage
        fields = [
            'id', 'camera', 'camera_name', 'camera_type', 'image', 'image_url',
            'thumbnail_url', 'analysis_type', 'confidence_score', 'detected_objects',
            'analysis_result', 'metadata', 'is_analyzed', 'created_at',
            'file_size_mb', 'dimensions'
        ]
        read_only_fields = ['created_at', 'thumbnail', 'image_url', 'thumbnail_url']
        extra_kwargs = {
            'camera': {'required': False}  # Make camera field optional for uploads
        }
    
    def create(self, validated_data):
        """Override create to handle image upload"""
        # Extract metadata from request headers if available
        request = self.context.get('request')
        if request:
            # Get camera ID from header
            camera_id = request.headers.get('X-Camera-ID')
            if camera_id:
                try:
                    camera = Camera.objects.get(camera_id=camera_id)
                    validated_data['camera'] = camera
                except Camera.DoesNotExist:
                    # Create default camera if it doesn't exist
                    camera = Camera.objects.create(
                        camera_id=camera_id,
                        name=f"Camera {camera_id}",
                        location="Smart Waste Bin Area",
                        camera_type='ESP32_CAM'
                    )
                    validated_data['camera'] = camera
            
            # Extract other metadata
            capture_time = request.headers.get('X-Capture-Time')
            if capture_time:
                validated_data['metadata'] = {
                    'capture_time': capture_time,
                    'upload_time': timezone.now().isoformat(),
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                    'remote_addr': request.META.get('REMOTE_ADDR', ''),
                }
        
        return super().create(validated_data) 