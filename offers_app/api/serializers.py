"""Serializers for offers and offer details.

The endpoint documentation uses four response shapes:
list, single offer, create/update and a single offer detail.
"""
from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import serializers

from offers_app.models import Offer, OfferDetail

REQUIRED_OFFER_TYPES = {
    OfferDetail.BASIC, OfferDetail.STANDARD, OfferDetail.PREMIUM,
}


def validate_complete_details(offer_types):
    """On create: exactly one basic, one standard and one premium."""
    if len(offer_types) != 3 or set(offer_types) != REQUIRED_OFFER_TYPES:
        raise serializers.ValidationError(
            "An offer needs exactly three details: "
            "basic, standard and premium."
        )


def validate_changed_details(offer_types):
    """On update: every detail names its type, each type only once."""
    if None in offer_types:
        raise serializers.ValidationError(
            "Every detail needs its offer_type to be identified."
        )
    if len(offer_types) != len(set(offer_types)):
        raise serializers.ValidationError(
            "Each offer_type may only appear once."
        )


class OfferDetailSerializer(serializers.ModelSerializer):
    """All fields of one offer detail (package)."""

    revisions = serializers.IntegerField(min_value=-1)
    delivery_time_in_days = serializers.IntegerField(min_value=1)
    price = serializers.DecimalField(
        max_digits=10, decimal_places=2, min_value=0
    )
    features = serializers.ListField(child=serializers.CharField())

    class Meta:
        model = OfferDetail
        fields = [
            "id", "title", "revisions", "delivery_time_in_days",
            "price", "features", "offer_type",
        ]


class OfferDetailLinkSerializer(serializers.ModelSerializer):
    """Short offer detail: only its id and the URL to its endpoint."""

    url = serializers.HyperlinkedIdentityField(view_name="offerdetail-detail")

    class Meta:
        model = OfferDetail
        fields = ["id", "url"]


class UserDetailsSerializer(serializers.ModelSerializer):
    """Name and username of the offer creator."""

    class Meta:
        model = User
        fields = ["first_name", "last_name", "username"]


class OfferListSerializer(serializers.ModelSerializer):
    """Offer as shown in the offer list (GET /api/offers/)."""

    details = OfferDetailLinkSerializer(many=True, read_only=True)
    min_price = serializers.FloatField(read_only=True)
    min_delivery_time = serializers.IntegerField(read_only=True)
    user_details = UserDetailsSerializer(source="user", read_only=True)

    class Meta:
        model = Offer
        fields = [
            "id", "user", "title", "image", "description", "created_at",
            "updated_at", "details", "min_price", "min_delivery_time",
            "user_details",
        ]


class OfferRetrieveSerializer(OfferListSerializer):
    """Single offer (GET /api/offers/{id}/): like the list item,
    but without user_details.
    """

    user_details = None

    class Meta(OfferListSerializer.Meta):
        fields = [
            "id", "user", "title", "image", "description", "created_at",
            "updated_at", "details", "min_price", "min_delivery_time",
        ]


class OfferWriteSerializer(serializers.ModelSerializer):
    """Creates (POST) and updates (PATCH) an offer with its details."""

    details = OfferDetailSerializer(many=True)

    class Meta:
        model = Offer
        fields = ["id", "title", "image", "description", "details"]

    def validate_details(self, value):
        """Check the offer types of the sent details."""
        offer_types = [detail.get("offer_type") for detail in value]
        if self.instance is None:
            validate_complete_details(offer_types)
        else:
            validate_changed_details(offer_types)
        return value

    @transaction.atomic
    def create(self, validated_data):
        """Create the offer and its three details together."""
        details_data = validated_data.pop("details")
        offer = Offer.objects.create(**validated_data)
        OfferDetail.objects.bulk_create(
            OfferDetail(offer=offer, **detail) for detail in details_data
        )
        return offer

    @transaction.atomic
    def update(self, instance, validated_data):
        """Update the offer; details are found by their offer_type."""
        details_data = validated_data.pop("details", [])
        for detail in details_data:
            instance.details.filter(
                offer_type=detail["offer_type"]
            ).update(**detail)
        return super().update(instance, validated_data)
