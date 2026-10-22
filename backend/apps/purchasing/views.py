from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from .models import PurchaseOrder, PurchaseOrderItem
from .serializers import (
    PurchaseOrderItemSerializer,
    PurchaseOrderSerializer,
)


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrder.objects.select_related("supplier").prefetch_related(
        "items__product"
    )
    serializer_class = PurchaseOrderSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class PurchaseOrderItemViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PurchaseOrderItem.objects.select_related(
        "purchase_order",
        "product",
    )
    serializer_class = PurchaseOrderItemSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


"""
PurchaseOrderViewSet: Purchase Order-এর CRUD API পরিচালনা করবে।
PurchaseOrderItemViewSet: Purchase Order-এর item-গুলো শুধু দেখা যাবে; আলাদাভাবে create, update বা delete করা যাবে না।
select_related() এবং prefetch_related() সংশ্লিষ্ট supplier ও product-এর data আনতে অপ্রয়োজনীয় database query কমাতে সাহায্য করবে।
IsAuthenticatedOrReadOnly: anonymous user-রা GET request করতে পারবে, কিন্তু পরিবর্তন করতে হলে authentication প্রয়োজন হবে।
"""
