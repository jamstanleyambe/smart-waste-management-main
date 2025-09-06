from django.contrib import admin
from django.utils.html import format_html
from django.contrib.admin import AdminSite
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from django.contrib.auth.views import LogoutView
from django.urls import path, reverse
from .models import Bin, DumpingSpot, Truck, SensorData, Camera, CameraImage

User = get_user_model()

class SmartWasteAdminSite(AdminSite):
    site_header = "Smart Waste Management"
    site_title = "Smart Waste Management Admin"
    index_title = "Welcome to Smart Waste Management Administration"
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('logout/', LogoutView.as_view(next_page='/admin/login/'), name='logout'),
        ]
        return custom_urls + urls
    
    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        
        # Get real data counts
        user_count = User.objects.count()
        active_user_count = User.objects.filter(is_active=True).count()
        bin_count = Bin.objects.count()
        truck_count = Truck.objects.count()
        dumping_spot_count = DumpingSpot.objects.count()
        sensor_count = SensorData.objects.count()
        
        # Calculate additional statistics
        from django.db.models import Avg, Count, Q
        from datetime import datetime, timedelta
        
        # Bin statistics
        avg_fill_level = Bin.objects.aggregate(avg_fill=Avg('fill_level'))['avg_fill'] or 0
        full_bins = Bin.objects.filter(fill_level__gte=80).count()
        empty_bins = Bin.objects.filter(fill_level__lte=20).count()
        
        # Truck statistics
        active_trucks = Truck.objects.filter(status='ACTIVE').count()
        idle_trucks = Truck.objects.filter(status='IDLE').count()
        maintenance_trucks = Truck.objects.filter(status='MAINTENANCE').count()
        
        # Dumping spot statistics
        total_capacity = DumpingSpot.objects.aggregate(total=Avg('total_capacity'))['total'] or 0
        
        # Calculate average fill level manually since it's a method
        dumping_spots = DumpingSpot.objects.all()
        total_fill_level = 0
        spot_count = dumping_spots.count()
        for spot in dumping_spots:
            total_fill_level += spot.current_fill_level()
        avg_fill_level_spots = total_fill_level / spot_count if spot_count > 0 else 0
        
        # Sensor statistics
        recent_sensors = SensorData.objects.filter(timestamp__gte=datetime.now() - timedelta(hours=1)).count()
        online_sensors = SensorData.objects.filter(sensor_status='ONLINE').count()
        
        # Recent activity (last 7 days)
        week_ago = datetime.now() - timedelta(days=7)
        recent_bins = Bin.objects.filter(last_updated__gte=week_ago).count()
        recent_trucks = Truck.objects.filter(last_updated__gte=week_ago).count()
        
        extra_context.update({
            'user_count': user_count,
            'active_user_count': active_user_count,
            'bin_count': bin_count,
            'truck_count': truck_count,
            'dumping_spot_count': dumping_spot_count,
            'sensor_count': sensor_count,
            
            # Enhanced statistics
            'avg_fill_level': round(avg_fill_level, 1),
            'full_bins': full_bins,
            'empty_bins': empty_bins,
            'active_trucks': active_trucks,
            'idle_trucks': idle_trucks,
            'maintenance_trucks': maintenance_trucks,
            'total_capacity': round(total_capacity, 1),
            'avg_fill_level_spots': round(avg_fill_level_spots, 1),
            'recent_bins': recent_bins,
            'recent_trucks': recent_trucks,
            'recent_sensors': recent_sensors,
            'online_sensors': online_sensors,
        })
        return super().index(request, extra_context)

# Create custom admin site instance
admin_site = SmartWasteAdminSite(name='smart_waste_admin')

class BinAdmin(admin.ModelAdmin):
    list_display = ('bin_id', 'fill_level', 'latitude', 'longitude', 'get_status', 'get_marker_color', 'last_updated')
    list_filter = ('fill_level', 'last_updated')
    search_fields = ('bin_id',)
    readonly_fields = ('last_updated',)
    ordering = ('bin_id',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('bin_id', 'fill_level')
        }),
        ('Location', {
            'fields': ('latitude', 'longitude')
        }),
        ('Waste Composition', {
            'fields': ('organic_percentage', 'plastic_percentage', 'metal_percentage')
        }),
        ('Timestamps', {
            'fields': ('last_updated',),
            'classes': ('collapse',)
        }),
    )
    
    def get_status(self, obj):
        return obj.get_status()
    get_status.short_description = 'Status'
    
    def get_marker_color(self, obj):
        color = obj.get_marker_color()
        return format_html('<span style="color: {};">●</span> {}', color, color.title())
    get_marker_color.short_description = 'Marker Color'

