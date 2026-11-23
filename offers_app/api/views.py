"""API views for offers and offer details."""
from django.db.models import Min
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated

from auth_app.api.permissions import IsBusinessUser
from offers_app.models import Offer, OfferDetail

from .filters import OfferFilter
from .pagination import OfferPagination
from .permissions import IsOfferOwnerOrReadOnly
from .serializers import (
    OfferDetailSerializer,
    OfferListSerializer,
    OfferRetrieveSerializer,
    OfferWriteSerializer,
)


class OfferViewSet(viewsets.ModelViewSet):
    """CRUD for offers: /api/offers/ and /api/offers/{id}/.

    list:     open for everyone (no permission in the documentation)
    create:   business users only
    retrieve: logged in users
    update / delete: the creator of the offer only
    """

    queryset = Offer.objects.select_related("user").prefetch_related(
        "details"
    ).annotate(
        min_price=Min("details__price"),
        min_delivery_time=Min("details__delivery_time_in_days"),
    )
    permission_classes = [IsAuthenticated, IsOfferOwnerOrReadOnly]
    pagination_class = OfferPagination
    filter_backends = [
        DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter,
    ]
    filterset_class = OfferFilter
    search_fields = ["title", "description"]
    ordering_fields = ["updated_at", "min_price"]
    ordering = ["-updated_at"]
    http_method_names = ["get", "post", "patch", "delete"]

    def get_permissions(self):
        """Open list, business-only create, default rules otherwise."""
        if self.action == "list":
            return [AllowAny()]
        if self.action == "create":
            return [IsAuthenticated(), IsBusinessUser()]
        return super().get_permissions()

    def get_serializer_class(self):
        """Pick the serializer that matches the documented response."""
        if self.action == "list":
            return OfferListSerializer
        if self.action == "retrieve":
            return OfferRetrieveSerializer
        return OfferWriteSerializer

    def perform_create(self, serializer):
        """The logged in business user becomes the offer creator."""
        serializer.save(user=self.request.user)


class OfferDetailView(generics.RetrieveAPIView):
    """GET /api/offerdetails/{id}/ - one offer detail (package)."""

    queryset = OfferDetail.objects.all()
    serializer_class = OfferDetailSerializer
    permission_classes = [IsAuthenticated]
