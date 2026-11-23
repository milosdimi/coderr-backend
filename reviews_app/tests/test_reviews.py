"""Tests for the review endpoints."""
from django.urls import reverse
from rest_framework import status

from auth_app.models import UserProfile
from auth_app.tests.helpers import BaseAPITestCase, create_user
from reviews_app.models import Review


class ReviewTestCase(BaseAPITestCase):
    """Base class: one review of the customer for the business user."""

    def setUp(self):
        """A second business user and one existing review."""
        super().setUp()
        self.other_business = create_user(
            "other_business", UserProfile.BUSINESS
        )
        self.review = Review.objects.create(
            business_user=self.business, reviewer=self.customer,
            rating=4, description="Good work",
        )
        self.url = reverse("review-detail", args=[self.review.id])


class ReviewListTests(ReviewTestCase):
    """GET /api/reviews/ with filters and ordering."""

    def setUp(self):
        """A second review by another customer for the other business."""
        super().setUp()
        other_customer = create_user("other_customer")
        Review.objects.create(
            business_user=self.other_business, reviewer=other_customer,
            rating=2, description="Okay",
        )

    def get_reviews(self, query=""):
        """Fetch the review list as the customer."""
        self.client.force_authenticate(self.customer)
        return self.client.get(reverse("review-list") + query)

    def test_list_reviews(self):
        """All reviews with the documented fields, newest first."""
        response = self.get_reviews()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["description"], "Okay")
        self.assertEqual(set(response.data[0]), {
            "id", "business_user", "reviewer", "rating", "description",
            "created_at", "updated_at",
        })

    def test_filter_by_business_user_and_reviewer(self):
        """Both filters return only the matching review."""
        by_business = self.get_reviews(
            f"?business_user_id={self.business.id}"
        )
        by_reviewer = self.get_reviews(f"?reviewer_id={self.customer.id}")
        for response in [by_business, by_reviewer]:
            self.assertEqual([review["id"] for review in response.data],
                             [self.review.id])

    def test_ordering_by_rating(self):
        """Reviews can be sorted by rating in both directions."""
        ascending = self.get_reviews("?ordering=rating")
        descending = self.get_reviews("?ordering=-rating")
        self.assertEqual([r["rating"] for r in ascending.data], [2, 4])
        self.assertEqual([r["rating"] for r in descending.data], [4, 2])

    def test_invalid_filter_value(self):
        """A filter value that is not a number returns 400."""
        response = self.get_reviews("?business_user_id=abc")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_not_authenticated(self):
        """A login is required."""
        response = self.client.get(reverse("review-list"))
        self.assertEqual(
            response.status_code, status.HTTP_401_UNAUTHORIZED
        )


class ReviewCreateTests(ReviewTestCase):
    """POST /api/reviews/ - customers only, once per business user."""

    def post_review(self, user, **changes):
        """Send a create request as the given user."""
        data = {"business_user": self.other_business.id, "rating": 5,
                "description": "Great!"}
        data.update(changes)
        self.client.force_authenticate(user)
        return self.client.post(reverse("review-list"), data, format="json")

    def test_create_review(self):
        """The logged in customer becomes the reviewer."""
        response = self.post_review(self.customer)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["reviewer"], self.customer.id)
        self.assertEqual(
            response.data["business_user"], self.other_business.id
        )

    def test_create_second_review_for_same_business(self):
        """A customer can review a business user only once."""
        response = self.post_review(
            self.customer, business_user=self.business.id
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_review_as_business_is_forbidden(self):
        """Business users cannot write reviews."""
        response = self.post_review(self.business)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_review_with_invalid_rating(self):
        """The rating has to be between 1 and 5."""
        for rating in [0, 6]:
            response = self.post_review(self.customer, rating=rating)
            self.assertEqual(
                response.status_code, status.HTTP_400_BAD_REQUEST
            )

    def test_create_review_for_non_business_user(self):
        """Customers and unknown users cannot be reviewed."""
        for user_id in [self.customer.id, 9999]:
            response = self.post_review(
                self.customer, business_user=user_id
            )
            self.assertEqual(
                response.status_code, status.HTTP_400_BAD_REQUEST
            )

    def test_create_review_with_missing_fields(self):
        """business_user and rating are required."""
        self.client.force_authenticate(self.customer)
        response = self.client.post(reverse("review-list"), {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("business_user", response.data)
        self.assertIn("rating", response.data)

    def test_create_review_not_authenticated(self):
        """A login is required."""
        response = self.client.post(reverse("review-list"), {}, format="json")
        self.assertEqual(
            response.status_code, status.HTTP_401_UNAUTHORIZED
        )


class ReviewUpdateDeleteTests(ReviewTestCase):
    """PATCH and DELETE /api/reviews/{id}/ - only for the reviewer."""

    def patch_review(self, user, data, url=None):
        """Send a PATCH request as the given user."""
        self.client.force_authenticate(user)
        return self.client.patch(url or self.url, data, format="json")

    def test_update_rating_and_description(self):
        """The reviewer can change rating and description."""
        response = self.patch_review(
            self.customer, {"rating": 5, "description": "Even better"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.review.refresh_from_db()
        self.assertEqual(self.review.rating, 5)
        self.assertEqual(self.review.description, "Even better")

    def test_update_other_fields_is_rejected(self):
        """Only rating and description are editable."""
        response = self.patch_review(
            self.customer, {"business_user": self.other_business.id}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("business_user", response.data)

    def test_update_with_invalid_rating(self):
        """The rating has to be between 1 and 5."""
        response = self.patch_review(self.customer, {"rating": 0})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_as_other_user_is_forbidden(self):
        """Only the reviewer may change the review."""
        response = self.patch_review(self.business, {"rating": 1})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_not_found(self):
        """An unknown review id returns 404."""
        url = reverse("review-detail", args=[9999])
        response = self.patch_review(self.customer, {"rating": 5}, url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_not_authenticated(self):
        """A login is required."""
        response = self.client.patch(self.url, {"rating": 5}, format="json")
        self.assertEqual(
            response.status_code, status.HTTP_401_UNAUTHORIZED
        )

    def test_delete_review(self):
        """The reviewer can delete the review."""
        self.client.force_authenticate(self.customer)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Review.objects.filter(id=self.review.id).exists())

    def test_delete_as_other_user_is_forbidden(self):
        """Only the reviewer may delete the review."""
        self.client.force_authenticate(self.business)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_not_found(self):
        """An unknown review id returns 404."""
        self.client.force_authenticate(self.customer)
        response = self.client.delete(reverse("review-detail", args=[9999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_not_authenticated(self):
        """A login is required."""
        response = self.client.delete(self.url)
        self.assertEqual(
            response.status_code, status.HTTP_401_UNAUTHORIZED
        )

    def test_get_single_review_is_not_allowed(self):
        """A single review cannot be fetched (not documented)."""
        self.client.force_authenticate(self.customer)
        response = self.client.get(self.url)
        self.assertEqual(
            response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def test_str_of_review(self):
        """A review shows reviewer, business user and rating."""
        self.assertEqual(
            str(self.review), "customer_user -> business_user: 4"
        )
