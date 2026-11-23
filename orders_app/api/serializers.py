"""Serializers for orders."""
from django.shortcuts import get_object_or_404
from rest_framework import serializers

from offers_app.models import OfferDetail
from orders_app.models import Order

ORDER_FIELDS = [
    "id", "customer_user", "business_user", "title", "revisions",
    "delivery_time_in_days", "price", "features", "offer_type", "status",
    "created_at", "updated_at",
]


DETAIL_FIELDS_TO_COPY = [
    "title", "revisions", "delivery_time_in_days", "price", "features",
    "offer_type",
]


def order_data_from_detail(detail):
    """Collect the offer detail values an order keeps as a copy."""
    data = {field: getattr(detail, field) for field in DETAIL_FIELDS_TO_COPY}
    data["business_user"] = detail.offer.user
    return data


class OrderSerializer(serializers.ModelSerializer):
    """Read-only representation of an order."""

    class Meta:
        model = Order
        fields = ORDER_FIELDS
        read_only_fields = ORDER_FIELDS


class OrderCreateSerializer(OrderSerializer):
    """Creates an order from an offer detail (POST /api/orders/)."""

    offer_detail_id = serializers.IntegerField(write_only=True)

    class Meta(OrderSerializer.Meta):
        fields = ORDER_FIELDS + ["offer_detail_id"]

    def create(self, validated_data):
        """Copy the offer detail data into a new order.

        The business user is the creator of the offer; an unknown
        offer detail leads to 404.
        """
        detail = get_object_or_404(
            OfferDetail.objects.select_related("offer"),
            pk=validated_data["offer_detail_id"],
        )
        return Order.objects.create(
            customer_user=validated_data["customer_user"],
            **order_data_from_detail(detail),
        )


class OrderStatusSerializer(OrderSerializer):
    """Updates only the status of an order (PATCH /api/orders/{id}/)."""

    class Meta(OrderSerializer.Meta):
        read_only_fields = [
            field for field in ORDER_FIELDS if field != "status"
        ]

    def validate(self, attrs):
        """Require the status and reject every other field."""
        other_fields = set(self.initial_data) - {"status"}
        if other_fields:
            raise serializers.ValidationError(
                {field: "This field cannot be changed."
                 for field in sorted(other_fields)}
            )
        if "status" not in attrs:
            raise serializers.ValidationError(
                {"status": "This field is required."}
            )
        return attrs
