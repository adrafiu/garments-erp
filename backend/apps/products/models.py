from django.db import models
from django.core.exceptions import ValidationError


class ProductCategory(models.Model):

    class CategoryType(models.TextChoices):
        RAW_MATERIAL = "raw_material", "Raw Material"
        ACCESSORY = "accessory", "Accessory"
        FINISHED_GOOD = "finished_good", "Finished Good"

    name = models.CharField(max_length=100, unique=True)
    category_type = models.CharField(
        max_length=30,
        choices=CategoryType.choices,
        unique=True,
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name", "id"]
        verbose_name_plural = "Product categories"

    def __str__(self):
        return self.name


class Product(models.Model):

    class Unit(models.TextChoices):
        PIECE = "piece", "Piece"
        SET = "set", "Set"
        DOZEN = "dozen", "Dozen"
        METER = "meter", "Meter"
        YARD = "yard", "Yard"
        KILOGRAM = "kg", "Kilogram"

    name = models.CharField(max_length=200)

    sku = models.CharField(
        max_length=50,
        unique=True,
    )

    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.PROTECT,
        related_name="products",
        null=True,
        blank=True,
    )

    description = models.TextField(blank=True)

    unit = models.CharField(
        max_length=20,
        choices=Unit.choices,
        default=Unit.PIECE,
    )

    current_stock = models.DecimalField(
        max_digits=14,
        decimal_places=3,
        default=0,
    )

    minimum_stock_level = models.DecimalField(
        max_digits=14,
        decimal_places=3,
        default=0,
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name", "id"]

    def __str__(self):
        return f"{self.sku} - {self.name}"


class StockMovement(models.Model):

    class MovementType(models.TextChoices):
        STOCK_IN = "stock_in", "Stock In"
        STOCK_OUT = "stock_out", "Stock Out"
        ADJUSTMENT = "adjustment", "Adjustment"

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="stock_movements",
    )

    movement_type = models.CharField(
        max_length=20,
        choices=MovementType.choices,
    )

    quantity = models.DecimalField(
        max_digits=14,
        decimal_places=3,
    )

    note = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        super().clean()

        if self.quantity is None:
            return

        if self.movement_type in (
            self.MovementType.STOCK_IN,
            self.MovementType.STOCK_OUT,
        ):
            if self.quantity <= 0:
                raise ValidationError(
                    {
                        "quantity": (
                            "Stock In and Stock Out quantity "
                            "must be greater than zero."
                        )
                    }
                )

        elif self.movement_type == self.MovementType.ADJUSTMENT:
            if self.quantity == 0:
                raise ValidationError(
                    {"quantity": ("Adjustment quantity cannot be zero.")}
                )

            if not self.note or not self.note.strip():
                raise ValidationError(
                    {"note": ("A reason is required for stock adjustment.")}
                )

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.product.sku} - {self.get_movement_type_display()}"

    """
        ProductCategory: category-এর জন্য আলাদা database table তৈরি করবে।
        category_type: তিনটি নির্ধারিত category type-এর মধ্যে একটি রাখবে।
        ForeignKey: প্রতিটি Product-কে একটি category-র সঙ্গে যুক্ত করবে।
        on_delete=models.PROTECT: কোনো category-তে Product থাকলে সেই category মুছে ফেলা আটকাবে।
        null=True, blank=True: পুরোনো Product-গুলোকে এখনই category দিতে হবে না। এতে বিদ্যমান data migration সহজ হবে।
        related_name="products": একটি category-র সব Product সহজে পাওয়া যাবে।
    """
