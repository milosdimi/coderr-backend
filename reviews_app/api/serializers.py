"""Serializers for reviews."""
from rest_framework import serializers

from auth_app.api.permissions import has_profile_type
from auth_app.models import UserProfile
from reviews_app.models import Review

EDITABLE_FIELDS = {"rating", "description"}


class ReviewSerializer(serializers.ModelSerializer):
    """Reads reviews and creates a new one (POST /api/reviews/)."""

    class Meta:
        model = Review
        fields = [
            "id", "business_user", "reviewer", "rating", "description",
            "created_at", "updated_at",
        ]
        read_only_fields = ["reviewer", "created_at", "updated_at"]

    def validate_business_user(self, value):
        """Only business users can be reviewed."""
        if not has_profile_type(value, UserProfile.BUSINESS):
            raise serializers.ValidationError(
                "The selected user is not a business user."
            )
        return value

    def validate(self, attrs):
        """A customer may review each business user only once."""
        reviewer = self.context["request"].user
        already_reviewed = Review.objects.filter(
            business_user=attrs["business_user"], reviewer=reviewer
        ).exists()
        if already_reviewed:
            raise serializers.ValidationError(
                "You have already reviewed this business user."
            )
        return attrs


class ReviewUpdateSerializer(serializers.ModelSerializer):
    """Updates rating and description (PATCH /api/reviews/{id}/)."""

    class Meta:
        model = Review
        fields = ReviewSerializer.Meta.fields
        read_only_fields = [
            "business_user", "reviewer", "created_at", "updated_at",
        ]

    def validate(self, attrs):
        """Reject every field except rating and description."""
        other_fields = set(self.initial_data) - EDITABLE_FIELDS
        if other_fields:
            raise serializers.ValidationError(
                {field: "This field cannot be changed."
                 for field in sorted(other_fields)}
            )
        return attrs