class DumpingSpotAdmin(admin.ModelAdmin):
    list_display = ('spot_id', 'latitude', 'longitude', 'total_capacity', 'current_fill_level', 'organic_percentage', 'plastic_percentage', 'metal_percentage')
    list_filter = ('total_capacity',)
    search_fields = ('spot_id',)
    ordering = ('spot_id',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('spot_id', 'total_capacity')
        }),
        ('Location', {
            'fields': ('latitude', 'longitude')
        }),
        ('Current Content', {
            'fields': ('organic_content', 'plastic_content', 'metal_content')
            }),
    )
    
    def current_fill_level(self, obj):
        return f"{obj.current_fill_level():.1f}%"
    current_fill_level.short_description = 'Fill Level'
    
    def organic_percentage(self, obj):
        return f"{obj.organic_percentage():.1f}%"
    organic_percentage.short_description = 'Organic %'
    
    def plastic_percentage(self, obj):
        return f"{obj.plastic_percentage():.1f}%"
    plastic_percentage.short_description = 'Plastic %'
    
    def metal_percentage(self, obj):
        return f"{obj.metal_percentage():.1f}%"
    metal_percentage.short_description = 'Metal %'

class TruckAdmin(admin.ModelAdmin):
    list_display = ('truck_id', 'driver_name', 'status', 'fuel_level', 'current_location', 'last_updated')
    list_filter = ('status', 'fuel_level', 'last_updated')
    search_fields = ('truck_id', 'driver_name')
    readonly_fields = ('last_updated',)
    ordering = ('truck_id',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('truck_id', 'driver_name', 'status')
        }),
        ('Location', {
            'fields': ('current_latitude', 'current_longitude')
        }),
        ('Vehicle Information', {
            'fields': ('fuel_level',)
        }),
        ('Timestamps', {
            'fields': ('last_updated',),
            'classes': ('collapse',)
        }),
    )
    
    def current_location(self, obj):
        return f"({obj.current_latitude:.4f}, {obj.current_longitude:.4f})"
    current_location.short_description = 'Current Location'

class SensorDataAdmin(admin.ModelAdmin):
    """
    Admin interface for real-time sensor data from ESP32 devices
    """
    list_display = ('sensor_id', 'bin_id', 'fill_level', 'get_fill_status', 'latitude', 'longitude', 'sensor_status', 'timestamp')
    list_filter = ('sensor_status', 'timestamp', 'bin_id')
    search_fields = ('sensor_id', 'bin_id')
    readonly_fields = ('timestamp', 'last_updated')
    ordering = ('-timestamp',)
    
    fieldsets = (
        ('Sensor Information', {
            'fields': ('sensor_id', 'bin_id', 'sensor_status')
        }),
        ('Real-time Measurements', {
            'fields': ('fill_level', 'latitude', 'longitude')
        }),
        ('Waste Composition', {
            'fields': ('organic_percentage', 'plastic_percentage', 'metal_percentage')
        }),
        ('Sensor Health', {
            'fields': ('battery_level', 'signal_strength', 'temperature', 'humidity'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('timestamp', 'last_updated'),
            'classes': ('collapse',)
        }),
    )
    
    def get_fill_status(self, obj):
        status = obj.get_fill_status()
        if 'Critical' in status:
            color = 'red'
        elif 'High' in status:
            color = 'orange'
        elif 'Moderate' in status:
            color = 'yellow'
        elif 'Low' in status:
            color = 'lightgreen'
        else:
            color = 'green'
        
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, status)
    get_fill_status.short_description = 'Fill Status'
    
    def get_queryset(self, request):
        """Optimize queryset for admin display"""
        return super().get_queryset(request).select_related()
    
    def has_add_permission(self, request):
        """Disable manual addition - sensor data should come from devices"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Allow editing sensor data for maintenance purposes"""
        return True
    
    def has_delete_permission(self, request, obj=None):
        """Allow deletion for data cleanup"""
        return True

