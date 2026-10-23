from decimal import Decimal

from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Product, ProductCategory, StockMovement
from .services import create_stock_movement


class ProductCategoryAPITests(APITestCase):
    list_url = "/api/categories/"

    def setUp(self):
        self.category = ProductCategory.objects.create(
            name="Raw Materials",
            category_type=ProductCategory.CategoryType.RAW_MATERIAL,
            description="Materials used in garment production",
            is_active=True,
        )

    def test_list_categories(self):
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "Raw Materials")

    def test_create_category(self):
        data = {
            "name": "Accessories",
            "category_type": "accessory",
            "description": "Garment accessories",
            "is_active": True,
        }

        response = self.client.post(
            self.list_url,
            data,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(ProductCategory.objects.filter(name="Accessories").exists())

    def test_retrieve_category(self):
        response = self.client.get(f"{self.list_url}{self.category.pk}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Raw Materials")

    def test_update_category(self):
        response = self.client.patch(
            f"{self.list_url}{self.category.pk}/",
            {"name": "Fabric and Raw Materials"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.category.refresh_from_db()
        self.assertEqual(self.category.name, "Fabric and Raw Materials")

    def test_delete_category(self):
        response = self.client.delete(f"{self.list_url}{self.category.pk}/")

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )
        self.assertFalse(ProductCategory.objects.filter(pk=self.category.pk).exists())

    def test_duplicate_category_name_is_rejected_case_insensitively(self):
        data = {
            "name": "raw materials",
            "category_type": "accessory",
            "description": "",
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
        self.assertEqual(ProductCategory.objects.count(), 1)

    def test_filter_categories_by_type(self):
        response = self.client.get(
            self.list_url,
            {"category_type": "raw_material"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)


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

    def test_low_stock_endpoint_excludes_inactive_products(self):
        self.product.current_stock = Decimal("0.000")
        self.product.minimum_stock_level = Decimal("10.000")
        self.product.is_active = False
        self.product.save()

        response = self.client.get(f"{self.list_url}low-stock/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)

    def test_low_stock_endpoint_returns_products_at_or_below_minimum(self):
        self.product.current_stock = Decimal("5.000")
        self.product.minimum_stock_level = Decimal("10.000")
        self.product.save()

        response = self.client.get(f"{self.list_url}low-stock/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["sku"], "FAB-001")

    def test_low_stock_endpoint_excludes_products_above_minimum(self):
        self.product.current_stock = Decimal("15.000")
        self.product.minimum_stock_level = Decimal("10.000")
        self.product.save()

        response = self.client.get(f"{self.list_url}low-stock/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)

    def test_low_stock_endpoint_includes_products_at_exact_minimum(self):
        self.product.current_stock = Decimal("10.000")
        self.product.minimum_stock_level = Decimal("10.000")
        self.product.save()

        response = self.client.get(f"{self.list_url}low-stock/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["sku"], "FAB-001")

    def test_list_products(self):
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["sku"], "FAB-001")

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

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Product.objects.filter(sku="FAB-002").exists())

    def test_create_product_ignores_direct_current_stock_input(self):
        data = {
            "sku": "FAB-003",
            "name": "Denim Fabric",
            "description": "Denim fabric",
            "unit": "meter",
            "current_stock": "100.000",
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

        product = Product.objects.get(sku="FAB-003")
        self.assertEqual(product.current_stock, Decimal("0.000"))

    def test_update_product_ignores_direct_current_stock_input(self):
        self.product.current_stock = Decimal("10.000")
        self.product.save(update_fields=["current_stock"])

        response = self.client.patch(
            f"{self.list_url}{self.product.pk}/",
            {"current_stock": "100.000"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, Decimal("10.000"))

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
        self.assertEqual(self.product.name, "Premium Cotton Fabric")

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


class StockMovementServiceTests(APITestCase):
    def setUp(self):
        self.category = ProductCategory.objects.create(
            name="Test Raw Materials",
            category_type=ProductCategory.CategoryType.RAW_MATERIAL,
        )

        self.product = Product.objects.create(
            sku="STOCK-TEST-001",
            name="Test Cotton Fabric",
            category=self.category,
            unit=Product.Unit.METER,
            current_stock=Decimal("10.000"),
            minimum_stock_level=Decimal("2.000"),
        )

    def test_stock_in_increases_current_stock(self):
        create_stock_movement(
            product_id=self.product.pk,
            movement_type=StockMovement.MovementType.STOCK_IN,
            quantity=Decimal("5.000"),
        )

        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, Decimal("15.000"))

    def test_stock_out_decreases_current_stock(self):
        create_stock_movement(
            product_id=self.product.pk,
            movement_type=StockMovement.MovementType.STOCK_OUT,
            quantity=Decimal("3.000"),
        )

        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, Decimal("7.000"))

    def test_stock_out_rejects_zero_quantity(self):
        with self.assertRaises(ValidationError):
            create_stock_movement(
                product_id=self.product.pk,
                movement_type=StockMovement.MovementType.STOCK_OUT,
                quantity=Decimal("0.000"),
            )

        self.product.refresh_from_db()

        self.assertEqual(self.product.current_stock, Decimal("10.000"))
        self.assertEqual(
            StockMovement.objects.filter(product=self.product).count(),
            0,
        )

    def test_stock_out_rejects_negative_quantity(self):
        with self.assertRaises(ValidationError):
            create_stock_movement(
                product_id=self.product.pk,
                movement_type=StockMovement.MovementType.STOCK_OUT,
                quantity=Decimal("-3.000"),
            )

        self.product.refresh_from_db()

        self.assertEqual(self.product.current_stock, Decimal("10.000"))
        self.assertEqual(
            StockMovement.objects.filter(product=self.product).count(),
            0,
        )

    def test_stock_out_rejects_insufficient_stock(self):
        with self.assertRaises(ValidationError):
            create_stock_movement(
                product_id=self.product.pk,
                movement_type=StockMovement.MovementType.STOCK_OUT,
                quantity=Decimal("11.000"),
            )

        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, Decimal("10.000"))
        self.assertEqual(
            StockMovement.objects.filter(product=self.product).count(),
            0,
        )

    def test_adjustment_updates_current_stock(self):
        movement = create_stock_movement(
            product_id=self.product.pk,
            movement_type=StockMovement.MovementType.ADJUSTMENT,
            quantity=Decimal("-2.000"),
            note="Physical stock count correction",
        )

        self.product.refresh_from_db()

        self.assertEqual(self.product.current_stock, Decimal("8.000"))
        self.assertEqual(
            movement.note,
            "Physical stock count correction",
        )

    def test_adjustment_cannot_make_stock_negative(self):
        with self.assertRaises(ValidationError):
            create_stock_movement(
                product_id=self.product.id,
                movement_type=StockMovement.MovementType.ADJUSTMENT,
                quantity=Decimal("-11.000"),
                note="Incorrect stock count",
            )

        self.product.refresh_from_db()

        self.assertEqual(self.product.current_stock, Decimal("10.000"))
        self.assertEqual(StockMovement.objects.count(), 0)

    def test_adjustment_without_reason_is_rejected(self):
        with self.assertRaises(ValidationError):
            create_stock_movement(
                product_id=self.product.pk,
                movement_type=StockMovement.MovementType.ADJUSTMENT,
                quantity=Decimal("-2.000"),
            )

        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, Decimal("10.000"))
        self.assertEqual(
            StockMovement.objects.filter(product=self.product).count(),
            0,
        )

    def test_adjustment_with_whitespace_reason_is_rejected(self):
        with self.assertRaises(ValidationError):
            create_stock_movement(
                product_id=self.product.pk,
                movement_type=StockMovement.MovementType.ADJUSTMENT,
                quantity=Decimal("-2.000"),
                note="   ",
            )

        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, Decimal("10.000"))
        self.assertEqual(
            StockMovement.objects.filter(product=self.product).count(),
            0,
        )

    def test_zero_adjustment_is_rejected(self):
        with self.assertRaises(ValidationError):
            create_stock_movement(
                product_id=self.product.pk,
                movement_type=StockMovement.MovementType.ADJUSTMENT,
                quantity=Decimal("0.000"),
                note="Physical stock count correction",
            )

        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, Decimal("10.000"))

    def test_zero_stock_in_is_rejected(self):
        with self.assertRaises(ValidationError):
            create_stock_movement(
                product_id=self.product.pk,
                movement_type=StockMovement.MovementType.STOCK_IN,
                quantity=Decimal("0.000"),
            )

        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, Decimal("10.000"))


class StockMovementAPITests(APITestCase):
    def setUp(self):
        self.category = ProductCategory.objects.create(
            name="API Test Raw Materials",
            category_type=ProductCategory.CategoryType.RAW_MATERIAL,
        )

        self.product = Product.objects.create(
            sku="STOCK-API-001",
            name="API Test Cotton Fabric",
            category=self.category,
            unit=Product.Unit.METER,
            current_stock=Decimal("10.000"),
            minimum_stock_level=Decimal("2.000"),
        )

        self.url = "/api/stock-movements/"

    def test_stock_movement_history_returns_movement_details(self):
        create_response = self.client.post(
            self.url,
            {
                "product": self.product.pk,
                "movement_type": "stock_in",
                "quantity": "5.000",
                "note": "History API test",
            },
            format="json",
        )

        self.assertEqual(
            create_response.status_code,
            status.HTTP_201_CREATED,
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

        movement = response.data["results"][0]

        self.assertEqual(movement["product"], self.product.pk)
        self.assertEqual(movement["product_sku"], "STOCK-API-001")
        self.assertEqual(movement["product_name"], "API Test Cotton Fabric")
        self.assertEqual(movement["movement_type"], "stock_in")
        self.assertEqual(movement["quantity"], "5.000")
        self.assertEqual(movement["note"], "History API test")
        self.assertIn("created_at", movement)

    def test_stock_movement_history_orders_by_quantity_descending(self):
        first_response = self.client.post(
            self.url,
            {
                "product": self.product.pk,
                "movement_type": "stock_in",
                "quantity": "2.000",
                "note": "Small fabric receipt",
            },
            format="json",
        )

        second_response = self.client.post(
            self.url,
            {
                "product": self.product.pk,
                "movement_type": "stock_in",
                "quantity": "8.000",
                "note": "Large fabric receipt",
            },
            format="json",
        )

        self.assertEqual(
            first_response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertEqual(
            second_response.status_code,
            status.HTTP_201_CREATED,
        )

        response = self.client.get(
            self.url,
            {"ordering": "-quantity"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)

        movements = response.data["results"]

        self.assertEqual(movements[0]["quantity"], "8.000")
        self.assertEqual(movements[1]["quantity"], "2.000")

    def test_stock_movement_history_filters_by_movement_type(self):
        stock_in_response = self.client.post(
            self.url,
            {
                "product": self.product.pk,
                "movement_type": "stock_in",
                "quantity": "5.000",
                "note": "Incoming fabric",
            },
            format="json",
        )

        stock_out_response = self.client.post(
            self.url,
            {
                "product": self.product.pk,
                "movement_type": "stock_out",
                "quantity": "3.000",
                "note": "Issued fabric",
            },
            format="json",
        )

        self.assertEqual(
            stock_in_response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertEqual(
            stock_out_response.status_code,
            status.HTTP_201_CREATED,
        )

        response = self.client.get(
            self.url,
            {"movement_type": "stock_in"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            response.data["results"][0]["movement_type"],
            "stock_in",
        )
        self.assertEqual(
            response.data["results"][0]["note"],
            "Incoming fabric",
        )

    def test_stock_movement_history_filters_by_product(self):
        another_product = Product.objects.create(
            sku="STOCK-API-002",
            name="API Test Sewing Thread",
            category=self.category,
            unit=Product.Unit.PIECE,
            current_stock=Decimal("20.000"),
            minimum_stock_level=Decimal("5.000"),
        )

        first_response = self.client.post(
            self.url,
            {
                "product": self.product.pk,
                "movement_type": "stock_in",
                "quantity": "5.000",
                "note": "Cotton fabric shipment alpha",
            },
            format="json",
        )

        second_response = self.client.post(
            self.url,
            {
                "product": another_product.pk,
                "movement_type": "stock_in",
                "quantity": "10.000",
                "note": "Sewing thread received",
            },
            format="json",
        )

        self.assertEqual(
            first_response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertEqual(
            second_response.status_code,
            status.HTTP_201_CREATED,
        )

        response = self.client.get(
            self.url,
            {"product": self.product.pk},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

        movement = response.data["results"][0]

        self.assertEqual(movement["product"], self.product.pk)
        self.assertEqual(
            movement["note"],
            "Cotton fabric shipment alpha",
        )

    def test_stock_movement_history_searches_by_note(self):
        first_response = self.client.post(
            self.url,
            {
                "product": self.product.pk,
                "movement_type": "stock_in",
                "quantity": "5.000",
                "note": "Cotton fabric shipment alpha",
            },
            format="json",
        )

        second_response = self.client.post(
            self.url,
            {
                "product": self.product.pk,
                "movement_type": "stock_in",
                "quantity": "2.000",
                "note": "Polyester fabric received",
            },
            format="json",
        )

        self.assertEqual(
            first_response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertEqual(
            second_response.status_code,
            status.HTTP_201_CREATED,
        )

        response = self.client.get(
            self.url,
            {"search": "alpha"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

        movement = response.data["results"][0]

        self.assertEqual(
            movement["note"],
            "Cotton fabric shipment alpha",
        )

    def test_stock_in_api_increases_current_stock(self):
        response = self.client.post(
            self.url,
            {
                "product": self.product.pk,
                "movement_type": "stock_in",
                "quantity": "5.000",
                "note": "API stock in test",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, Decimal("15.000"))

    def test_stock_out_api_decreases_current_stock(self):
        response = self.client.post(
            self.url,
            {
                "product": self.product.pk,
                "movement_type": "stock_out",
                "quantity": "3.000",
                "note": "API stock out test",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, Decimal("7.000"))

    def test_insufficient_stock_returns_400(self):
        response = self.client.post(
            self.url,
            {
                "product": self.product.pk,
                "movement_type": "stock_out",
                "quantity": "11.000",
                "note": "Insufficient stock API test",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, Decimal("10.000"))
        self.assertEqual(
            StockMovement.objects.filter(product=self.product).count(),
            0,
        )

    def test_adjustment_api_updates_current_stock(self):
        response = self.client.post(
            self.url,
            {
                "product": self.product.pk,
                "movement_type": "adjustment",
                "quantity": "-2.000",
                "note": "Physical stock count correction",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, Decimal("8.000"))

    def test_adjustment_api_without_reason_returns_400(self):
        response = self.client.post(
            self.url,
            {
                "product": self.product.pk,
                "movement_type": "adjustment",
                "quantity": "-2.000",
                "note": "",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, Decimal("10.000"))
        self.assertEqual(
            StockMovement.objects.filter(product=self.product).count(),
            0,
        )

    def test_invalid_quantity_returns_400_without_changing_stock(self):
        response = self.client.post(
            self.url,
            {
                "product": self.product.pk,
                "movement_type": "stock_in",
                "quantity": "abc",
                "note": "Invalid quantity API test",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.product.refresh_from_db()
        self.assertEqual(
            self.product.current_stock,
            Decimal("10.000"),
        )

        self.assertEqual(
            StockMovement.objects.filter(product=self.product).count(),
            0,
        )

    def test_invalid_movement_type_returns_400_without_changing_stock(self):
        response = self.client.post(
            self.url,
            {
                "product": self.product.pk,
                "movement_type": "invalid_type",
                "quantity": "5.000",
                "note": "Invalid movement type API test",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.product.refresh_from_db()
        self.assertEqual(
            self.product.current_stock,
            Decimal("10.000"),
        )

        self.assertEqual(
            StockMovement.objects.filter(product=self.product).count(),
            0,
        )
