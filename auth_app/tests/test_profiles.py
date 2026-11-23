"""Tests for the profile endpoints."""
from django.urls import reverse
from rest_framework import status

from auth_app.models import UserProfile

from .helpers import BaseAPITestCase, create_image, create_user

TEXT_FIELDS = [
    "first_name", "last_name", "location", "tel", "description",
    "working_hours",
]


class ProfileDetailTests(BaseAPITestCase):
    """GET and PATCH /api/profile/{pk}/."""

    def profile_url(self, user_id):
        """URL of the profile of the given user."""
        return reverse("profile-detail", args=[user_id])

    def patch_profile(self, user, data, user_id=None, data_format="json"):
        """Send a PATCH request as the given user."""
        self.client.force_authenticate(user)
        return self.client.patch(
            self.profile_url(user_id or user.id), data, format=data_format
        )

    def test_get_profile_returns_documented_fields(self):
        """Any logged in user can read a profile."""
        self.client.force_authenticate(self.customer)
        response = self.client.get(self.profile_url(self.business.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"], self.business.id)
        self.assertEqual(response.data["type"], UserProfile.BUSINESS)
        self.assertEqual(response.data["email"], "business_user@mail.de")
        self.assertIn("created_at", response.data)

    def test_empty_text_fields_are_empty_strings(self):
        """Empty profile fields are returned as '' and never as null."""
        self.client.force_authenticate(self.customer)
        response = self.client.get(self.profile_url(self.customer.id))
        for field in TEXT_FIELDS:
            self.assertEqual(response.data[field], "")

    def test_get_profile_not_authenticated(self):
        """Profiles are only visible for logged in users."""
        response = self.client.get(self.profile_url(self.business.id))
        self.assertEqual(
            response.status_code, status.HTTP_401_UNAUTHORIZED
        )

    def test_get_profile_not_found(self):
        """An unknown user id returns 404."""
        self.client.force_authenticate(self.customer)
        response = self.client.get(self.profile_url(9999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_own_profile(self):
        """User fields and profile fields are both updated."""
        data = {"first_name": "Max", "location": "Berlin",
                "email": "max@business.de"}
        response = self.patch_profile(self.business, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.business.refresh_from_db()
        self.assertEqual(self.business.first_name, "Max")
        self.assertEqual(self.business.email, "max@business.de")
        self.assertEqual(self.business.profile.location, "Berlin")

    def test_patch_own_profile_with_image(self):
        """A profile picture can be uploaded as multipart data."""
        self.use_temp_media()
        response = self.patch_profile(
            self.business, {"file": create_image()},
            data_format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("profile_pictures/", response.data["file"])

    def test_patch_cannot_change_type(self):
        """The profile type is read-only."""
        self.patch_profile(self.business, {"type": "customer"})
        self.business.profile.refresh_from_db()
        self.assertEqual(self.business.profile.type, UserProfile.BUSINESS)

    def test_patch_keeps_own_email(self):
        """Sending the own email again is not a conflict."""
        response = self.patch_profile(
            self.business, {"email": "business_user@mail.de"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_patch_other_profile_is_forbidden(self):
        """Only the owner may change a profile."""
        response = self.patch_profile(
            self.customer, {"tel": "123"}, user_id=self.business.id
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_profile_not_found(self):
        """An unknown user id returns 404."""
        response = self.patch_profile(self.customer, {"tel": "1"}, 9999)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_with_invalid_email(self):
        """The email has to be valid."""
        response = self.patch_profile(self.business, {"email": "no-mail"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_with_taken_email(self):
        """The email may not belong to another user."""
        response = self.patch_profile(
            self.business, {"email": "Customer_User@mail.de"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_patch_not_authenticated(self):
        """Changing a profile requires a login."""
        response = self.client.patch(
            self.profile_url(self.business.id), {"tel": "1"}, format="json"
        )
        self.assertEqual(
            response.status_code, status.HTTP_401_UNAUTHORIZED
        )

    def test_put_is_not_allowed(self):
        """Only PATCH is documented for updates."""
        self.client.force_authenticate(self.business)
        response = self.client.put(
            self.profile_url(self.business.id), {}, format="json"
        )
        self.assertEqual(
            response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED
        )


class ProfileListTests(BaseAPITestCase):
    """GET /api/profiles/business/ and /api/profiles/customer/."""

    def get_list(self, url_name):
        """Fetch a profile list as the customer."""
        self.client.force_authenticate(self.customer)
        return self.client.get(reverse(url_name))

    def test_business_list_contains_only_business_users(self):
        """Every entry of the business list is a business profile."""
        create_user("second_business", UserProfile.BUSINESS)
        response = self.get_list("business-profile-list")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        types = {profile["type"] for profile in response.data}
        self.assertEqual(types, {UserProfile.BUSINESS})
        self.assertIn("working_hours", response.data[0])

    def test_customer_list_contains_only_customer_users(self):
        """Every entry of the customer list is a customer profile."""
        response = self.get_list("customer-profile-list")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        types = {profile["type"] for profile in response.data}
        self.assertEqual(types, {UserProfile.CUSTOMER})
        self.assertIn("uploaded_at", response.data[0])

    def test_lists_not_authenticated(self):
        """Both lists require a login."""
        for url_name in ["business-profile-list", "customer-profile-list"]:
            response = self.client.get(reverse(url_name))
            self.assertEqual(
                response.status_code, status.HTTP_401_UNAUTHORIZED
            )
