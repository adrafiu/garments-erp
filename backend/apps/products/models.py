from django.db import models


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

    description = models.TextField(blank=True)

    unit = models.CharField(
        max_length=20,
        choices=Unit.choices,
        default=Unit.PIECE,
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name", "id"]

    def __str__(self):
        return f"{self.sku} - {self.name}"
