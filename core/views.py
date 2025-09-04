import logging
from rest_framework import status
from rest_framework.decorators import api_view, throttle_classes, permission_classes
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import DatabaseError
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from .models import Bin, DumpingSpot, Truck, Role, SensorData, Camera, CameraImage
from .serializers import (
    BinSerializer, DumpingSpotSerializer, TruckSerializer,
    RoleSerializer, SensorDataSerializer, CameraSerializer, CameraImageSerializer
)

# Set up logging
logger = logging.getLogger(__name__)

User = get_user_model()

# Rate limiting classes
class BinRateThrottle(UserRateThrottle):
    rate = '10000/hour'  # Increased for dashboard access

class AnonBinRateThrottle(AnonRateThrottle):
    rate = '5000/hour'   # Increased for dashboard access

# Special rate limiting for sensor data (higher frequency)
class SensorDataRateThrottle(UserRateThrottle):
    rate = '1000/hour'  # Allow 1000 requests per hour for sensors

class AnonSensorDataRateThrottle(AnonRateThrottle):
    rate = '500/hour'   # Allow 500 requests per hour for anonymous sensors

@api_view(['GET', 'POST'])
@throttle_classes([BinRateThrottle, AnonBinRateThrottle])
@permission_classes([AllowAny])  # Allow unauthenticated access for dashboard
def bin_data(request):
    if request.method == 'GET':
        try:
            bins = Bin.objects.all()
            serializer = BinSerializer(bins, many=True)
            
            # Log the request
            user = request.user if request.user.is_authenticated else 'Anonymous'
            logger.info(f"Bin data retrieved by user: {user}")
            
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error retrieving bin data: {str(e)}")
            return Response(
                {'error': 'Failed to retrieve bin data'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    elif request.method == 'POST':
        try:
            serializer = BinSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                logger.info(f"Bin created: {serializer.instance.bin_id}")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                logger.warning(f"Invalid bin data: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error creating bin: {str(e)}")
            return Response(
                {'error': 'Failed to create bin'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class DumpingSpotViewSet(viewsets.ModelViewSet):
    queryset = DumpingSpot.objects.all()
    serializer_class = DumpingSpotSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save()
        logger.info(f"Dumping spot created: {serializer.instance.spot_id}")
    
    def perform_update(self, serializer):
        serializer.save()
        logger.info(f"Dumping spot updated: {serializer.instance.spot_id}")
    
    def perform_destroy(self, instance):
        spot_id = instance.spot_id
        instance.delete()
        logger.info(f"Dumping spot deleted: {spot_id}")

class TruckViewSet(viewsets.ModelViewSet):
    queryset = Truck.objects.all()
    serializer_class = TruckSerializer
    
    def get_permissions(self):
        """
        Allow unauthenticated access for GET requests (dashboard access)
        Require authentication for POST, PUT, DELETE operations
        """
        if self.action in ['list', 'retrieve']:
            return []  # No permission required for read operations
        return [IsAuthenticated()]  # Authentication required for create/update/delete operations
    
    def perform_create(self, serializer):
        serializer.save()
        logger.info(f"Truck created: {serializer.instance.truck_id}")
    
    def perform_update(self, serializer):
        serializer.save()
        logger.info(f"Truck updated: {serializer.instance.truck_id}")
    
    def perform_destroy(self, instance):
        truck_id = instance.truck_id
        instance.delete()
        logger.info(f"Truck deleted: {truck_id}")

class BinViewSet(viewsets.ModelViewSet):
    queryset = Bin.objects.all()
    serializer_class = BinSerializer
    
    def get_permissions(self):
        """
        Allow unauthenticated access for GET requests (dashboard access)
        Require authentication for POST, PUT, DELETE operations
        """
        if self.action in ['list', 'retrieve']:
            return []  # No permission required for read operations
        return [IsAuthenticated()]  # Authentication required for create/update/delete operations
    
    def perform_create(self, serializer):
        serializer.save()
        logger.info(f"Bin created: {serializer.instance.bin_id}")
    
    def perform_update(self, serializer):
        serializer.save()
        logger.info(f"Bin updated: {serializer.instance.bin_id}")
    
    def perform_destroy(self, instance):
        bin_id = instance.bin_id
        instance.delete()
        logger.info(f"Bin deleted: {bin_id}")

class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save()
        logger.info(f"Role created: {serializer.instance.name}")
    
    def perform_update(self, serializer):
        serializer.save()
        logger.info(f"Role updated: {serializer.instance.name}")
    
    def perform_destroy(self, instance):
        role_name = instance.name
        instance.delete()
        logger.info(f"Role deleted: {role_name}")

class SensorDataViewSet(viewsets.ModelViewSet):
    """
    ViewSet for real-time sensor data from ESP32 devices
    """
    queryset = SensorData.objects.all()
    serializer_class = SensorDataSerializer
    throttle_classes = [SensorDataRateThrottle, AnonSensorDataRateThrottle]
    
    def get_permissions(self):
        """
        Allow unauthenticated access for GET requests (dashboard access)
        Allow unauthenticated access for POST requests (sensor data ingestion)
        Require authentication for PUT, DELETE operations
        """
        if self.action in ['list', 'retrieve', 'create']:
            return []  # No permission required for read and create operations
        return [IsAuthenticated()]  # Authentication required for update/delete operations

    def perform_create(self, serializer):
        """Handle sensor data creation with special logic"""
        # Extract sensor data
        sensor_data = serializer.validated_data
        sensor_id = sensor_data.get('sensor_id')
        bin_id = sensor_data.get('bin_id')
        
        # Log the sensor data reception
        logger.info(f"📡 Sensor data received from {sensor_id} for bin {bin_id}: "
                   f"Fill level: {sensor_data.get('fill_level')}%, "
                   f"Location: ({sensor_data.get('latitude')}, {sensor_data.get('longitude')})")
        
        # Save the sensor data
        serializer.save()
        
        # Update the associated bin if it exists
        try:
            bin_instance = Bin.objects.get(bin_id=bin_id)
            bin_instance.fill_level = sensor_data.get('fill_level')
            bin_instance.latitude = sensor_data.get('latitude')
            bin_instance.longitude = sensor_data.get('longitude')
            bin_instance.organic_percentage = sensor_data.get('organic_percentage')
            bin_instance.plastic_percentage = sensor_data.get('plastic_percentage')
            bin_instance.metal_percentage = sensor_data.get('metal_percentage')
            bin_instance.save()
            
            logger.info(f"✅ Bin {bin_id} updated with sensor data from {sensor_id}")
            
        except Bin.DoesNotExist:
            logger.warning(f"⚠️ Bin {bin_id} not found. Sensor data saved but bin not updated.")
        except Exception as e:
            logger.error(f"❌ Error updating bin {bin_id}: {str(e)}")

    def perform_update(self, serializer):
        serializer.save()
        sensor_id = serializer.instance.sensor_id
        logger.info(f"Sensor data updated: {sensor_id} by user: {self.request.user}")

    def perform_destroy(self, instance):
        sensor_id = instance.sensor_id
        instance.delete()
        logger.info(f"Sensor data deleted: {sensor_id} by user: {self.request.user}")

    def get_queryset(self):
        """Custom queryset with filtering options"""
        queryset = SensorData.objects.all()
        
        # Filter by sensor ID
        sensor_id = self.request.query_params.get('sensor_id', None)
        if sensor_id:
            queryset = queryset.filter(sensor_id=sensor_id)
        
        # Filter by bin ID
        bin_id = self.request.query_params.get('bin_id', None)
        if bin_id:
            queryset = queryset.filter(bin_id=bin_id)
        
        # Filter by sensor status
        status = self.request.query_params.get('status', None)
        if status:
            queryset = queryset.filter(sensor_status=status)
        
        # Filter by recent data (last 24 hours)
        recent = self.request.query_params.get('recent', None)
        if recent == 'true':
            from django.utils import timezone
            from datetime import timedelta
            yesterday = timezone.now() - timedelta(hours=24)
            queryset = queryset.filter(timestamp__gte=yesterday)
        
        return queryset.order_by('-timestamp') 

class CameraViewSet(viewsets.ModelViewSet):
    """ViewSet for Camera management"""
    queryset = Camera.objects.all()
    serializer_class = CameraSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]
    
    def get_permissions(self):
        """Allow unauthenticated access for GET operations"""
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return super().get_permissions()
    
    def get_queryset(self):
        """Filter cameras by status if requested"""
        queryset = Camera.objects.all()
        status = self.request.query_params.get('status', None)
        if status:
            queryset = queryset.filter(status=status)
        return queryset

class CameraImageViewSet(viewsets.ModelViewSet):
    """ViewSet for CameraImage management"""
    queryset = CameraImage.objects.all()
    serializer_class = CameraImageSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]
    
    def get_permissions(self):
        """Allow unauthenticated access for image upload and viewing"""
        if self.action in ['list', 'retrieve', 'create']:
            return [AllowAny()]
        return super().get_permissions()
    
    def get_queryset(self):
        """Filter images by various parameters"""
        queryset = CameraImage.objects.all()
        
        # Filter by camera
        camera_id = self.request.query_params.get('camera_id', None)
        if camera_id:
            queryset = queryset.filter(camera__camera_id=camera_id)
        
        # Filter by analysis type
        analysis_type = self.request.query_params.get('analysis_type', None)
        if analysis_type:
            queryset = queryset.filter(analysis_type=analysis_type)
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from', None)
        if date_from:
            try:
                from datetime import datetime
                date_obj = datetime.strptime(date_from, '%Y-%m-%d')
                queryset = queryset.filter(created_at__date__gte=date_obj.date())
            except ValueError:
                pass
        
        date_to = self.request.query_params.get('date_to', None)
        if date_to:
            try:
                from datetime import datetime
                date_obj = datetime.strptime(date_to, '%Y-%m-%d')
                queryset = queryset.filter(created_at__date__lte=date_obj.date())
            except ValueError:
                pass
        
        # Filter by analyzed status
        is_analyzed = self.request.query_params.get('is_analyzed', None)
        if is_analyzed is not None:
            is_analyzed_bool = is_analyzed.lower() == 'true'
            queryset = queryset.filter(is_analyzed=is_analyzed_bool)
        
        return queryset
    
    def perform_create(self, serializer):
        """Handle image upload and processing"""
        # Save the image
        image_instance = serializer.save()
        
        # Log the upload
        print(f"📸 New image uploaded: {image_instance.image.name}")
        print(f"📊 Image size: {image_instance.get_file_size_mb()} MB")
        print(f"📅 Upload time: {image_instance.created_at}")
        
        # TODO: Add image analysis processing here
        # This could include:
        # - Waste classification using AI
        # - Object detection
        # - Quality assessment
        
        return image_instance 