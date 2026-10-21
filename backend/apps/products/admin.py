from django.contrib import admin

from .models import Product, ProductCategory, StockMovement


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category_type",
        "is_active",
        "created_at",
    )

    list_filter = (
        "category_type",
        "is_active",
    )

    search_fields = (
        "name",
        "description",
    )

    ordering = (
        "name",
        "id",
    )

    list_editable = ("is_active",)

    readonly_fields = (
        "created_at",
        "updated_at",
    )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "sku",
        "name",
        "category",
        "unit",
        "current_stock",
        "minimum_stock_level",
        "is_active",
        "created_at",
    )

    list_filter = (
        "category",
        "unit",
        "is_active",
    )

    search_fields = (
        "sku",
        "name",
        "description",
    )

    ordering = (
        "name",
        "id",
    )

    list_editable = ("is_active",)

    readonly_fields = (
        "created_at",
        "updated_at",
    )


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "movement_type",
        "quantity",
        "created_at",
    )

    list_filter = ("movement_type", "created_at")

    search_fields = ("product__sku", "product__name", "note")

    ordering = ("-created_at", "-id")

    readonly_fields = ("created_at",)

    """
    list_display: প্রতিটি movement-এর পণ্য, ধরন, পরিমাণ ও সময় দেখাবে।
    list_filter: Stock In, Stock Out ও Adjustment অনুযায়ী filter করা যাবে।
    search_fields: SKU, product name বা note দিয়ে খোঁজা যাবে।
    readonly_fields: movement তৈরির সময় স্বয়ংক্রিয় timestamp সরাসরি পরিবর্তন করা যাবে না।
    """
