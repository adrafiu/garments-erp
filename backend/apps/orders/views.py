from rest_framework import filters, viewsets
from django_filters.rest_framework import DjangoFilterBackend

from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderItemSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.select_related("buyer").all()

    serializer_class = OrderSerializer

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filterset_fields = [
        "buyer",
        "status",
        "order_date",
        "delivery_date",
    ]

    search_fields = [
        "order_number",
        "buyer__name",
    ]

    ordering_fields = [
        "order_number",
        "order_date",
        "delivery_date",
        "quantity",
        "created_at",
        "updated_at",
    ]

    ordering = [
        "-order_date",
        "-id",
    ]


class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.select_related(
        "order",
        "product",
    ).all()

    serializer_class = OrderItemSerializer

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filterset_fields = [
        "order",
        "product",
    ]

    search_fields = [
        "order__order_number",
        "product__name",
    ]

    ordering_fields = [
        "quantity",
        "unit_price",
        "id",
    ]

    ordering = [
        "id",
    ]

    """
        ModelViewSet — list, create, retrieve, update, partial update ও delete-এর ব্যবস্থা দেয়।
        select_related("buyer") — Order-এর সঙ্গে Buyer-এর তথ্য আনতে database query কমাতে সাহায্য করে।
        DjangoFilterBackend — নির্দিষ্ট field দিয়ে filter করে।
        SearchFilter — order number বা Buyer-এর নাম দিয়ে search করে।
        OrderingFilter — তারিখ, quantity বা order number অনুযায়ী sort করে।
    """
    
    """
        select_related("order", "product") ব্যবহার করে সংশ্লিষ্ট Order ও Product-এর তথ্য দক্ষভাবে আনবে।
        filterset_fields দিয়ে নির্দিষ্ট Order বা Product-এর আইটেম খুঁজতে পারবে।
        search_fields দিয়ে Order Number বা Product Name দিয়ে সার্চ করতে পারবে।
        ModelViewSet দিয়ে Order Item-এর CRUD অপারেশন—Create, Read, Update, Delete—সমর্থন করবে।
    """