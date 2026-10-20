from datetime import date

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.buyers.models import Buyer
from .models import Order


class OrderAPITests(APITestCase):
    """Test Order API CRUD operations and validation."""

    def setUp(self):
        """Create a buyer and order for each test."""

        self.buyer = Buyer.objects.create(
            name="ABC Fashion Ltd.",
            contact_person="John Smith",
            email="john@example.com",
            country="US",
        )

        self.list_url = reverse("order-list")

        self.order = Order.objects.create(
            order_number="ORD-2026-001",
            buyer=self.buyer,
            order_date=date(2026, 10, 20),
            delivery_date=date(2026, 11, 10),
            quantity=1000,
            status=Order.Status.DRAFT,
            notes="Initial test order",
        )

        self.detail_url = reverse(
            "order-detail",
            args=[self.order.pk],
        )

    def get_order_payload(self, **overrides):
        """Return a valid order payload for API requests."""

        payload = {
            "order_number": "ORD-2026-002",
            "buyer": self.buyer.pk,
            "order_date": "2026-10-20",
            "delivery_date": "2026-11-15",
            "quantity": 2000,
            "status": "draft",
            "notes": "Test order",
        }

        payload.update(overrides)
        return payload

    def test_list_orders(self):
        """The API should return a paginated order list."""

        response = self.client.get(self.list_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            response.data["results"][0]["order_number"],
            "ORD-2026-001",
        )

    def test_create_order(self):
        """The API should create a new order."""

        payload = self.get_order_payload()

        response = self.client.post(
            self.list_url,
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertTrue(Order.objects.filter(order_number="ORD-2026-002").exists())
        self.assertEqual(
            response.data["buyer_name"],
            "ABC Fashion Ltd.",
        )

    def test_retrieve_order(self):
        """The API should return the selected order."""

        response = self.client.get(self.detail_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            response.data["order_number"],
            "ORD-2026-001",
        )
        self.assertEqual(
            response.data["buyer_name"],
            "ABC Fashion Ltd.",
        )

    def test_partial_update_order_status(self):
        """PATCH should update only the supplied fields."""

        response = self.client.patch(
            self.detail_url,
            {"status": "confirmed"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.order.refresh_from_db()

        self.assertEqual(
            self.order.status,
            Order.Status.CONFIRMED,
        )
        self.assertEqual(self.order.quantity, 1000)

    def test_delete_order(self):
        """The API should delete the selected order."""

        response = self.client.delete(self.detail_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )
        self.assertFalse(Order.objects.filter(pk=self.order.pk).exists())

    def test_duplicate_order_number_is_rejected(self):
        """Order numbers should be unique regardless of case."""

        payload = self.get_order_payload(
            order_number="ord-2026-001",
        )

        response = self.client.post(
            self.list_url,
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn("order_number", response.data)

    def test_inactive_buyer_is_rejected(self):
        """An inactive buyer cannot receive a new order."""

        self.buyer.is_active = False
        self.buyer.save()

        payload = self.get_order_payload()

        response = self.client.post(
            self.list_url,
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn("buyer", response.data)

    def test_delivery_date_before_order_date_is_rejected(self):
        """Delivery date cannot precede order date."""

        payload = self.get_order_payload(
            order_date="2026-10-20",
            delivery_date="2026-10-19",
        )

        response = self.client.post(
            self.list_url,
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn("delivery_date", response.data)

    def test_search_orders_by_order_number(self):
        """Search should find an order by its number."""

        response = self.client.get(
            self.list_url,
            {"search": "ORD-2026-001"},
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            response.data["results"][0]["order_number"],
            "ORD-2026-001",
        )

    def test_filter_orders_by_status(self):
        """Status filter should return matching orders."""

        response = self.client.get(
            self.list_url,
            {"status": "draft"},
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            response.data["results"][0]["status"],
            "draft",
        )

    def test_filter_orders_by_buyer(self):
        """Buyer filter should return that buyer's orders."""

        response = self.client.get(
            self.list_url,
            {"buyer": self.buyer.pk},
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            response.data["results"][0]["buyer"],
            self.buyer.pk,
        )
