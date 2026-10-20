from rest_framework.routers import DefaultRouter

from .views import BuyerViewSet

router = DefaultRouter()
router.register("buyers", BuyerViewSet, basename="buyer")

urlpatterns = router.urls
