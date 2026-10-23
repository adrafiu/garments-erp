from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Count, F, Q
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response

from .models import Product, ProductCategory, StockMovement
from .serializers import (
    ProductCategorySerializer,
    ProductSerializer,
    StockMovementSerializer,
)
from .services import create_stock_movement


class ProductCategoryViewSet(viewsets.ModelViewSet):
    queryset = ProductCategory.objects.all()
    serializer_class = ProductCategorySerializer

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filterset_fields = [
        "category_type",
        "is_active",
    ]

    search_fields = [
        "name",
        "description",
    ]

    ordering_fields = [
        "name",
        "category_type",
        "created_at",
        "updated_at",
    ]

    ordering = [
        "name",
        "id",
    ]


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filterset_fields = [
        "category",
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

    ordering = [
        "name",
        "id",
    ]

    @action(detail=False, methods=["get"], url_path="inventory-summary")
    def inventory_summary(self, request):
        active_products = Product.objects.filter(is_active=True)

        summary = active_products.aggregate(
            total_active_products=Count("id"),
            total_low_stock_products=Count(
                "id",
                filter=Q(current_stock__lte=F("minimum_stock_level")),
            ),
            total_out_of_stock_products=Count(
                "id",
                filter=Q(current_stock__lte=0),
            ),
        )

        categories = (
            ProductCategory.objects.filter(is_active=True)
            .annotate(
                product_count=Count(
                    "products",
                    filter=Q(products__is_active=True),
                )
            )
            .values("id", "name", "category_type", "product_count")
        )

        return Response({
            **summary,
            "categories": list(categories),
        })

    @action(detail=False, methods=["get"], url_path="low-stock")
    def low_stock(self, request):
        queryset = self.filter_queryset(self.get_queryset()).filter(
            current_stock__lte=F("minimum_stock_level"),
            is_active=True,
        )

        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


"""
@action(...) — নতুন /api/products/low-stock/ endpoint তৈরি করবে।
current_stock__lte=F("minimum_stock_level") — বর্তমান stock minimum stock-এর সমান বা কম কি না যাচাই করবে।
is_active=True — শুধু সক্রিয় পণ্য দেখাবে।
self.filter_queryset(...) — বিদ্যমান search, filter ও ordering-এর সুবিধা বজায় রাখবে।
paginate_queryset(...) — বিদ্যমান pagination ব্যবহার করবে।
"""


class StockMovementViewSet(viewsets.ModelViewSet):
    queryset = StockMovement.objects.select_related("product").all()
    serializer_class = StockMovementSerializer

    # Stock history cannot be edited or deleted directly.
    http_method_names = [
        "get",
        "post",
        "head",
        "options",
    ]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filterset_fields = [
        "product",
        "movement_type",
    ]

    search_fields = [
        "product__sku",
        "product__name",
        "note",
    ]

    ordering_fields = [
        "created_at",
        "quantity",
    ]

    ordering = [
        "-created_at",
        "-id",
    ]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            movement = create_stock_movement(
                product_id=serializer.validated_data["product"].pk,
                movement_type=serializer.validated_data["movement_type"],
                quantity=serializer.validated_data["quantity"],
                note=serializer.validated_data.get("note", ""),
            )
        except DjangoValidationError as exc:
            detail = exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            raise DRFValidationError(detail) from exc

        output_serializer = self.get_serializer(movement)

        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED,
        )
