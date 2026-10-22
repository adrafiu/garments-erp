from django.utils import timezone
from rest_framework import serializers

from apps.products.models import Product
from apps.suppliers.models import Supplier

from .models import (
    GoodsReceipt,
    GoodsReceiptItem,
    PurchaseOrder,
    PurchaseOrderItem,
)


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


class GoodsReceiptItemSerializer(serializers.ModelSerializer):
    purchase_order_item_id = serializers.IntegerField(min_value=1)
    product_name = serializers.CharField(
        source="purchase_order_item.product.name",
        read_only=True,
    )

    class Meta:
        model = GoodsReceiptItem
        fields = [
            "id",
            "purchase_order_item_id",
            "product_name",
            "received_quantity",
        ]
        read_only_fields = ["id", "product_name"]

    def validate_received_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Received quantity must be greater than zero."
            )
        return value


class GoodsReceiptSerializer(serializers.ModelSerializer):
    items = GoodsReceiptItemSerializer(many=True)
    purchase_order_number = serializers.CharField(
        source="purchase_order.po_number",
        read_only=True,
    )

    class Meta:
        model = GoodsReceipt
        fields = [
            "id",
            "receipt_number",
            "purchase_order",
            "purchase_order_number",
            "received_date",
            "status",
            "notes",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "created_at",
            "updated_at",
        ]

    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError(
                "A goods receipt must contain at least one item."
            )

        item_ids = [item["purchase_order_item_id"] for item in items]

        if len(item_ids) != len(set(item_ids)):
            raise serializers.ValidationError(
                "A purchase order item can appear only once per receipt."
            )

        return items

    def validate(self, attrs):
        purchase_order = attrs["purchase_order"]

        allowed_statuses = {
            PurchaseOrder.Status.APPROVED,
            PurchaseOrder.Status.PARTIALLY_RECEIVED,
        }

        if purchase_order.status not in allowed_statuses:
            raise serializers.ValidationError(
                {
                    "purchase_order": (
                        "Goods can only be received for approved or "
                        "partially received purchase orders."
                    )
                }
            )

        return attrs

    def create(self, validated_data):
        from .services import create_goods_receipt

        items_data = validated_data.pop("items")
        purchase_order = validated_data.pop("purchase_order")

        service_items = [
            {
                "purchase_order_item_id": item["purchase_order_item_id"],
                "received_quantity": item["received_quantity"],
            }
            for item in items_data
        ]

        try:
            return create_goods_receipt(
                receipt_number=validated_data["receipt_number"],
                purchase_order_id=purchase_order.id,
                received_date=validated_data["received_date"],
                items=service_items,
                notes=validated_data.get("notes", ""),
            )
        except Exception as exc:
            from django.core.exceptions import ValidationError

            if isinstance(exc, ValidationError):
                raise serializers.ValidationError(exc.messages) from exc
            raise


"""
GoodsReceiptItemSerializer: কোন Purchase Order item কত quantity receive করা হচ্ছে, তা validate করবে।
GoodsReceiptSerializer: receipt-এর মূল তথ্য ও nested items validate করবে।
validate_items(): receipt-এ item খালি রাখা বা একই item দুবার পাঠানো আটকাবে।
validate(): শুধু approved অথবা partially_received Purchase Order গ্রহণ করবে।
create(): validated data-কে create_goods_receipt() service-এ পাঠাবে। Stock ও Purchase Order status update হবে service-এর মাধ্যমে।
"""
