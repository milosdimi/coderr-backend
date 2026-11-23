"""Tests for GET /api/offers/ with filters, search, ordering, paging."""
from django.urls import reverse
from rest_framework import status

from auth_app.models import UserProfile
from auth_app.tests.helpers import BaseAPITestCase, create_offer, create_user

LIST_FIELDS = {
    "id", "user", "title", "image", "description", "created_at",
    "updated_at", "details", "min_price", "min_delivery_time",
    "user_details",
}


class OfferListTests(BaseAPITestCase):
    """The offer list is open for everyone."""

    def setUp(self):
        """Two offers of two business users with different prices."""
        super().setUp()
        self.website = create_offer(self.business, "Website", 100, 5)
        other = create_user("other_business", UserProfile.BUSINESS)
        self.logo = create_offer(other, "Logo Design", 50, 3)

    def get_offers(self, query=""):
        """Fetch the offer list without login."""
        return self.client.get(reverse("offer-list") + query)

    def result_titles(self, response):
        """Titles of the offers in the response, in order."""
        return [offer["title"] for offer in response.data["results"]]

    def test_list_is_open_and_paginated(self):
        """No login needed; the response is a paginated page."""
        response = self.get_offers()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            set(response.data), {"count", "next", "previous", "results"}
        )
        self.assertEqual(response.data["count"], 2)

    def test_list_item_has_documented_fields(self):
        """Each offer has min values, detail links and user details."""
        response = self.get_offers("?search=website")
        offer = response.data["results"][0]
        self.assertEqual(set(offer), LIST_FIELDS)
        self.assertEqual(offer["min_price"], 100.0)
        self.assertEqual(offer["min_delivery_time"], 5)
        self.assertEqual(len(offer["details"]), 3)
        self.assertIn("/api/offerdetails/", offer["details"][0]["url"])
        self.assertEqual(
            offer["user_details"]["username"], "business_user"
        )

    def test_default_ordering_is_newest_first(self):
        """Without ordering the latest updated offer comes first."""
        response = self.get_offers()
        self.assertEqual(
            self.result_titles(response), ["Logo Design", "Website"]
        )

    def test_empty_frontend_parameters_are_ignored(self):
        """The frontend always sends all parameters, often empty."""
        response = self.get_offers(
            "?creator_id=&search=&ordering=&page=1&max_delivery_time="
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)

    def test_filter_by_creator(self):
        """creator_id returns only the offers of that user."""
        response = self.get_offers(f"?creator_id={self.business.id}")
        self.assertEqual(self.result_titles(response), ["Website"])

    def test_filter_by_min_price(self):
        """min_price keeps offers whose cheapest detail costs enough."""
        response = self.get_offers("?min_price=60")
        self.assertEqual(self.result_titles(response), ["Website"])

    def test_filter_by_max_delivery_time(self):
        """max_delivery_time keeps offers that can be delivered in time."""
        response = self.get_offers("?max_delivery_time=4")
        self.assertEqual(self.result_titles(response), ["Logo Design"])

    def test_search_in_title_and_description(self):
        """search looks into title and description."""
        self.website.description = "Responsive pages"
        self.website.save()
        by_title = self.get_offers("?search=logo")
        by_description = self.get_offers("?search=responsive")
        self.assertEqual(self.result_titles(by_title), ["Logo Design"])
        self.assertEqual(self.result_titles(by_description), ["Website"])

    def test_ordering_by_min_price(self):
        """The list can be sorted by the lowest price in both directions."""
        ascending = self.get_offers("?ordering=min_price")
        descending = self.get_offers("?ordering=-min_price")
        self.assertEqual(
            self.result_titles(ascending), ["Logo Design", "Website"]
        )
        self.assertEqual(
            self.result_titles(descending), ["Website", "Logo Design"]
        )

    def test_ordering_by_updated_at(self):
        """The oldest offer comes first with ordering=updated_at."""
        response = self.get_offers("?ordering=updated_at")
        self.assertEqual(
            self.result_titles(response), ["Website", "Logo Design"]
        )

    def test_invalid_filter_value(self):
        """A filter value that is not a number returns 400."""
        response = self.get_offers("?creator_id=abc")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_page_size_parameter(self):
        """page_size limits the results and creates a next link."""
        response = self.get_offers("?page_size=1")
        self.assertEqual(len(response.data["results"]), 1)
        self.assertIsNotNone(response.data["next"])

    def test_default_page_size_is_six(self):
        """Six offers per page, like PAGE_SIZE in the frontend."""
        for number in range(5):
            create_offer(self.business, f"Extra {number}")
        response = self.get_offers()
        self.assertEqual(response.data["count"], 7)
        self.assertEqual(len(response.data["results"]), 6)
