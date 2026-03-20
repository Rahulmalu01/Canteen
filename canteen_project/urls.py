"""
canteen_project/urls.py — Root URL configuration for all 5 apps
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('student/', include('students.urls')),
    path('kitchen/', include('kitchen.urls')),
    path('staff/', include('canteen_staff.urls')),
    path('admin-panel/', include('admin_panel.urls')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
