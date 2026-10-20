from django.contrib import admin

from django.contrib import admin
from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "sku",
        "name",
        "unit",
        "is_active",
        "created_at",
    )

    list_filter = (
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
