"""Tests for POST /api/registration/ and POST /api/login/."""
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status

from auth_app.models import UserProfile

from .helpers import PASSWORD, BaseAPITestCase


class RegistrationTests(BaseAPITestCase):
    """Sign up as customer or business user."""

    def registration_data(self, **changes):
        """Valid registration data; changes overwrite values."""
        data = {
            "username": "new_user", "email": "new@mail.de",
            "password": "secret123", "repeated_password": "secret123",
            "type": "customer",
        }
        data.update(changes)
        return data

    def register(self, **changes):
        """Send the registration request."""
        return self.client.post(
            reverse("registration"), self.registration_data(**changes),
            format="json",
        )

    def test_register_customer_returns_token_and_user(self):
        """A new customer gets a token and the documented user data."""
        response = self.register()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username="new_user")
        self.assertEqual(
            set(response.data), {"token", "username", "email", "user_id"}
        )
        self.assertEqual(response.data["user_id"], user.id)
        self.assertEqual(user.profile.type, UserProfile.CUSTOMER)

    def test_register_business_creates_business_profile(self):
        """The type of the request decides the profile type."""
        response = self.register(type="business")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username="new_user")
        self.assertEqual(user.profile.type, UserProfile.BUSINESS)

    def test_register_saves_email_in_lowercase(self):
        """Emails are stored in lowercase."""
        self.register(email="New@Mail.DE")
        self.assertTrue(User.objects.filter(email="new@mail.de").exists())

    def test_register_with_taken_username_and_email(self):
        """Username and email must be unique."""
        response = self.register(
            username="customer_user", email="customer_user@mail.de"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data)
        self.assertIn("email", response.data)

    def test_register_with_different_passwords(self):
        """Both passwords have to be identical."""
        response = self.register(repeated_password="other123")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("repeated_password", response.data)

    def test_register_with_invalid_type(self):
        """Only customer and business are valid types."""
        response = self.register(type="admin")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("type", response.data)

    def test_register_with_missing_fields(self):
        """An empty request names every required field."""
        response = self.client.post(
            reverse("registration"), {}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        for field in ["username", "email", "password", "type"]:
            self.assertIn(field, response.data)

    def test_register_ignores_invalid_token(self):
        """An outdated token in the header does not block sign up."""
        self.client.credentials(HTTP_AUTHORIZATION="Token invalid")
        response = self.register()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class LoginTests(BaseAPITestCase):
    """Log in with username and password."""

    def login(self, username, password):
        """Send the login request."""
        return self.client.post(
            reverse("login"),
            {"username": username, "password": password},
            format="json",
        )

    def test_login_returns_token_and_user(self):
        """Correct credentials return the documented data."""
        response = self.login("customer_user", PASSWORD)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user_id"], self.customer.id)
        self.assertEqual(response.data["username"], "customer_user")
        self.assertEqual(response.data["email"], "customer_user@mail.de")
        self.assertTrue(response.data["token"])

    def test_login_with_wrong_password(self):
        """A wrong password is rejected."""
        response = self.login("customer_user", "wrong")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_with_missing_fields(self):
        """Username and password are required."""
        response = self.client.post(reverse("login"), {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data)
        self.assertIn("password", response.data)

    def test_guest_users_can_log_in(self):
        """The guest users of the frontend exist with the right type."""
        guests = [("andrey", "asdasd", UserProfile.CUSTOMER),
                  ("kevin", "asdasd24", UserProfile.BUSINESS)]
        for username, password, profile_type in guests:
            response = self.login(username, password)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            user = User.objects.get(username=username)
            self.assertEqual(user.profile.type, profile_type)
