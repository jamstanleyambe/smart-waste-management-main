from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
 
# Create a router and register our viewsets with it.
router = DefaultRouter()
# Assuming you might eventually convert bin_data to a ViewSet, 
# for now, keep the path for bin_data as is and add dumping spots to router.
# If views.bin_data was a ViewSet, you would register it like this:
# router.register(r'bin-data', views.BinViewSet, basename='bin-data')
router.register(r'dumping-spots', views.DumpingSpotViewSet, basename='dumpingspot')
router.register(r'trucks', views.TruckViewSet, basename='truck')
router.register(r'bin-data', views.BinViewSet, basename='bin')

# Admin endpoints
router.register(r'roles', views.RoleViewSet, basename='role')

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('bin-data/', views.bin_data, name='bin_data'),
    path('', include(router.urls)),
] 