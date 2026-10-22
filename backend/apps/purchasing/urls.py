from rest_framework.routers import DefaultRouter

from .views import (
    GoodsReceiptViewSet,
    PurchaseOrderItemViewSet,
    PurchaseOrderViewSet,
)

router = DefaultRouter()

router.register(
    "purchase-orders",
    PurchaseOrderViewSet,
    basename="purchase-order",
)
router.register(
    "purchase-order-items",
    PurchaseOrderItemViewSet,
    basename="purchase-order-item",
)
router.register(
    "goods-receipts",
    GoodsReceiptViewSet,
    basename="goods-receipt",
)

urlpatterns = router.urls
