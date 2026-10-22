from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Supplier


class SupplierAPITests(APITestCase):
    def setUp(self):
        self.list_url = reverse("supplier-list")

        self.supplier = Supplier.objects.create(
            name="ABC Garments",
            contact_person="Rahim Ahmed",
            email="rahim@example.com",
            phone="01712345678",
            address="Dhaka, Bangladesh",
            country="BD",
            is_active=True,
        )

        self.valid_payload = {
            "name": "XYZ Textiles",
            "contact_person": "Karim Ahmed",
            "email": "karim@example.com",
            "phone": "01812345678",
            "address": "Chattogram, Bangladesh",
            "country": "BD",
            "is_active": True,
        }

    def get_results(self, response):
        if isinstance(response.data, dict) and "results" in response.data:
            return response.data["results"]

        return response.data

    def test_list_suppliers(self):
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_create_supplier(self):
        response = self.client.post(
            self.list_url,
            self.valid_payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Supplier.objects.count(), 2)
        self.assertEqual(
            response.data["name"],
            "XYZ Textiles",
        )

    def test_retrieve_supplier(self):
        url = reverse("supplier-detail", args=[self.supplier.pk])

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "ABC Garments")

    def test_update_supplier(self):
        url = reverse("supplier-detail", args=[self.supplier.pk])

        response = self.client.patch(
            url,
            {"name": "Updated Garments"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.supplier.refresh_from_db()
        self.assertEqual(self.supplier.name, "Updated Garments")

    def test_delete_supplier(self):
        url = reverse("supplier-detail", args=[self.supplier.pk])

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            Supplier.objects.filter(pk=self.supplier.pk).exists()
        )

    def test_search_supplier_by_name(self):
        response = self.client.get(
            self.list_url,
            {"search": "ABC"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = self.get_results(response)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "ABC Garments")

    def test_filter_active_suppliers(self):
        Supplier.objects.create(
            name="Inactive Supplier",
            is_active=False,
        )

        response = self.client.get(
            self.list_url,
            {"is_active": "true"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = self.get_results(response)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "ABC Garments")

    def test_filter_suppliers_by_country(self):
        Supplier.objects.create(
            name="Foreign Supplier",
            country="US",
        )

        response = self.client.get(
            self.list_url,
            {"country": "BD"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = self.get_results(response)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "ABC Garments")

    def test_order_suppliers_by_name(self):
        Supplier.objects.create(name="Apex Textiles")
        Supplier.objects.create(name="Zenith Fabrics")

        response = self.client.get(
            self.list_url,
            {"ordering": "name"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = self.get_results(response)
        names = [item["name"] for item in results]

        self.assertEqual(names, sorted(names))

    def test_duplicate_supplier_name_is_rejected_case_insensitively(self):
        payload = {
            **self.valid_payload,
            "name": "abc garments",
        }

        response = self.client.post(
            self.list_url,
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(Supplier.objects.count(), 1)

    def test_supplier_name_is_trimmed(self):
        payload = {
            **self.valid_payload,
            "name": "  New Garments  ",
        }

        response = self.client.post(
            self.list_url,
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "New Garments")

    def test_create_supplier_without_name_is_rejected(self):
        payload = {
            **self.valid_payload,
            "name": "",
        }

        response = self.client.post(
            self.list_url,
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
