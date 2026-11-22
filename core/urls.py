"""
URL configuration for the Coderr backend.

All app routes are included here under the "api/" prefix.
Uploaded media files are served by Django in development mode.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
