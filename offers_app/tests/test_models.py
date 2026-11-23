"""Tests for the models of the offers app."""
from auth_app.tests.helpers import BaseAPITestCase, create_offer


class OfferModelTests(BaseAPITestCase):
    """String representation of offers and offer details."""

    def test_str_of_offer_and_detail(self):
        """An offer shows its title, a detail also its type."""
        offer = create_offer(self.business, "Website")
        detail = offer.details.get(offer_type="premium")
        self.assertEqual(str(offer), "Website")
        self.assertEqual(str(detail), "Website - premium")
