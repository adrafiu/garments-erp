from django.contrib import admin

from .models import Buyer


@admin.register(Buyer)
class BuyerAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "contact_person",
        "email",
        "country",
        "is_active",
        "created_at",
    )

    search_fields = ("name", "contact_person", "email", "country")

    list_filter = ("is_active", "country")

    ordering = ("name",)
