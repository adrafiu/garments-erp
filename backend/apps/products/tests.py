from rest_framework import status
from rest_framework.test import APITestCase

from .models import Product


class ProductAPITests(APITestCase):
    list_url = "/api/products/"

    def setUp(self):
        self.product = Product.objects.create(
            sku="FAB-001",
            name="Cotton Fabric",
            description="100% cotton fabric",
            unit=Product.Unit.METER,
            is_active=True,
        )

    def test_list_products(self):
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            response.data["results"][0]["sku"],
            "FAB-001",
        )

    def test_create_product(self):
        data = {
            "sku": "FAB-002",
            "name": "Polyester Fabric",
            "description": "Polyester fabric",
            "unit": "meter",
            "is_active": True,
        }

        response = self.client.post(
            self.list_url,
            data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertTrue(Product.objects.filter(sku="FAB-002").exists())

    def test_retrieve_product(self):
        response = self.client.get(f"{self.list_url}{self.product.pk}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Cotton Fabric")

    def test_update_product(self):
        response = self.client.patch(
            f"{self.list_url}{self.product.pk}/",
            {"name": "Premium Cotton Fabric"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.product.refresh_from_db()
        self.assertEqual(
            self.product.name,
            "Premium Cotton Fabric",
        )

    def test_delete_product(self):
        response = self.client.delete(f"{self.list_url}{self.product.pk}/")

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )
        self.assertFalse(Product.objects.filter(pk=self.product.pk).exists())

    def test_search_products_by_name(self):
        response = self.client.get(
            self.list_url,
            {"search": "Cotton"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_filter_products_by_unit(self):
        response = self.client.get(
            self.list_url,
            {"unit": "meter"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_filter_products_by_active_status(self):
        response = self.client.get(
            self.list_url,
            {"is_active": "true"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_duplicate_sku_is_rejected_case_insensitively(self):
        data = {
            "sku": "fab-001",
            "name": "Duplicate Fabric",
            "description": "",
            "unit": "meter",
            "is_active": True,
        }

        response = self.client.post(
            self.list_url,
            data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(Product.objects.count(), 1)

    def test_update_with_same_sku_is_allowed(self):
        response = self.client.patch(
            f"{self.list_url}{self.product.pk}/",
            {"sku": "FAB-001"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
