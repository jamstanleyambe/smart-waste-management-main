from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import user_management
 
# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'bins', views.BinViewSet)
router.register(r'trucks', views.TruckViewSet)
router.register(r'dumping-spots', views.DumpingSpotViewSet)
router.register(r'roles', views.RoleViewSet)
router.register(r'sensor-data', views.SensorDataViewSet)
router.register(r'cameras', views.CameraViewSet)
router.register(r'camera-images', views.CameraImageViewSet)

# Admin endpoints
# router.register(r'roles', views.RoleViewSet, basename='role')  # Temporarily disabled to fix admin error

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('bin-data/', views.bin_data, name='bin_data'),
    path('', include(router.urls)),
    
    # User Management URLs
    path('user-management/', user_management.user_dashboard, name='user_dashboard'),
    path('user-management/activity-log/', user_management.user_activity_log, name='user_activity_log'),
    path('user-management/toggle-status/<int:user_id>/', user_management.toggle_user_status, name='toggle_user_status'),
    path('user-management/reset-password/<int:user_id>/', user_management.reset_user_password, name='reset_user_password'),
    path('user-management/unlock-account/<int:user_id>/', user_management.unlock_user_account, name='unlock_user_account'),
    path('user-management/clear-ip-block/', user_management.clear_ip_block, name='clear_ip_block'),
] 