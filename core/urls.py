"""
URL configuration for the Coderr backend.

All app routes are included here under the "api/" prefix.
Uploaded media files are served by Django in development mode.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('auth_app.api.urls')),
    path('api/', include('offers_app.api.urls')),
    path('api/', include('orders_app.api.urls')),
    path('api/', include('reviews_app.api.urls')),
    path('api/', include('base_info_app.api.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
