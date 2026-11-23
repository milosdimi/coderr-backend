"""API views for reviews."""
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics
from rest_framework.permissions import IsAuthenticated

from auth_app.api.permissions import IsCustomerUser
from reviews_app.models import Review

from .filters import ReviewFilter
from .permissions import IsReviewer
from .serializers import ReviewSerializer, ReviewUpdateSerializer


class ReviewListCreateView(generics.ListCreateAPIView):
    """GET / POST /api/reviews/.

    Every logged in user may read reviews (filter and ordering
    possible), only customer users may create one.
    """

    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = ReviewFilter
    ordering_fields = ["updated_at", "rating"]
    ordering = ["-updated_at"]

    def get_permissions(self):
        """Creating a review is only allowed for customer users."""
        if self.request.method == "POST":
            return [IsAuthenticated(), IsCustomerUser()]
        return super().get_permissions()

    def perform_create(self, serializer):
        """The logged in customer becomes the reviewer."""
        serializer.save(reviewer=self.request.user)


class ReviewUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """PATCH / DELETE /api/reviews/{id}/ - only for the reviewer.

    GET is not part of the documentation and therefore not allowed.
    """

    queryset = Review.objects.all()
    serializer_class = ReviewUpdateSerializer
    permission_classes = [IsAuthenticated, IsReviewer]
    http_method_names = ["patch", "delete"]
