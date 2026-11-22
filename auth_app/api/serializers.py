"""Serializers for registration, login and user profiles."""
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


class BaseProfileSerializer(serializers.ModelSerializer):
    """Profile fields shared by all profile responses.

    Username and names live in Django's User model and are read
    through the related user.
    """

    username = serializers.CharField(source="user.username", read_only=True)
    first_name = serializers.CharField(
        source="user.first_name", max_length=150,
        required=False, allow_blank=True,
    )
    last_name = serializers.CharField(
        source="user.last_name", max_length=150,
        required=False, allow_blank=True,
    )


class BusinessProfileListSerializer(BaseProfileSerializer):
    """Business profile as shown in the business profile list."""

    class Meta:
        model = UserProfile
        fields = [
            "user", "username", "first_name", "last_name", "file",
            "location", "tel", "description", "working_hours", "type",
        ]


class CustomerProfileListSerializer(BaseProfileSerializer):
    """Customer profile as shown in the customer profile list."""

    class Meta:
        model = UserProfile
        fields = [
            "user", "username", "first_name", "last_name", "file",
            "uploaded_at", "type",
        ]


class ProfileDetailSerializer(BaseProfileSerializer):
    """Full profile of one user; used for reading and updating (PATCH)."""

    email = serializers.EmailField(source="user.email", required=False)

    class Meta:
        model = UserProfile
        fields = [
            "user", "username", "first_name", "last_name", "file",
            "location", "tel", "description", "working_hours", "type",
            "email", "created_at",
        ]
        read_only_fields = ["user", "type", "created_at"]

    def validate_email(self, value):
        """Reject an email address that another user already has."""
        email = value.lower()
        other_users = User.objects.exclude(pk=self.instance.user.pk)
        if other_users.filter(email__iexact=email).exists():
            raise serializers.ValidationError("This email is already in use.")
        return email

    def update(self, instance, validated_data):
        """Save the user fields on the User, the rest on the profile."""
        user_data = validated_data.pop("user", {})
        for field, value in user_data.items():
            setattr(instance.user, field, value)
        instance.user.save()
        return super().update(instance, validated_data)
