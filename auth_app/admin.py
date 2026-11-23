"""Admin panel registration of the auth app (registration, login, profiles)."""
from django.contrib import admin

from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin list of all user profiles, filterable by type."""

    list_display = ['user', 'type', 'location', 'created_at']
    list_filter = ['type']
    search_fields = ['user__username', 'user__email', 'location']
