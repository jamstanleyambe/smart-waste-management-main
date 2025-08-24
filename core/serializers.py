from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Bin, DumpingSpot, Truck, Role

User = get_user_model()

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'permissions', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class BinSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    marker_color = serializers.SerializerMethodField()

    class Meta:
        model = Bin
        fields = ['id', 'bin_id', 'fill_level', 'latitude', 'longitude',
                 'organic_percentage', 'plastic_percentage', 'metal_percentage',
                 'last_updated', 'status', 'marker_color']

    def get_status(self, obj):
        return obj.get_status()

    def get_marker_color(self, obj):
        return obj.get_marker_color()

    def validate(self, data):
        total_percentage = (data.get('organic_percentage', 0) +
                          data.get('plastic_percentage', 0) +
                          data.get('metal_percentage', 0))
        if abs(total_percentage - 100) > 0.01:  # Allow for small floating-point errors
            raise serializers.ValidationError(
                "The sum of organic, plastic, and metal percentages must equal 100%"
            )
        return data 

class DumpingSpotSerializer(serializers.ModelSerializer):
    current_fill_level = serializers.SerializerMethodField()
    organic_percentage = serializers.SerializerMethodField()
    plastic_percentage = serializers.SerializerMethodField()
    metal_percentage = serializers.SerializerMethodField()

    class Meta:
        model = DumpingSpot
        fields = ['id', 'spot_id', 'latitude', 'longitude', 'total_capacity',
                  'organic_content', 'plastic_content', 'metal_content',
                  'current_fill_level', 'organic_percentage', 'plastic_percentage', 'metal_percentage']

    def get_current_fill_level(self, obj):
        return obj.current_fill_level()

    def get_organic_percentage(self, obj):
        return obj.organic_percentage()
    
    def get_plastic_percentage(self, obj):
        return obj.plastic_percentage()

    def get_metal_percentage(self, obj):
        return obj.metal_percentage() 

class TruckSerializer(serializers.ModelSerializer):
    class Meta:
        model = Truck
        fields = ['id', 'truck_id', 'driver_name', 'current_latitude', 'current_longitude', 'fuel_level', 'status', 'last_updated'] 