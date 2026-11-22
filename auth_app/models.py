from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    """Extra data for a user: account type and public profile fields.

    Name, email and username are stored in Django's User model.
    Text fields default to an empty string, never null.
    """

    CUSTOMER = 'customer'
    BUSINESS = 'business'
    TYPE_CHOICES = [
        (CUSTOMER, 'Customer'),
        (BUSINESS, 'Business'),
    ]

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='profile'
    )
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    file = models.ImageField(
        upload_to='profile_pictures/', blank=True, null=True
    )
    location = models.CharField(max_length=255, blank=True, default='')
    tel = models.CharField(max_length=50, blank=True, default='')
    description = models.TextField(blank=True, default='')
    working_hours = models.CharField(max_length=100, blank=True, default='')
    uploaded_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'User profile'
        verbose_name_plural = 'User profiles'
        ordering = ['user__username']

    def __str__(self):
        return f'{self.user.username} ({self.type})'
