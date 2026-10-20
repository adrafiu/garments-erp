from rest_framework import filters, viewsets
from django_filters.rest_framework import DjangoFilterBackend

from .models import Product
from .serializers import ProductSerializer


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filterset_fields = [
        "unit",
        "is_active",
    ]

    search_fields = [
        "sku",
        "name",
        "description",
    ]

    ordering_fields = [
        "sku",
        "name",
        "created_at",
        "updated_at",
    ]

    ordering = [
        "name",
        "id",
    ]
