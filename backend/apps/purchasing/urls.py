from rest_framework.routers import DefaultRouter

from .views import PurchaseOrderItemViewSet, PurchaseOrderViewSet

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

urlpatterns = router.urls
