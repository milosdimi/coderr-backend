"""Serializers for registration and login."""
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import serializers

from auth_app.models import UserProfile


class RegistrationSerializer(serializers.ModelSerializer):
    """Validates the sign up data and creates a user with a profile."""

    email = serializers.EmailField()
    repeated_password = serializers.CharField(write_only=True)
    type = serializers.ChoiceField(
        choices=UserProfile.TYPE_CHOICES, write_only=True
    )

    class Meta:
        model = User
        fields = ["username", "email", "password", "repeated_password", "type"]
        extra_kwargs = {"password": {"write_only": True}}

    def validate_email(self, value):
        """Reject an email address that is already registered."""
        email = value.lower()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("This email is already in use.")
        return email

    def validate(self, attrs):
        """Make sure both passwords are identical."""
        if attrs["password"] != attrs["repeated_password"]:
            raise serializers.ValidationError(
                {"repeated_password": "Passwords do not match."}
            )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        """Create the user and its profile together (all or nothing)."""
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
        )
        UserProfile.objects.create(user=user, type=validated_data["type"])
        return user


class LoginSerializer(serializers.Serializer):
    """Checks username and password and returns the matching user."""

    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """Authenticate the user by username and password."""
        user = authenticate(
            username=attrs["username"], password=attrs["password"]
        )
        if not user:
            raise serializers.ValidationError(
                "Invalid username or password."
            )
        attrs["user"] = user
        return attrs
