from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from core.admin import admin_site  # Enable custom admin site

urlpatterns = [
    path('admin/', admin_site.urls),  # Use custom admin site
    # path('admin/', admin.site.urls),  # Default admin site disabled
    path('api/', include('core.urls')),
    path('', TemplateView.as_view(template_name='index.html'), name='index'),
] 