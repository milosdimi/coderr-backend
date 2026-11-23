"""API views for orders and order counts."""
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.api.permissions import IsCustomerUser
from auth_app.models import UserProfile
from orders_app.models import Order

from .permissions import IsOrderBusinessUser
from .serializers import (
    OrderCreateSerializer,
    OrderSerializer,
    OrderStatusSerializer,
)


class OrderListCreateView(generics.ListCreateAPIView):
    """GET / POST /api/orders/.

    GET lists the orders of the logged in user (as customer or business),
    POST creates a new order and is allowed for customers only.
    """

    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Only orders the logged in user takes part in."""
        user = self.request.user
        return Order.objects.filter(
            Q(customer_user=user) | Q(business_user=user)
        )

    def get_permissions(self):
        """Creating an order is only allowed for customer users."""
        if self.request.method == "POST":
            return [IsAuthenticated(), IsCustomerUser()]
        return super().get_permissions()

    def get_serializer_class(self):
        """Use the create serializer for POST."""
        if self.request.method == "POST":
            return OrderCreateSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        """The logged in customer becomes the customer of the order."""
        serializer.save(customer_user=self.request.user)


class OrderUpdateView(generics.UpdateAPIView):
    """PATCH /api/orders/{id}/ - the business user changes the status."""

    queryset = Order.objects.all()
    serializer_class = OrderStatusSerializer
    permission_classes = [IsAuthenticated, IsOrderBusinessUser]
    http_method_names = ["patch"]


class BaseOrderCountView(APIView):
    """Counts the orders of a business user with a given status.

    Subclasses set the status and the key of the response.
    """

    permission_classes = [IsAuthenticated]
    order_status = None
    response_key = None

    def get(self, request, business_user_id):
        """Return the number of orders; 404 for an unknown business user."""
        business_user = get_object_or_404(
            User, pk=business_user_id, profile__type=UserProfile.BUSINESS
        )
        count = Order.objects.filter(
            business_user=business_user, status=self.order_status
        ).count()
        return Response({self.response_key: count})


class OrderCountView(BaseOrderCountView):
    """GET /api/order-count/{business_user_id}/ - orders in progress."""

    order_status = Order.IN_PROGRESS
    response_key = "order_count"


class CompletedOrderCountView(BaseOrderCountView):
    """GET /api/completed-order-count/{business_user_id}/ - completed."""

    order_status = Order.COMPLETED
    response_key = "completed_order_count"
