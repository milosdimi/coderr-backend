"""Tests for the order endpoints."""
from django.urls import reverse
from rest_framework import status

from auth_app.models import UserProfile
from auth_app.tests.helpers import BaseAPITestCase, create_offer, create_user
from orders_app.models import Order


class OrderTestCase(BaseAPITestCase):
    """Base class: an offer of the business user and an order helper."""

    def setUp(self):
        """One offer of the business user and its basic detail."""
        super().setUp()
        offer = create_offer(self.business)
        self.detail = offer.details.get(offer_type="basic")

    def create_order(self, order_status=Order.IN_PROGRESS):
        """Save an order of the customer at the business user."""
        return Order.objects.create(
            customer_user=self.customer, business_user=self.business,
            title="Logo", revisions=2, delivery_time_in_days=5, price=100,
            features=["Logo"], offer_type="basic", status=order_status,
        )


class OrderCreateTests(OrderTestCase):
    """POST /api/orders/ - customers only."""

    def post_order(self, user, data):
        """Send the create request as the given user."""
        self.client.force_authenticate(user)
        return self.client.post(reverse("order-list"), data, format="json")

    def test_create_order_copies_offer_detail(self):
        """The order takes over the data of the offer detail."""
        response = self.post_order(
            self.customer, {"offer_detail_id": self.detail.id}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["customer_user"], self.customer.id)
        self.assertEqual(response.data["business_user"], self.business.id)
        self.assertEqual(response.data["title"], self.detail.title)
        self.assertEqual(response.data["price"], 100.0)
        self.assertEqual(response.data["status"], Order.IN_PROGRESS)

    def test_create_order_not_authenticated(self):
        """A login is required."""
        response = self.client.post(
            reverse("order-list"), {"offer_detail_id": self.detail.id},
            format="json",
        )
        self.assertEqual(
            response.status_code, status.HTTP_401_UNAUTHORIZED
        )

    def test_create_order_as_business_is_forbidden(self):
        """Business users cannot order."""
        response = self.post_order(
            self.business, {"offer_detail_id": self.detail.id}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_order_with_missing_or_invalid_id(self):
        """offer_detail_id is required and must be a number."""
        for data in [{}, {"offer_detail_id": "abc"}]:
            response = self.post_order(self.customer, data)
            self.assertEqual(
                response.status_code, status.HTTP_400_BAD_REQUEST
            )

    def test_create_order_with_unknown_offer_detail(self):
        """An unknown offer detail returns 404."""
        response = self.post_order(self.customer, {"offer_detail_id": 9999})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class OrderListTests(OrderTestCase):
    """GET /api/orders/ - only the own orders."""

    def get_orders(self, user):
        """Fetch the order list as the given user."""
        self.client.force_authenticate(user)
        return self.client.get(reverse("order-list"))

    def test_customer_and_business_see_their_order(self):
        """Both participants of an order see it."""
        order = self.create_order()
        for user in [self.customer, self.business]:
            response = self.get_orders(user)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual([item["id"] for item in response.data],
                             [order.id])

    def test_other_users_do_not_see_the_order(self):
        """Users who are not part of the order get an empty list."""
        self.create_order()
        stranger = create_user("stranger", UserProfile.CUSTOMER)
        response = self.get_orders(stranger)
        self.assertEqual(response.data, [])

    def test_list_not_authenticated(self):
        """A login is required."""
        response = self.client.get(reverse("order-list"))
        self.assertEqual(
            response.status_code, status.HTTP_401_UNAUTHORIZED
        )


class OrderUpdateTests(OrderTestCase):
    """PATCH /api/orders/{id}/ - only the business user, only status."""

    def setUp(self):
        """One order in progress."""
        super().setUp()
        self.order = self.create_order()
        self.url = reverse("order-detail", args=[self.order.id])

    def patch_order(self, user, data):
        """Send a PATCH request as the given user."""
        self.client.force_authenticate(user)
        return self.client.patch(self.url, data, format="json")

    def test_business_user_updates_status(self):
        """The business user of the order can complete it."""
        response = self.patch_order(self.business, {"status": "completed"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], Order.COMPLETED)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.COMPLETED)

    def test_customer_cannot_update_status(self):
        """The customer of the order is not allowed to change it."""
        response = self.patch_order(self.customer, {"status": "cancelled"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_other_business_user_cannot_update_status(self):
        """Only the business user of this order may change it."""
        other = create_user("other_business", UserProfile.BUSINESS)
        response = self.patch_order(other, {"status": "completed"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_invalid_status(self):
        """Only the documented status values are allowed."""
        response = self.patch_order(self.business, {"status": "done"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_other_fields_are_rejected(self):
        """Fields other than status return 400."""
        response = self.patch_order(
            self.business, {"status": "completed", "price": 1}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("price", response.data)

    def test_status_is_required(self):
        """An empty PATCH returns 400."""
        response = self.patch_order(self.business, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("status", response.data)

    def test_update_not_found(self):
        """An unknown order id returns 404."""
        self.client.force_authenticate(self.business)
        response = self.client.patch(
            reverse("order-detail", args=[9999]), {"status": "completed"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_not_authenticated(self):
        """A login is required."""
        response = self.client.patch(
            self.url, {"status": "completed"}, format="json"
        )
        self.assertEqual(
            response.status_code, status.HTTP_401_UNAUTHORIZED
        )

    def test_get_and_delete_are_not_allowed(self):
        """A single order can only be updated."""
        self.client.force_authenticate(self.business)
        for response in [self.client.get(self.url),
                         self.client.delete(self.url)]:
            self.assertEqual(
                response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED
            )


class OrderCountTests(OrderTestCase):
    """GET /api/order-count/{id}/ and /api/completed-order-count/{id}/."""

    def get_count(self, url_name, user_id):
        """Fetch an order count as the customer."""
        self.client.force_authenticate(self.customer)
        return self.client.get(reverse(url_name, args=[user_id]))

    def test_counts_by_status(self):
        """Orders in progress and completed orders are counted apart."""
        for order_status in [Order.IN_PROGRESS, Order.IN_PROGRESS,
                             Order.COMPLETED, Order.CANCELLED]:
            self.create_order(order_status)
        in_progress = self.get_count("order-count", self.business.id)
        completed = self.get_count(
            "completed-order-count", self.business.id
        )
        self.assertEqual(in_progress.data, {"order_count": 2})
        self.assertEqual(completed.data, {"completed_order_count": 1})

    def test_count_for_non_business_user(self):
        """A customer id is not a business user and returns 404."""
        for url_name in ["order-count", "completed-order-count"]:
            response = self.get_count(url_name, self.customer.id)
            self.assertEqual(
                response.status_code, status.HTTP_404_NOT_FOUND
            )

    def test_count_for_unknown_user(self):
        """An unknown user id returns 404."""
        response = self.get_count("order-count", 9999)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_count_not_authenticated(self):
        """A login is required."""
        response = self.client.get(
            reverse("order-count", args=[self.business.id])
        )
        self.assertEqual(
            response.status_code, status.HTTP_401_UNAUTHORIZED
        )

    def test_str_of_order(self):
        """An order shows its title and status."""
        self.assertEqual(str(self.create_order()), "Logo (in_progress)")
