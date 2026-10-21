from datetime import date
from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.buyers.models import Buyer
from apps.products.models import Product
from .models import Order, OrderItem



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

    def test_order_response_includes_nested_items(self):
        """Order response should include its items and calculated subtotal."""

        product = Product.objects.create(
            name="Cotton Fabric",
            sku="NESTED-FAB-001",
            unit=Product.Unit.METER,
        )

        OrderItem.objects.create(
            order=self.order,
            product=product,
            quantity=100,
            unit_price="250.00",
        )

        response = self.client.get(self.detail_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(len(response.data["items"]), 1)

        item = response.data["items"][0]

        self.assertEqual(item["product_name"], "Cotton Fabric")
        self.assertEqual(item["quantity"], 100)
        self.assertEqual(item["unit_price"], "250.00")
        self.assertEqual(item["subtotal"], "25000.00")

    def test_order_financial_summary(self):
        """Order response should include item count and total amount."""

        first_product = Product.objects.create(
            name="Cotton Fabric",
            sku="SUMMARY-FAB-001",
            unit=Product.Unit.METER,
        )

        second_product = Product.objects.create(
            name="Sewing Thread",
            sku="SUMMARY-THR-001",
            unit=Product.Unit.METER,
        )

        OrderItem.objects.create(
            order=self.order,
            product=first_product,
            quantity=100,
            unit_price="250.00",
        )

        OrderItem.objects.create(
            order=self.order,
            product=second_product,
            quantity=100,
            unit_price="150.00",
        )

        response = self.client.get(self.detail_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(response.data["total_items"], 2)
        self.assertEqual(
            response.data["total_amount"],
            Decimal("40000.00"),
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


class OrderItemAPITests(APITestCase):
    """Test OrderItem API CRUD operations and validation."""

    def setUp(self):
        self.buyer = Buyer.objects.create(
            name="Test Fashion Ltd.",
            email="test@example.com",
            country="US",
        )

        self.order = Order.objects.create(
            order_number="TEST-ORD-001",
            buyer=self.buyer,
            order_date=date(2026, 10, 20),
            delivery_date=date(2026, 11, 10),
            quantity=1000,
            status=Order.Status.DRAFT,
        )

        self.product = Product.objects.create(
            name="Cotton Fabric",
            sku="TEST-FAB-001",
            unit=Product.Unit.METER,
        )

        self.second_product = Product.objects.create(
            name="Polyester Fabric",
            sku="TEST-FAB-002",
            unit=Product.Unit.METER,
        )

        self.list_url = reverse("order-item-list")

        self.item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=100,
            unit_price="250.00",
        )

        self.detail_url = reverse(
            "order-item-detail",
            args=[self.item.pk],
        )

    def get_item_payload(self, **overrides):
        """Return valid data for creating an order item."""

        payload = {
            "order": self.order.pk,
            "product": self.second_product.pk,
            "quantity": 50,
            "unit_price": "300.00",
        }

        payload.update(overrides)
        return payload

    def test_list_order_items(self):
        response = self.client.get(self.list_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            response.data["results"][0]["product_name"],
            "Cotton Fabric",
        )

    def test_create_order_item(self):
        response = self.client.post(
            self.list_url,
            self.get_item_payload(),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertTrue(
            OrderItem.objects.filter(
                order=self.order,
                product=self.second_product,
            ).exists()
        )
        self.assertEqual(response.data["subtotal"], "15000.00")

    def test_retrieve_order_item(self):
        response = self.client.get(self.detail_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(response.data["quantity"], 100)
        self.assertEqual(response.data["subtotal"], "25000.00")

    def test_partial_update_order_item(self):
        response = self.client.patch(
            self.detail_url,
            {"quantity": 120},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, 120)
        self.assertEqual(self.item.unit_price, 250)

    def test_delete_order_item(self):
        response = self.client.delete(self.detail_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )
        self.assertFalse(OrderItem.objects.filter(pk=self.item.pk).exists())

    def test_duplicate_product_in_same_order_is_rejected(self):
        payload = self.get_item_payload(
            product=self.product.pk,
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

    def test_zero_quantity_is_rejected(self):
        response = self.client.post(
            self.list_url,
            self.get_item_payload(quantity=0),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_negative_unit_price_is_rejected(self):
        response = self.client.post(
            self.list_url,
            self.get_item_payload(unit_price="-10.00"),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_filter_order_items_by_order(self):
        response = self.client.get(
            self.list_url,
            {"order": self.order.pk},
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(response.data["count"], 1)
