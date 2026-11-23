"""Permissions of the reviews app."""
from rest_framework.permissions import BasePermission


class IsReviewer(BasePermission):
    """Only the creator of a review may change or delete it."""

    message = "You can only change your own reviews."

    def has_object_permission(self, request, view, obj):
        """Allow access only for the reviewer."""
        return obj.reviewer == request.user
