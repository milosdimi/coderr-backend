"""Tests for the models of the auth app."""
from django.test import TestCase, override_settings

from auth_app.models import UserProfile

from .helpers import FAST_PASSWORD_HASHERS, create_user


@override_settings(PASSWORD_HASHERS=FAST_PASSWORD_HASHERS)
class UserProfileModelTests(TestCase):
    """String representation of a profile."""

    def test_str_shows_username_and_type(self):
        """The profile is shown as 'username (type)'."""
        user = create_user("max", UserProfile.BUSINESS)
        self.assertEqual(str(user.profile), "max (business)")
