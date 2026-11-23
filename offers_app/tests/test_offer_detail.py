"""Tests for GET /api/offers/{id}/ and GET /api/offerdetails/{id}/."""
from django.urls import reverse
from rest_framework import status

from auth_app.tests.helpers import BaseAPITestCase, create_offer


class OfferRetrieveTests(BaseAPITestCase):
    """A single offer is visible for logged in users."""

    def setUp(self):
        """One offer of the business user."""
        super().setUp()
        self.offer = create_offer(self.business)
        self.url = reverse("offer-detail", args=[self.offer.id])

    def test_get_single_offer(self):
        """The single offer has min values but no user_details."""
        self.client.force_authenticate(self.customer)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"], self.business.id)
        self.assertEqual(response.data["min_price"], 100.0)
        self.assertEqual(response.data["min_delivery_time"], 5)
        self.assertNotIn("user_details", response.data)

    def test_get_single_offer_not_authenticated(self):
        """A login is required."""
        response = self.client.get(self.url)
        self.assertEqual(
            response.status_code, status.HTTP_401_UNAUTHORIZED
        )

    def test_get_single_offer_not_found(self):
        """An unknown offer id returns 404."""
        self.client.force_authenticate(self.customer)
        response = self.client.get(reverse("offer-detail", args=[9999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class OfferDetailEndpointTests(BaseAPITestCase):
    """One offer detail (package) is visible for logged in users."""

    def setUp(self):
        """One offer with its basic detail."""
        super().setUp()
        self.detail = create_offer(self.business).details.get(
            offer_type="basic"
        )
        self.url = reverse("offerdetail-detail", args=[self.detail.id])

    def test_get_offer_detail(self):
        """All documented fields; the price is a number."""
        self.client.force_authenticate(self.customer)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["offer_type"], "basic")
        self.assertEqual(response.data["price"], 100.0)
        self.assertEqual(response.data["features"], ["Feature"])

    def test_get_offer_detail_not_authenticated(self):
        """A login is required."""
        response = self.client.get(self.url)
        self.assertEqual(
            response.status_code, status.HTTP_401_UNAUTHORIZED
        )

    def test_get_offer_detail_not_found(self):
        """An unknown detail id returns 404."""
        self.client.force_authenticate(self.customer)
        response = self.client.get(
            reverse("offerdetail-detail", args=[9999])
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
