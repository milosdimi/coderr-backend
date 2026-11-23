"""Permissions of the offers app."""
from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsOfferOwnerOrReadOnly(BasePermission):
    """Everyone may read an offer, only its creator may change it."""

    message = "You can only change your own offers."

    def has_object_permission(self, request, view, obj):
        """Allow reading for all, writing only for the offer creator."""
        if request.method in SAFE_METHODS:
            return True
        return obj.user == request.user
