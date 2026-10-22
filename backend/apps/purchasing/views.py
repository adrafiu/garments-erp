from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from .models import (
    GoodsReceipt,
    PurchaseOrder,
    PurchaseOrderItem,
)
from .serializers import (
    GoodsReceiptSerializer,
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


class GoodsReceiptViewSet(viewsets.ModelViewSet):
    queryset = GoodsReceipt.objects.select_related(
        "purchase_order", "purchase_order__supplier"
    ).prefetch_related(
        "items__purchase_order_item__product",
        "items__stock_movement",
    )
    serializer_class = GoodsReceiptSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    http_method_names = ["get", "post", "head", "options"]


"""
GET — Goods Receipt-এর তালিকা ও বিস্তারিত দেখা।
POST — নতুন Goods Receipt তৈরি করা।
PUT, PATCH, DELETE — আপাতত বন্ধ থাকবে, যাতে তৈরি হওয়া receipt পরিবর্তন বা মুছে stock history অসামঞ্জস্যপূর্ণ না হয়।
select_related() ও prefetch_related() — সম্পর্কিত data আনতে অপ্রয়োজনীয় database query কমাতে সাহায্য করবে।
"""
