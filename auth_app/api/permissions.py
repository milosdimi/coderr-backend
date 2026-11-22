"""Permissions of the auth app."""
from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsProfileOwnerOrReadOnly(BasePermission):
    """Everyone may read a profile, only its owner may change it."""

    message = "You can only edit your own profile."

    def has_object_permission(self, request, view, obj):
        """Allow reading for all, writing only for the profile owner."""
        if request.method in SAFE_METHODS:
            return True
        return obj.user == request.user
