from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    fields = (
        "product",
        "quantity",
        "unit_price",
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number",
        "buyer",
        "order_date",
        "delivery_date",
        "quantity",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "order_date",
        "delivery_date",
    )

    search_fields = (
        "order_number",
        "buyer__name",
    )

    ordering = (
        "-order_date",
        "-id",
    )

    list_select_related = ("buyer",)

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    date_hierarchy = "order_date"

    inlines = [OrderItemInline]

    """
        list_display — Order list-এ গুরুত্বপূর্ণ তথ্য দেখাবে।
        list_filter — Status ও date অনুযায়ী filter করতে দেবে।
        search_fields — Order number ও Buyer company name দিয়ে search করতে দেবে।
        list_select_related — Buyer-এর তথ্য দেখানোর সময় অপ্রয়োজনীয় database query কমাতে সাহায্য করবে।
        readonly_fields — created_at ও updated_at Admin form-এ edit করা যাবে না।
    """

    """
        OrderItem ইমপোর্ট করা হয়েছে।
        OrderItemInline একটি Order-এর ভেতরে একাধিক পণ্যের তথ্য যোগ করার ব্যবস্থা করবে।
        extra = 1 একটি খালি Product row দেখাবে।
        inlines = [OrderItemInline] Order-এর Admin পেজে এই সুবিধাটি চালু করবে।
    """
