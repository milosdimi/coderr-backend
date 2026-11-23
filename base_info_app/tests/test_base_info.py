"""Tests for GET /api/base-info/."""
from django.urls import reverse
from rest_framework import status

from auth_app.models import UserProfile
from auth_app.tests.helpers import BaseAPITestCase, create_offer, create_user
from reviews_app.models import Review


class BaseInfoTests(BaseAPITestCase):
    """Platform statistics, open for every visitor."""

    def get_base_info(self):
        """Fetch the statistics without login."""
        return self.client.get(reverse("base-info"))

    def add_reviews(self, ratings):
        """Create one review per rating, each by a new customer."""
        for number, rating in enumerate(ratings):
            reviewer = create_user(f"reviewer_{number}")
            Review.objects.create(
                business_user=self.business, reviewer=reviewer,
                rating=rating,
            )

    def test_base_info_without_reviews(self):
        """Without reviews the average rating is 0.0."""
        response = self.get_base_info()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["review_count"], 0)
        self.assertEqual(response.data["average_rating"], 0.0)
        self.assertEqual(response.data["offer_count"], 0)

    def test_average_rating_is_rounded(self):
        """(5 + 4 + 4) / 3 = 4.33 is rounded to one decimal place."""
        self.add_reviews([5, 4, 4])
        response = self.get_base_info()
        self.assertEqual(response.data["review_count"], 3)
        self.assertEqual(response.data["average_rating"], 4.3)

    def test_counts_business_profiles_and_offers(self):
        """New business users and offers raise the counts."""
        before = self.get_base_info().data
        create_user("new_business", UserProfile.BUSINESS)
        create_user("new_customer", UserProfile.CUSTOMER)
        create_offer(self.business)
        after = self.get_base_info().data
        self.assertEqual(
            after["business_profile_count"],
            before["business_profile_count"] + 1,
        )
        self.assertEqual(after["offer_count"], before["offer_count"] + 1)

    def test_invalid_token_does_not_block(self):
        """An outdated token in the header is ignored."""
        self.client.credentials(HTTP_AUTHORIZATION="Token invalid")
        response = self.get_base_info()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_is_not_allowed(self):
        """Only GET is documented."""
        response = self.client.post(reverse("base-info"))
        self.assertEqual(
            response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED
        )
