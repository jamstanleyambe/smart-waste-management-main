from django.contrib import admin
from .models import Bin
 
@admin.register(Bin)
class BinAdmin(admin.ModelAdmin):
    list_display = ('bin_id', 'fill_level', 'latitude', 'longitude', 'get_status', 'last_updated')
    list_filter = ('fill_level',)
    search_fields = ('bin_id',) 