@admin.register(Camera)
class CameraAdmin(admin.ModelAdmin):
    """Admin interface for Camera model"""
    list_display = ['camera_id', 'name', 'camera_type', 'location', 'status', 'total_images', 'last_maintenance', 'created_at']
    list_filter = ['camera_type', 'status', 'created_at']
    search_fields = ['camera_id', 'name', 'location']
    readonly_fields = ['created_at', 'updated_at', 'total_images']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('camera_id', 'name', 'camera_type', 'location')
        }),
        ('Status & Configuration', {
            'fields': ('status', 'ip_address', 'rtsp_url')
        }),
        ('Maintenance', {
            'fields': ('last_maintenance',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def total_images(self, obj):
        """Display total number of images"""
        return obj.images.count()
    total_images.short_description = 'Total Images'

@admin.register(CameraImage)
class CameraImageAdmin(admin.ModelAdmin):
    """Admin interface for CameraImage model with enhanced upload capabilities"""
    list_display = ['id', 'camera', 'analysis_type', 'file_size_mb', 'dimensions', 'is_analyzed', 'created_at']
    list_filter = ['camera', 'analysis_type', 'is_analyzed', 'created_at']
    search_fields = ['camera__name', 'camera__camera_id']
    readonly_fields = ['created_at', 'file_size_mb', 'dimensions', 'image_url', 'thumbnail_url', 'image_preview', 'thumbnail_preview']
    ordering = ['-created_at']
    actions = ['bulk_upload_images']
    
    def get_form(self, request, obj=None, **kwargs):
        """Use custom form for better image upload experience"""
        # Only use custom form for bulk upload, not regular add/edit
        if request.path.endswith('/bulk-upload/'):
            from .forms import BulkImageUploadForm
            return BulkImageUploadForm
        return super().get_form(request, obj, **kwargs)
    
    def changelist_view(self, request, extra_context=None):
        """Add bulk upload link to changelist"""
        extra_context = extra_context or {}
        extra_context['bulk_upload_url'] = reverse('admin:core_cameraimage_bulk_upload')
        return super().changelist_view(request, extra_context=extra_context)
    
    fieldsets = (
        ('Image Upload', {
            'fields': ('camera', 'image', 'image_preview'),
            'description': '📸 Upload images directly from your computer. Images will be automatically resized and thumbnails created.'
        }),
        ('Image Information', {
            'fields': ('thumbnail', 'thumbnail_preview', 'analysis_type', 'confidence_score', 'is_analyzed')
        }),
        ('Analysis Results', {
            'fields': ('detected_objects', 'analysis_result', 'metadata'),
            'classes': ('collapse',)
        }),
        ('File Details', {
            'fields': ('file_size_mb', 'dimensions', 'image_url', 'thumbnail_url'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def file_size_mb(self, obj):
        """Display file size in MB"""
        return f"{obj.get_file_size_mb()} MB"
    file_size_mb.short_description = 'File Size'
    
    def dimensions(self, obj):
        """Display image dimensions"""
        return obj.get_dimensions()
    dimensions.short_description = 'Dimensions'
    
    def image_url(self, obj):
        """Display image URL"""
        url = obj.get_image_url()
        if url:
            return f'<a href="{url}" target="_blank">View Image</a>'
        return 'No image'
    image_url.short_description = 'Image URL'
    image_url.allow_tags = True
    
    def thumbnail_url(self, obj):
        """Display thumbnail URL"""
        url = obj.get_thumbnail_url()
        if url:
            return f'<a href="{url}" target="_blank">View Thumbnail</a>'
        return 'No thumbnail'
    thumbnail_url.short_description = 'Thumbnail URL'
    thumbnail_url.allow_tags = True
    
    def image_preview(self, obj):
        """Display image preview in admin"""
        if obj.image:
            url = obj.get_image_url()
            if url:
                return f'<img src="{url}" style="max-width: 300px; max-height: 200px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" />'
        return 'No image uploaded'
    image_preview.short_description = 'Image Preview'
    image_preview.allow_tags = True
    
    def thumbnail_preview(self, obj):
        """Display thumbnail preview in admin"""
        if obj.thumbnail:
            url = obj.get_thumbnail_url()
            if url:
                return f'<img src="{url}" style="max-width: 150px; max-height: 100px; border-radius: 4px; box-shadow: 0 1px 4px rgba(0,0,0,0.1);" />'
        return 'No thumbnail available'
    thumbnail_preview.short_description = 'Thumbnail Preview'
    thumbnail_preview.allow_tags = True
    
    def bulk_upload_images(self, request, queryset):
        """Custom admin action for bulk image upload"""
        from django.http import HttpResponseRedirect
        from django.urls import reverse
        
        # Redirect to the bulk upload page
        return HttpResponseRedirect(reverse('admin:core_cameraimage_bulk_upload'))
    
    bulk_upload_images.short_description = "📸 Bulk Upload Images"
    
    def get_urls(self):
        """Add custom URLs for bulk upload"""
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('bulk-upload/', self.admin_site.admin_view(self.bulk_upload_view), name='core_cameraimage_bulk_upload'),
        ]
        return custom_urls + urls
    
    def bulk_upload_view(self, request):
        """Custom view for bulk image upload"""
        from django.shortcuts import render, redirect
        from django.contrib import messages
        from .forms import BulkImageUploadForm
        
        if request.method == 'POST':
            form = BulkImageUploadForm(request.POST, request.FILES)
            if form.is_valid():
                try:
                    created_images = form.save()
                    messages.success(
                        request, 
                        f"✅ Successfully uploaded {len(created_images)} images! "
                        f"All images have been processed and thumbnails created."
                    )
                    return redirect('admin:core_cameraimage_changelist')
                except Exception as e:
                    messages.error(request, f"❌ Error uploading images: {str(e)}")
        else:
            form = BulkImageUploadForm()
        
        context = {
            'form': form,
            'title': 'Bulk Image Upload',
            'has_permission': True,
            'site_title': self.admin_site.site_title,
            'site_header': self.admin_site.site_header,
        }
        
        return render(request, 'admin/core/cameraimage/bulk_upload.html', context)

# Register models with custom admin site
admin_site.register(Bin, BinAdmin)
admin_site.register(DumpingSpot, DumpingSpotAdmin)
admin_site.register(Truck, TruckAdmin)
admin_site.register(SensorData, SensorDataAdmin)
admin_site.register(Camera, CameraAdmin)
admin_site.register(CameraImage, CameraImageAdmin)

# Register User model for authentication
admin_site.register(User, UserAdmin)

# Customize custom admin site
admin_site.site_header = "Smart Waste Management"
admin_site.site_title = "Smart Waste Management Admin"
admin_site.index_title = "Welcome to Smart Waste Management Administration"
