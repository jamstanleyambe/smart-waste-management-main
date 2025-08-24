from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.contrib.auth import get_user_model
from .models import Bin, DumpingSpot, Truck, Role
from .serializers import (
    BinSerializer, DumpingSpotSerializer, TruckSerializer,
    RoleSerializer
)

User = get_user_model()

@api_view(['GET', 'POST'])
def bin_data(request):
    if request.method == 'GET':
        bins = Bin.objects.all()
        serializer = BinSerializer(bins, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = BinSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DumpingSpotViewSet(viewsets.ModelViewSet):
    queryset = DumpingSpot.objects.all()
    serializer_class = DumpingSpotSerializer

class TruckViewSet(viewsets.ModelViewSet):
    queryset = Truck.objects.all()
    serializer_class = TruckSerializer

class BinViewSet(viewsets.ModelViewSet):
    queryset = Bin.objects.all()
    serializer_class = BinSerializer

class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated, IsAdminUser] 