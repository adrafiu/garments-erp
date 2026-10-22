from django.contrib import admin

from .models import Supplier


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "contact_person",
        "email",
        "phone",
        "country",
        "is_active",
        "created_at",
    )

    search_fields = (
        "name",
        "contact_person",
        "email",
        "phone",
    )

    list_filter = (
        "is_active",
        "country",
    )

    ordering = ("name",)
