from django.db import IntegrityError, transaction
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Buyer


class BuyerAPITests(APITestCase):
    """Test Buyer API CRUD operations and validation."""

    def setUp(self):
        """Create a buyer used by the API tests."""
        self.buyer = Buyer.objects.create(
            name="ABC Fashion Ltd.",
            contact_person="John Smith",
            email="john@example.com",
            country="US",
        )
        self.list_url = "/api/buyers/"
        self.detail_url = f"/api/buyers/{self.buyer.pk}/"

    def test_search_buyers_by_name(self):
        """Search should find buyers by company name."""
        response = self.client.get(
            self.list_url,
            {"search": "ABC Fashion"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            response.data["results"][0]["name"],
            "ABC Fashion Ltd.",
        )

    def test_filter_buyers_by_country(self):
        """Country filter should return matching buyers."""
        response = self.client.get(
            self.list_url,
            {"country": "US"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            response.data["results"][0]["country"],
            "US",
        )

    def test_filter_buyers_by_active_status(self):
        """Active status filter should return active buyers."""
        response = self.client.get(
            self.list_url,
            {"is_active": "true"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertTrue(response.data["results"][0]["is_active"])

    def test_list_buyers(self):
        """The API should return a paginated buyer list."""
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)

    def test_create_buyer(self):
        """The API should create a new buyer."""
        payload = {
            "name": "Global Apparel Trading Ltd.",
            "contact_person": "Sarah Johnson",
            "email": "sarah@example.com",
            "phone": "01700000000",
            "address": "Dhaka, Bangladesh",
            "country": "BD",
            "is_active": True,
        }

        response = self.client.post(
            self.list_url,
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Buyer.objects.filter(name="Global Apparel Trading Ltd.").exists()
        )

    def test_retrieve_buyer(self):
        """The API should return one buyer."""
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "ABC Fashion Ltd.")

    def test_partial_update_buyer(self):
        """The API should update only the supplied fields."""
        response = self.client.patch(
            self.detail_url,
            {"contact_person": "Emily Wilson"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.buyer.refresh_from_db()
        self.assertEqual(
            self.buyer.contact_person,
            "Emily Wilson",
        )

    def test_delete_buyer(self):
        """The API should delete the selected buyer."""
        response = self.client.delete(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Buyer.objects.filter(pk=self.buyer.pk).exists())

    def test_duplicate_name_is_rejected(self):
        """The API should reject a case-insensitive duplicate name."""
        response = self.client.post(
            self.list_url,
            {"name": "abc fashion ltd."},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn("name", response.data)


class BuyerDatabaseConstraintTests(TestCase):
    """Test database-level buyer name uniqueness."""

    def test_case_insensitive_duplicate_is_rejected(self):
        """The database should reject names differing only by case."""
        Buyer.objects.create(name="ABC Fashion Ltd.")

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Buyer.objects.create(name="abc fashion ltd.")

    """
    APITestCase	- Django REST Framework API পরীক্ষা করে
    setUp()	- প্রতিটি API test-এর আগে নতুন test buyer তৈরি করে
    self.client.get() - GET request পাঠায়
    self.client.post() - POST request পাঠায়
    self.client.patch() - PATCH request পাঠায়
    self.client.delete() -	DELETE request পাঠায়
    assertEqual()	- প্রত্যাশিত ও প্রকৃত ফলাফল তুলনা করে
    refresh_from_db() -	database থেকে সর্বশেষ record আবার পড়ে
    transaction.atomic() -	database constraint failure-কে নিরাপদভাবে আলাদা transaction-এ পরীক্ষা করে
    """
