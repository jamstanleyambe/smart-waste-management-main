from rest_framework import serializers
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from .models import Bin, DumpingSpot, Truck, Role

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