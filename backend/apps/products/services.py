from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Product, StockMovement


@transaction.atomic
def create_stock_movement(
    *,
    product_id: int,
    movement_type: str,
    quantity: Decimal,
    note: str = "",
) -> StockMovement:
    product = Product.objects.select_for_update().get(pk=product_id)

    movement = StockMovement(
        product=product,
        movement_type=movement_type,
        quantity=quantity,
        note=note,
    )

    movement.full_clean()

    if movement_type == StockMovement.MovementType.STOCK_IN:
        product.current_stock += quantity

    elif movement_type == StockMovement.MovementType.STOCK_OUT:
        if product.current_stock < quantity:
            raise ValidationError("Insufficient stock for this operation.")

        product.current_stock -= quantity

    elif movement_type == StockMovement.MovementType.ADJUSTMENT:
        product.current_stock += quantity

    else:
        raise ValidationError("Invalid stock movement type.")

    if product.current_stock < 0:
        raise ValidationError("Stock cannot be negative.")

    product.save(update_fields=["current_stock", "updated_at"])

    movement.save()

    return movement


"""
select_for_update() transaction চলাকালে সমর্থিত database-এ একই Product-এর stock update সমন্বয় করতে সাহায্য করে।
full_clean() movement-এর validation চালায়।
Stock In হলে stock বাড়ে।
Stock Out হলে পর্যাপ্ত stock আছে কি না পরীক্ষা করে, তারপর কমায়।
Adjustment-এর ধনাত্মক quantity stock বাড়ায়; ঋণাত্মক quantity stock কমায়।
কোনো validation বা database error হলে transaction.atomic-এর কারণে transaction rollback হবে।
"""
