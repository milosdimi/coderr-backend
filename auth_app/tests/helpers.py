"""Shared helpers for the tests of all apps.

Creates users with profiles, offers with three details, request
payloads and small test images.
"""
import io
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image
from rest_framework.test import APITestCase

from auth_app.models import UserProfile
from offers_app.models import Offer, OfferDetail

PASSWORD = "testpass123"
OFFER_TYPES = ["basic", "standard", "premium"]

# Fast password hashing for tests only. PBKDF2 stays in the list so the
# guest users from the data migration can still log in.
FAST_PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]


def create_user(username, profile_type=UserProfile.CUSTOMER):
    """Create a user with a profile of the given type."""
    user = User.objects.create_user(
        username=username, email=f"{username}@mail.de", password=PASSWORD
    )
    UserProfile.objects.create(user=user, type=profile_type)
    return user


def create_offer(user, title="Website", base_price=100, base_days=5):
    """Create an offer with three details; basic is cheapest and fastest."""
    offer = Offer.objects.create(
        user=user, title=title, description=f"{title} description"
    )
    for factor, offer_type in enumerate(OFFER_TYPES, start=1):
        OfferDetail.objects.create(
            offer=offer, title=f"{offer_type} package", revisions=factor,
            delivery_time_in_days=base_days * factor,
            price=base_price * factor, features=["Feature"],
            offer_type=offer_type,
        )
    return offer


def detail_payload(offer_type, **changes):
    """Request data for one offer detail; changes overwrite values."""
    data = {
        "title": f"{offer_type} package", "revisions": 2,
        "delivery_time_in_days": 5, "price": 100.0,
        "features": ["Logo"], "offer_type": offer_type,
    }
    data.update(changes)
    return data


def offer_payload(**changes):
    """Request data for a complete offer; changes overwrite values."""
    data = {
        "title": "Design package", "image": None,
        "description": "Logo and business cards",
        "details": [detail_payload(offer_type) for offer_type in OFFER_TYPES],
    }
    data.update(changes)
    return data


def create_image(name="test.png"):
    """Return a tiny PNG image as an uploaded file."""
    buffer = io.BytesIO()
    Image.new("RGB", (10, 10)).save(buffer, "PNG")
    return SimpleUploadedFile(
        name, buffer.getvalue(), content_type="image/png"
    )


@override_settings(PASSWORD_HASHERS=FAST_PASSWORD_HASHERS)
class BaseAPITestCase(APITestCase):
    """Test case with one business and one customer user."""

    def setUp(self):
        """Create the two users most tests need."""
        self.business = create_user("business_user", UserProfile.BUSINESS)
        self.customer = create_user("customer_user", UserProfile.CUSTOMER)

    def use_temp_media(self):
        """Store uploaded files in a temporary folder during the test."""
        media_dir = tempfile.TemporaryDirectory()
        self.addCleanup(media_dir.cleanup)
        media_settings = override_settings(MEDIA_ROOT=media_dir.name)
        media_settings.enable()
        self.addCleanup(media_settings.disable)
