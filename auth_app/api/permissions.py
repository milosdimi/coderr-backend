"""Permissions of the auth app.

IsBusinessUser and IsCustomerUser are also used by other apps,
because the profile type belongs to this app.
"""
from rest_framework.permissions import SAFE_METHODS, BasePermission

from auth_app.models import UserProfile


def has_profile_type(user, profile_type):
    """Return True if the user has a profile of the given type."""
    profile = getattr(user, "profile", None)
    return profile is not None and profile.type == profile_type


class IsBusinessUser(BasePermission):
    """Only users with a business profile get access."""

    message = "Only business users can perform this action."

    def has_permission(self, request, view):
        """Check the profile type of the logged in user."""
        return has_profile_type(request.user, UserProfile.BUSINESS)


class IsCustomerUser(BasePermission):
    """Only users with a customer profile get access."""

    message = "Only customer users can perform this action."

    def has_permission(self, request, view):
        """Check the profile type of the logged in user."""
        return has_profile_type(request.user, UserProfile.CUSTOMER)


class IsProfileOwnerOrReadOnly(BasePermission):
    """Everyone may read a profile, only its owner may change it."""

    message = "You can only edit your own profile."

    def has_object_permission(self, request, view, obj):
        """Allow reading for all, writing only for the profile owner."""
        if request.method in SAFE_METHODS:
            return True
        return obj.user == request.user
