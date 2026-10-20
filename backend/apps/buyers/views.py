from rest_framework import filters, viewsets
from django_filters.rest_framework import DjangoFilterBackend

from .models import Buyer
from .serializers import BuyerSerializer


class BuyerViewSet(viewsets.ModelViewSet):
    queryset = Buyer.objects.all().order_by("name", "pk")
    serializer_class = BuyerSerializer

    # Search by company name, contact person, and email.
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    # Exact-match filters.
    filterset_fields = ["is_active", "country"]

    # Partial text search.
    search_fields = ["name", "contact_person", "email"]

    # Fields allowed for sorting.
    ordering_fields = ["name", "created_at", "updated_at"]

    # Default sorting order.
    ordering = ["name", "pk"]
