from django_countries.serializer_fields import CountryField
from rest_framework import serializers

from .models import Supplier


class SupplierSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        max_length=200,
        trim_whitespace=True,
    )

    country = CountryField(
        required=False,
        allow_blank=True,
    )

    def validate_name(self, value):
        normalized_name = value.strip().casefold()

        existing_suppliers = Supplier.objects.filter(
            name__iexact=normalized_name
        )

        if self.instance:
            existing_suppliers = existing_suppliers.exclude(
                pk=self.instance.pk
            )

        if existing_suppliers.exists():
            raise serializers.ValidationError(
                "A supplier with this company name already exists."
            )

        return value.strip()

    class Meta:
        model = Supplier
        fields = "__all__"
