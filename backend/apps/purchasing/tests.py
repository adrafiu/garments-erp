from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse

from apps.products.models import Product
from apps.suppliers.models import Supplier

from .models import PurchaseOrder, PurchaseOrderItem


class PurchaseOrderAPITests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser",
            password="test-password-123",
        )

        self.client.force_authenticate(user=self.user)
        self.supplier = Supplier.objects.create(
            name="ABC Garments",
            contact_person="Rahim Ahmed",
            email="rahim@example.com",
            phone="01712345678",
            address="Dhaka, Bangladesh",
            country="BD",
            is_active=True,
        )

        self.product = Product.objects.create(
            sku="FAB-001",
            name="Cotton Fabric",
            description="100% cotton fabric",
            unit=Product.Unit.METER,
            is_active=True,
        )

        self.list_url = reverse("purchase-order-list")
        self.item_list_url = reverse("purchase-order-item-list")

        self.valid_payload = {
            "po_number": "PO-2026-001",
            "supplier": self.supplier.pk,
            "order_date": "2026-10-22",
            "expected_delivery_date": "2026-10-30",
            "status": "draft",
            "notes": "Test purchase order",
            "items": [
                {
                    "product": self.product.pk,
                    "quantity": "100.000",
                    "unit_price": "12.50",
                }
            ],
        }

    def create_purchase_order(self):
        """Create a purchase order using the API."""
        return self.client.post(
            self.list_url,
            self.valid_payload,
            format="json",
        )

    def test_list_purchase_orders(self):
        response = self.create_purchase_order()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            response.data["results"][0]["po_number"],
            "PO-2026-001",
        )

    def test_create_purchase_order_with_items(self):
        response = self.create_purchase_order()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PurchaseOrder.objects.count(), 1)
        self.assertEqual(PurchaseOrderItem.objects.count(), 1)

        purchase_order = PurchaseOrder.objects.get(po_number="PO-2026-001")

        self.assertEqual(
            purchase_order.supplier,
            self.supplier,
        )
        self.assertEqual(
            purchase_order.items.first().quantity,
            self._decimal("100.000"),
        )

        self.assertEqual(
            response.data["supplier_name"],
            "ABC Garments",
        )
        self.assertEqual(
            response.data["items"][0]["product_name"],
            "Cotton Fabric",
        )
        self.assertEqual(
            response.data["items"][0]["subtotal"],
            "1250.00000",
        )

    def test_retrieve_purchase_order(self):
        create_response = self.create_purchase_order()
        self.assertEqual(
            create_response.status_code,
            status.HTTP_201_CREATED,
        )

        purchase_order_id = create_response.data["id"]
        detail_url = reverse(
            "purchase-order-detail",
            args=[purchase_order_id],
        )

        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["po_number"],
            "PO-2026-001",
        )

    def test_update_purchase_order_notes(self):
        create_response = self.create_purchase_order()
        purchase_order_id = create_response.data["id"]

        detail_url = reverse(
            "purchase-order-detail",
            args=[purchase_order_id],
        )

        response = self.client.patch(
            detail_url,
            {"notes": "Updated purchase order notes"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["notes"],
            "Updated purchase order notes",
        )

    def test_reject_expected_delivery_date_before_order_date(self):
        payload = self.valid_payload.copy()
        payload["expected_delivery_date"] = "2026-10-20"

        response = self.client.post(
            self.list_url,
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn(
            "expected_delivery_date",
            response.data,
        )

    def test_reject_inactive_supplier(self):
        inactive_supplier = Supplier.objects.create(
            name="Inactive Supplier",
            contact_person="Test Person",
            email="inactive@example.com",
            phone="01700000000",
            address="Dhaka, Bangladesh",
            country="BD",
            is_active=False,
        )

        payload = self.valid_payload.copy()
        payload["po_number"] = "PO-2026-002"
        payload["supplier"] = inactive_supplier.pk

        response = self.client.post(
            self.list_url,
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn("supplier", response.data)

    def test_reject_inactive_product(self):
        inactive_product = Product.objects.create(
            sku="FAB-002",
            name="Inactive Fabric",
            description="Inactive product for testing",
            unit=Product.Unit.METER,
            is_active=False,
        )

        payload = self.valid_payload.copy()
        payload["items"] = [
            {
                "product": inactive_product.pk,
                "quantity": "10.000",
                "unit_price": "5.00",
            }
        ]

        response = self.client.post(
            self.list_url,
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn("items", response.data)

    def test_reject_duplicate_product_in_same_purchase_order(self):
        payload = self.valid_payload.copy()
        payload["items"] = [
            {
                "product": self.product.pk,
                "quantity": "10.000",
                "unit_price": "5.00",
            },
            {
                "product": self.product.pk,
                "quantity": "20.000",
                "unit_price": "6.00",
            },
        ]

        response = self.client.post(
            self.list_url,
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn("items", response.data)

    def test_reject_zero_quantity(self):
        payload = self.valid_payload.copy()
        payload["items"] = [
            {
                "product": self.product.pk,
                "quantity": "0",
                "unit_price": "12.50",
            }
        ]

        response = self.client.post(
            self.list_url,
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_reject_negative_unit_price(self):
        payload = self.valid_payload.copy()
        payload["items"] = [
            {
                "product": self.product.pk,
                "quantity": "10.000",
                "unit_price": "-1.00",
            }
        ]

        response = self.client.post(
            self.list_url,
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_reject_status_change_through_generic_update(self):
        create_response = self.create_purchase_order()
        purchase_order_id = create_response.data["id"]

        detail_url = reverse(
            "purchase-order-detail",
            args=[purchase_order_id],
        )

        response = self.client.patch(
            detail_url,
            {"status": "approved"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        purchase_order = PurchaseOrder.objects.get(pk=purchase_order_id)
        self.assertEqual(purchase_order.status, "draft")

    def test_reject_duplicate_purchase_order_number(self):
        first_response = self.create_purchase_order()
        self.assertEqual(
            first_response.status_code,
            status.HTTP_201_CREATED,
        )

        response = self.client.post(
            self.list_url,
            self.valid_payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(PurchaseOrder.objects.count(), 1)

    def test_list_purchase_order_items(self):
        create_response = self.create_purchase_order()
        self.assertEqual(
            create_response.status_code,
            status.HTTP_201_CREATED,
        )

        response = self.client.get(self.item_list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            response.data["results"][0]["product_name"],
            "Cotton Fabric",
        )

    @staticmethod
    def _decimal(value):
        from decimal import Decimal

        return Decimal(value)
