"""Permissions of the orders app."""
from rest_framework.permissions import BasePermission


class IsOrderBusinessUser(BasePermission):
    """Only the business user of an order may change it."""

    message = "Only the business user of this order can update it."

    def has_object_permission(self, request, view, obj):
        """Allow access only for the business user of the order."""
        return obj.business_user == request.user
