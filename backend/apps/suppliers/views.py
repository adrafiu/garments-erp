from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets

from .models import Supplier
from .serializers import SupplierSerializer


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all().order_by("name", "pk")
    serializer_class = SupplierSerializer

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filterset_fields = ["is_active", "country"]

    search_fields = ["name", "contact_person", "email", "phone"]

    ordering_fields = ["name", "created_at", "updated_at"]

    ordering = ["name", "pk"]
