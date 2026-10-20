from rest_framework import filters, viewsets
from django_filters.rest_framework import DjangoFilterBackend

from .models import Order
from .serializers import OrderSerializer


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

    """
        ModelViewSet — list, create, retrieve, update, partial update ও delete-এর ব্যবস্থা দেয়।
        select_related("buyer") — Order-এর সঙ্গে Buyer-এর তথ্য আনতে database query কমাতে সাহায্য করে।
        DjangoFilterBackend — নির্দিষ্ট field দিয়ে filter করে।
        SearchFilter — order number বা Buyer-এর নাম দিয়ে search করে।
        OrderingFilter — তারিখ, quantity বা order number অনুযায়ী sort করে।
    """
