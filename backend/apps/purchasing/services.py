from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum

from apps.products.models import StockMovement
from apps.products.services import create_stock_movement

from .models import (
    GoodsReceipt,
    GoodsReceiptItem,
    PurchaseOrder,
    PurchaseOrderItem,
)


@transaction.atomic
def create_goods_receipt(
    *,
    receipt_number: str,
    purchase_order_id: int,
    received_date,
    items: list[dict],
    notes: str = "",
) -> GoodsReceipt:
    if not items:
        raise ValidationError("A goods receipt must contain at least one item.")

    purchase_order = PurchaseOrder.objects.select_for_update().get(pk=purchase_order_id)

    allowed_statuses = {
        PurchaseOrder.Status.APPROVED,
        PurchaseOrder.Status.PARTIALLY_RECEIVED,
    }

    if purchase_order.status not in allowed_statuses:
        raise ValidationError(
            "Goods can only be received for approved or partially "
            "received purchase orders."
        )

    # Validate every item before changing stock.
    validated_items = []
    seen_item_ids = set()

    for item in items:
        purchase_order_item_id = item["purchase_order_item_id"]
        quantity = Decimal(str(item["received_quantity"]))

        if purchase_order_item_id in seen_item_ids:
            raise ValidationError(
                "A purchase order item can appear only once per receipt."
            )

        seen_item_ids.add(purchase_order_item_id)

        if quantity <= 0:
            raise ValidationError("Received quantity must be greater than zero.")

        try:
            po_item = PurchaseOrderItem.objects.select_related("product").get(
                pk=purchase_order_item_id,
                purchase_order=purchase_order,
            )
        except PurchaseOrderItem.DoesNotExist as exc:
            raise ValidationError(
                "Each received item must belong to the selected " "purchase order."
            ) from exc

        previous_received = GoodsReceiptItem.objects.filter(
            purchase_order_item=po_item,
            goods_receipt__status=GoodsReceipt.Status.RECEIVED,
        ).aggregate(total=Sum("received_quantity"))["total"] or Decimal("0")

        if previous_received + quantity > po_item.quantity:
            remaining = po_item.quantity - previous_received

            raise ValidationError(
                "Received quantity exceeds the remaining quantity "
                f"for product {po_item.product.name}. "
                f"Remaining: {remaining}."
            )

        validated_items.append((po_item, quantity))

    receipt = GoodsReceipt.objects.create(
        receipt_number=receipt_number,
        purchase_order=purchase_order,
        received_date=received_date,
        notes=notes,
    )

    for po_item, quantity in validated_items:
        movement = create_stock_movement(
            product_id=po_item.product_id,
            movement_type=StockMovement.MovementType.STOCK_IN,
            quantity=quantity,
            note=(
                f"Goods receipt {receipt.receipt_number} "
                f"for purchase order {purchase_order.po_number}"
            ),
        )

        GoodsReceiptItem.objects.create(
            goods_receipt=receipt,
            purchase_order_item=po_item,
            received_quantity=quantity,
            stock_movement=movement,
        )

    received_item_ids = purchase_order.items.values_list(
        "id",
        flat=True,
    )

    totals = (
        GoodsReceiptItem.objects.filter(
            purchase_order_item_id__in=received_item_ids,
            goods_receipt__status=GoodsReceipt.Status.RECEIVED,
        )
        .values("purchase_order_item_id")
        .annotate(total=Sum("received_quantity"))
    )

    received_by_item = {row["purchase_order_item_id"]: row["total"] for row in totals}

    all_items_fully_received = all(
        received_by_item.get(item.id, Decimal("0")) >= item.quantity
        for item in purchase_order.items.all()
    )

    purchase_order.status = (
        PurchaseOrder.Status.RECEIVED
        if all_items_fully_received
        else PurchaseOrder.Status.PARTIALLY_RECEIVED
    )

    purchase_order.save(update_fields=["status", "updated_at"])

    return receipt


"""
transaction.atomic() নিশ্চিত করে যে receipt, item, stock movement এবং stock update একসঙ্গে সফল হবে অথবা rollback হবে।
select_for_update() একই Purchase Order-এ concurrent receiving সমন্বয় করতে সাহায্য করে—যদিও SQLite-এ row-level locking সমর্থন সীমিত।
একই PO item এক receipt-এ দুইবার দেওয়া যাবে না।
আগের receipt-সহ মোট received quantity ordered quantity অতিক্রম করতে পারবে না।
Stock পরিবর্তনের জন্য বিদ্যমান create_stock_movement() service ব্যবহার করা হয়েছে।
"""
