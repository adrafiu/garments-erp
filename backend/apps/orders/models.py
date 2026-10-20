from django.db import models
from django.core.validators import MinValueValidator

from apps.buyers.models import Buyer


class Order(models.Model):

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        CONFIRMED = "confirmed", "Confirmed"
        IN_PRODUCTION = "in_production", "In Production"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    order_number = models.CharField(
        max_length=30,
        unique=True,
    )

    buyer = models.ForeignKey(
        Buyer,
        on_delete=models.PROTECT,
        related_name="orders",
    )

    order_date = models.DateField()

    delivery_date = models.DateField()

    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-order_date", "-id"]

    def __str__(self):
        return self.order_number

    """
    - order_number — প্রতিটি order-এর আলাদা পরিচিতি, যেমন ORD-2026-001। unique=True একই নম্বর দ্বিতীয়বার সংরক্ষণ করতে বাধা দেয়।
    - ForeignKey — একটি order-কে একজন Buyer-এর সঙ্গে যুক্ত করে। একই Buyer-এর একাধিক order থাকতে পারে।
    - on_delete=models.PROTECT — কোনো Buyer-এর সঙ্গে order যুক্ত থাকলে সেই Buyer-কে সরাসরি delete করতে বাধা দেয়। এতে order history সুরক্ষিত থাকে।
    - Status — order-এর বর্তমান অবস্থা নির্ধারণ করে।
    - quantity — অন্তত ১ হতে হবে। তবে MinValueValidator-এর validation শুধু model field-এ ঘোষণা করলেই সব ধরনের সরাসরি database write আটকায় না; API serializer-এও validation থাকবে।
    - related_name="orders" — কোনো Buyer-এর order পেতে buyer.orders.all() ব্যবহার করা যাবে।
    """
