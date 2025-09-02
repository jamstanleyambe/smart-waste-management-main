from django.contrib import admin
from django.utils.html import format_html
from .models import Bin, DumpingSpot, Truck, Role

# Custom admin site configuration (using default admin site)

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

# User model is automatically registered by Django, no need to register again

# Remove default admin site customization to avoid conflicts
# admin.site.site_header = "Smart Waste Management Admin"
# admin.site.site_title = "Waste Management Admin"
# admin.site.index_title = "Welcome to Smart Waste Management Administration" 