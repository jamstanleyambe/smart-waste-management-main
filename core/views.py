import logging
from rest_framework import status
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import DatabaseError
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from .models import Bin, DumpingSpot, Truck, Role
from .serializers import (
    BinSerializer, DumpingSpotSerializer, TruckSerializer,
    RoleSerializer
)

# Set up logging
logger = logging.getLogger(__name__)

User = get_user_model()

# Rate limiting classes
class BinRateThrottle(UserRateThrottle):
    rate = '100/hour'

class AnonBinRateThrottle(AnonRateThrottle):
    rate = '20/hour'

@api_view(['GET', 'POST'])
@throttle_classes([BinRateThrottle, AnonBinRateThrottle])
def bin_data(request):
    try:
        if request.method == 'GET':
            bins = Bin.objects.all()
            serializer = BinSerializer(bins, many=True)
            user_info = request.user.username if request.user.is_authenticated else 'Anonymous'
            logger.info(f"Bin data retrieved by user: {user_info}")
            return Response(serializer.data)

        elif request.method == 'POST':
            serializer = BinSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                user_info = request.user.username if request.user.is_authenticated else 'Anonymous'
                logger.info(f"New bin created: {serializer.data.get('bin_id', 'Unknown')} by user: {user_info}")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            user_info = request.user.username if request.user.is_authenticated else 'Anonymous'
            logger.warning(f"Invalid bin data: {serializer.errors} by user: {user_info}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
    except DatabaseError as e:
        logger.error(f"Database error in bin_data: {str(e)}")
        return Response(
            {'error': 'Database error occurred'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        logger.error(f"Unexpected error in bin_data: {str(e)}")
        return Response(
            {'error': 'An unexpected error occurred'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

class DumpingSpotViewSet(viewsets.ModelViewSet):
    queryset = DumpingSpot.objects.all()
    serializer_class = DumpingSpotSerializer
    throttle_classes = [UserRateThrottle]
    
    def get_permissions(self):
        """
        Allow unauthenticated access for GET requests (dashboard access)
        Require authentication for POST, PUT, DELETE operations
        """
        if self.action in ['list', 'retrieve']:
            return []  # No permission required for read operations
        return [IsAuthenticated()]  # Authentication required for write operations

    def perform_create(self, serializer):
        serializer.save()
        user_info = self.request.user.username if self.request.user.is_authenticated else 'Anonymous'
        logger.info(f"Dumping spot created: {serializer.instance.spot_id} by user: {user_info}")

    def perform_update(self, serializer):
        serializer.save()
        user_info = self.request.user.username if self.request.user.is_authenticated else 'Anonymous'
        logger.info(f"Dumping spot updated: {serializer.instance.spot_id} by user: {user_info}")

    def perform_destroy(self, instance):
        spot_id = instance.spot_id
        instance.delete()
        user_info = self.request.user.username if self.request.user.is_authenticated else 'Anonymous'
        logger.info(f"Dumping spot deleted: {spot_id} by user: {user_info}")

class TruckViewSet(viewsets.ModelViewSet):
    queryset = Truck.objects.all()
    serializer_class = TruckSerializer
    throttle_classes = [UserRateThrottle]
    
    def get_permissions(self):
        """
        Allow unauthenticated access for GET requests (dashboard access)
        Require authentication for POST, PUT, DELETE operations
        """
        if self.action in ['list', 'retrieve']:
            return []  # No permission required for read operations
        return [IsAuthenticated()]  # Authentication required for write operations

    def perform_create(self, serializer):
        serializer.save()
        user_info = self.request.user.username if self.request.user.is_authenticated else 'Anonymous'
        logger.info(f"Truck created: {serializer.instance.truck_id} by user: {user_info}")

    def perform_update(self, serializer):
        serializer.save()
        user_info = self.request.user.username if self.request.user.is_authenticated else 'Anonymous'
        logger.info(f"Truck updated: {serializer.instance.truck_id} by user: {user_info}")

    def perform_destroy(self, instance):
        truck_id = instance.truck_id
        instance.delete()
        user_info = self.request.user.username if self.request.user.is_authenticated else 'Anonymous'
        logger.info(f"Truck deleted: {truck_id} by user: {user_info}")

class BinViewSet(viewsets.ModelViewSet):
    queryset = Bin.objects.all()
    serializer_class = BinSerializer
    throttle_classes = [UserRateThrottle]
    
    def get_permissions(self):
        """
        Allow unauthenticated access for GET requests (dashboard access)
        Require authentication for POST, PUT, DELETE operations
        """
        if self.action in ['list', 'retrieve']:
            return []  # No permission required for read operations
        return [IsAuthenticated()]  # Authentication required for write operations

    def perform_create(self, serializer):
        serializer.save()
        user_info = self.request.user.username if self.request.user.is_authenticated else 'Anonymous'
        logger.info(f"Bin created: {serializer.instance.bin_id} by user: {user_info}")

    def perform_update(self, serializer):
        serializer.save()
        user_info = self.request.user.username if self.request.user.is_authenticated else 'Anonymous'
        logger.info(f"Bin updated: {serializer.instance.bin_id} by user: {user_info}")

    def perform_destroy(self, instance):
        bin_id = instance.bin_id
        instance.delete()
        user_info = self.request.user.username if self.request.user.is_authenticated else 'Anonymous'
        logger.info(f"Bin deleted: {bin_id} by user: {user_info}")

class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    throttle_classes = [UserRateThrottle]

    def perform_create(self, serializer):
        serializer.save()
        logger.info(f"Role created: {serializer.instance.name} by user: {self.request.user}")

    def perform_update(self, serializer):
        serializer.save()
        logger.info(f"Role updated: {serializer.instance.name} by user: {self.request.user}")

    def perform_destroy(self, instance):
        role_name = instance.name
        instance.delete()
        logger.info(f"Role deleted: {role_name} by user: {self.request.user}") 