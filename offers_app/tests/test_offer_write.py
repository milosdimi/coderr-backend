"""Tests for creating, updating and deleting offers."""
from django.urls import reverse
from rest_framework import status

from auth_app.tests.helpers import (
    BaseAPITestCase,
    create_image,
    create_offer,
    detail_payload,
    offer_payload,
)
from offers_app.models import Offer, OfferDetail


class OfferCreateTests(BaseAPITestCase):
    """POST /api/offers/ - business users only, exactly three details."""

    def post_offer(self, user, data):
        """Send the create request as the given user."""
        self.client.force_authenticate(user)
        return self.client.post(reverse("offer-list"), data, format="json")

    def test_create_offer(self):
        """The offer is saved with three details for the creator."""
        response = self.post_offer(self.business, offer_payload())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            set(response.data),
            {"id", "title", "image", "description", "details"},
        )
        offer = Offer.objects.get(id=response.data["id"])
        self.assertEqual(offer.user, self.business)
        self.assertEqual(offer.details.count(), 3)

    def test_create_offer_accepts_price_as_string(self):
        """The price may also be sent as a string."""
        details = [detail_payload("basic", price="99.50"),
                   detail_payload("standard"), detail_payload("premium")]
        response = self.post_offer(
            self.business, offer_payload(details=details)
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["details"][0]["price"], 99.5)

    def test_create_offer_not_authenticated(self):
        """A login is required."""
        response = self.client.post(
            reverse("offer-list"), offer_payload(), format="json"
        )
        self.assertEqual(
            response.status_code, status.HTTP_401_UNAUTHORIZED
        )

    def test_create_offer_as_customer_is_forbidden(self):
        """Customers cannot create offers."""
        response = self.post_offer(self.customer, offer_payload())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_offer_with_two_details(self):
        """Exactly three details are required."""
        details = [detail_payload("basic"), detail_payload("standard")]
        response = self.post_offer(
            self.business, offer_payload(details=details)
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_offer_with_duplicate_type(self):
        """Each offer type is required exactly once."""
        details = [detail_payload("basic"), detail_payload("standard"),
                   detail_payload("basic")]
        response = self.post_offer(
            self.business, offer_payload(details=details)
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_offer_with_invalid_numbers(self):
        """Delivery time >= 1, revisions >= -1, price >= 0."""
        details = [
            detail_payload("basic", delivery_time_in_days=0, revisions=-2,
                           price=-1),
            detail_payload("standard"), detail_payload("premium"),
        ]
        data = offer_payload(details=details)
        response = self.post_offer(self.business, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            set(response.data["details"][0]),
            {"delivery_time_in_days", "revisions", "price"},
        )

    def test_create_offer_with_missing_fields(self):
        """Title and details are required."""
        response = self.post_offer(self.business, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("title", response.data)
        self.assertIn("details", response.data)


class OfferUpdateDeleteTests(BaseAPITestCase):
    """PATCH and DELETE /api/offers/{id}/ - only for the creator."""

    def setUp(self):
        """One offer of the business user."""
        super().setUp()
        self.offer = create_offer(self.business)
        self.url = reverse("offer-detail", args=[self.offer.id])

    def patch_offer(self, user, data, data_format="json"):
        """Send a PATCH request as the given user."""
        self.client.force_authenticate(user)
        return self.client.patch(self.url, data, format=data_format)

    def test_patch_title_and_one_detail(self):
        """Only the sent detail changes; all detail ids stay the same."""
        detail_ids = list(self.offer.details.values_list("id", flat=True))
        data = {"title": "Updated", "details": [
            {"title": "Basic new", "price": 120, "offer_type": "basic"}]}
        response = self.patch_offer(self.business, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Updated")
        returned_ids = [detail["id"] for detail in response.data["details"]]
        self.assertEqual(sorted(returned_ids), sorted(detail_ids))
        basic = self.offer.details.get(offer_type="basic")
        self.assertEqual((basic.title, basic.price), ("Basic new", 120))

    def test_patch_detail_without_offer_type(self):
        """Every sent detail needs its offer_type."""
        response = self.patch_offer(
            self.business, {"details": [{"price": 150}]}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_detail_type_twice(self):
        """The same offer type may not be sent twice."""
        details = [{"price": 1, "offer_type": "basic"},
                   {"price": 2, "offer_type": "basic"}]
        response = self.patch_offer(self.business, {"details": details})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_image(self):
        """An offer image can be uploaded as multipart data."""
        self.use_temp_media()
        response = self.patch_offer(
            self.business, {"image": create_image()}, "multipart"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("offer_images/", response.data["image"])

    def test_patch_as_other_user_is_forbidden(self):
        """Only the creator may change the offer."""
        response = self.patch_offer(self.customer, {"title": "Hacked"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_not_found(self):
        """An unknown offer id returns 404."""
        self.client.force_authenticate(self.business)
        response = self.client.patch(
            reverse("offer-detail", args=[9999]), {"title": "x"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_not_authenticated(self):
        """A login is required."""
        response = self.client.patch(self.url, {"title": "x"}, format="json")
        self.assertEqual(
            response.status_code, status.HTTP_401_UNAUTHORIZED
        )

    def test_put_is_not_allowed(self):
        """Only PATCH is documented for updates."""
        self.client.force_authenticate(self.business)
        response = self.client.put(self.url, offer_payload(), format="json")
        self.assertEqual(
            response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def test_delete_offer_with_details(self):
        """Deleting an offer also deletes its details."""
        self.client.force_authenticate(self.business)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Offer.objects.filter(id=self.offer.id).exists())
        self.assertFalse(
            OfferDetail.objects.filter(offer_id=self.offer.id).exists()
        )

    def test_delete_as_other_user_is_forbidden(self):
        """Only the creator may delete the offer."""
        self.client.force_authenticate(self.customer)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_not_found(self):
        """An unknown offer id returns 404."""
        self.client.force_authenticate(self.business)
        response = self.client.delete(reverse("offer-detail", args=[9999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_not_authenticated(self):
        """A login is required."""
        response = self.client.delete(self.url)
        self.assertEqual(
            response.status_code, status.HTTP_401_UNAUTHORIZED
        )
