"""API view for general platform statistics."""
from django.db.models import Avg
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.models import UserProfile
from offers_app.models import Offer
from reviews_app.models import Review


class BaseInfoView(APIView):
    """GET /api/base-info/ - counts and average rating of the platform.

    Open on purpose: the start page shows these numbers to every
    visitor. Authentication is disabled so an outdated token in the
    header cannot block the request.
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        """Return review count, average rating, business and offer count."""
        average = Review.objects.aggregate(average=Avg("rating"))["average"]
        return Response({
            "review_count": Review.objects.count(),
            "average_rating": round(average or 0.0, 1),
            "business_profile_count": UserProfile.objects.filter(
                type=UserProfile.BUSINESS
            ).count(),
            "offer_count": Offer.objects.count(),
        })
