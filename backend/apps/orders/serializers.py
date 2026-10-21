from rest_framework import serializers

from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(
        source="product.name",
        read_only=True,
    )

    subtotal = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = OrderItem
        fields = (
            "id",
            "order",
            "product",
            "product_name",
            "quantity",
            "unit_price",
            "subtotal",
        )
        read_only_fields = ("id", "subtotal")


class OrderSerializer(serializers.ModelSerializer):
    total_items = serializers.SerializerMethodField()
    total_amount = serializers.SerializerMethodField()

    def get_total_items(self, obj):
        return obj.items.count()

    def get_total_amount(self, obj):
        total = sum(
            (item.subtotal for item in obj.items.all()),
            start=0,
        )
        return total

    items = OrderItemSerializer(
        many=True,
        read_only=True,
    )

    buyer_name = serializers.CharField(
        source="buyer.name",
        read_only=True,
    )

    order_number = serializers.CharField(
        max_length=30,
        trim_whitespace=True,
    )

    def validate_order_number(self, value):
        value = value.strip()

        existing_orders = Order.objects.filter(order_number__iexact=value)

        if self.instance:
            existing_orders = existing_orders.exclude(pk=self.instance.pk)

        if existing_orders.exists():
            raise serializers.ValidationError(
                "An order with this order number already exists."
            )

        return value

    def validate(self, attrs):
        order_date = attrs.get(
            "order_date",
            getattr(self.instance, "order_date", None),
        )

        delivery_date = attrs.get(
            "delivery_date",
            getattr(self.instance, "delivery_date", None),
        )

        if order_date and delivery_date and delivery_date < order_date:
            raise serializers.ValidationError(
                {"delivery_date": ("Delivery date cannot be earlier than order date.")}
            )

        return attrs

    def validate_buyer(self, buyer):
        if not buyer.is_active:
            raise serializers.ValidationError(
                "Orders cannot be assigned to an inactive buyer."
            )

        return buyer

    class Meta:
        model = Order
        fields = "__all__"
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
            "total_items",
            "total_amount",
        )

    """
        buyer_name — API response-এ Buyer-এর নাম দেখাবে; এটি database-এ আলাদা করে সংরক্ষিত হবে না।
        validate_order_number() — একই order number-এর uppercase/lowercase পরিবর্তন করে duplicate তৈরি হতে দেবে না।
        validate() — delivery date যেন order date-এর আগের না হয়, সেটি পরীক্ষা করবে।
        validate_buyer() — inactive Buyer-এর জন্য নতুন Order তৈরি করতে বাধা দেবে।
        read_only_fields — ID ও timestamp client থেকে পরিবর্তন করা যাবে না।
    """
