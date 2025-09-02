from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.contrib.admin import AdminSite
from django.contrib.auth import get_user_model
from .models import Bin, DumpingSpot, Truck, Role

User = get_user_model()

class WasteManagementAdminSite(AdminSite):
    site_header = "Smart Waste Management Admin"
    site_title = "Waste Management Admin"
    index_title = "Welcome to Smart Waste Management Administration"
    
    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        
        # Get real data counts
        user_count = User.objects.count()
        active_user_count = User.objects.filter(is_active=True).count()
        bin_count = Bin.objects.count()
        truck_count = Truck.objects.count()
        dumping_spot_count = DumpingSpot.objects.count()
        role_count = Role.objects.count()
        
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
            'role_count': role_count,
            
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
        })
        return super().index(request, extra_context)

# Custom admin site configuration (using default admin site)

# Register models with custom admin site
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at', 'updated_at')
    list_filter = ('name', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('name',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description')
        }),
        ('Permissions', {
            'fields': ('permissions',),
            'description': 'Enter permissions as JSON format'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

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

# Register models with default admin site
admin.site.register(Role, RoleAdmin)
admin.site.register(Bin, BinAdmin)
admin.site.register(DumpingSpot, DumpingSpotAdmin)
admin.site.register(Truck, TruckAdmin)

# Register User model with default admin site
admin.site.register(User, UserAdmin)

# Remove default admin site customization to avoid conflicts
# admin.site.site_header = "Smart Waste Management Admin"
# admin.site.site_title = "Waste Management Admin"
# admin.site.index_title = "Welcome to Smart Waste Management Administration" 