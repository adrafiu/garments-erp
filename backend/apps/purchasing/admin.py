from django.contrib import admin

from .models import PurchaseOrder, PurchaseOrderItem


class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 0
    autocomplete_fields = ["product"]


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = [
        "po_number",
        "supplier",
        "order_date",
        "expected_delivery_date",
        "status",
    ]

    list_filter = [
        "status",
        "order_date",
        "expected_delivery_date",
    ]

    search_fields = [
        "po_number",
        "supplier__name",
    ]

    readonly_fields = [
        "created_at",
        "updated_at",
    ]

    inlines = [PurchaseOrderItemInline]


@admin.register(PurchaseOrderItem)
class PurchaseOrderItemAdmin(admin.ModelAdmin):
    list_display = [
        "purchase_order",
        "product",
        "quantity",
        "unit_price",
    ]

    list_filter = [
        "purchase_order__status",
    ]

    search_fields = [
        "purchase_order__po_number",
        "product__name",
        "product__sku",
    ]

    autocomplete_fields = [
        "purchase_order",
        "product",
    ]
