from django.utils import timezone
from rest_framework import serializers

from apps.products.models import Product
from apps.suppliers.models import Supplier

from .models import PurchaseOrder, PurchaseOrderItem


class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(
        source="product.name",
        read_only=True,
    )

    subtotal = serializers.DecimalField(
        max_digits=28,
        decimal_places=5,
        read_only=True,
    )

    class Meta:
        model = PurchaseOrderItem
        fields = [
            "id",
            "product",
            "product_name",
            "quantity",
            "unit_price",
            "subtotal",
        ]
        read_only_fields = ["id", "product_name", "subtotal"]

    def validate_product(self, value):
        if not value.is_active:
            raise serializers.ValidationError("Cannot order an inactive product.")
        return value

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value

    def validate_unit_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Unit price cannot be negative.")
        return value


class PurchaseOrderSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(
        source="supplier.name",
        read_only=True,
    )

    items = PurchaseOrderItemSerializer(many=True)

    class Meta:
        model = PurchaseOrder
        fields = [
            "id",
            "po_number",
            "supplier",
            "supplier_name",
            "order_date",
            "expected_delivery_date",
            "status",
            "notes",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "supplier_name",
            "created_at",
            "updated_at",
        ]

    def validate_supplier(self, value):
        if not value.is_active:
            raise serializers.ValidationError(
                "Cannot create a purchase order for an inactive supplier."
            )
        return value

    def validate(self, attrs):
        order_date = attrs.get(
            "order_date",
            getattr(self.instance, "order_date", None),
        )
        expected_date = attrs.get(
            "expected_delivery_date",
            getattr(self.instance, "expected_delivery_date", None),
        )

        if order_date and expected_date and expected_date < order_date:
            raise serializers.ValidationError(
                {
                    "expected_delivery_date": (
                        "Expected delivery date cannot be before order date."
                    )
                }
            )

        items = attrs.get("items")

        if items is not None:
            product_ids = [item["product"].id for item in items]

            if len(product_ids) != len(set(product_ids)):
                raise serializers.ValidationError(
                    {"items": "A product can appear only once per purchase order."}
                )

        if self.instance is not None and "items" in attrs:
            raise serializers.ValidationError(
                {"items": ("Updating purchase order items is not supported yet.")}
            )

        if self.instance is not None and "status" in attrs:
            if attrs["status"] != self.instance.status:
                raise serializers.ValidationError(
                    {
                        "status": (
                            "Status changes must use the dedicated workflow actions."
                        )
                    }
                )

        return attrs

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        purchase_order = PurchaseOrder.objects.create(**validated_data)

        PurchaseOrderItem.objects.bulk_create(
            [
                PurchaseOrderItem(
                    purchase_order=purchase_order,
                    **item_data,
                )
                for item_data in items_data
            ]
        )

        return purchase_order
