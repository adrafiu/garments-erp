from rest_framework import serializers

from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    sku = serializers.CharField(
        max_length=50,
        trim_whitespace=True,
    )

    name = serializers.CharField(
        max_length=200,
        trim_whitespace=True,
    )

    def validate_sku(self, value):
        value = value.strip()

        existing_products = Product.objects.filter(sku__iexact=value)

        if self.instance:
            existing_products = existing_products.exclude(pk=self.instance.pk)

        if existing_products.exists():
            raise serializers.ValidationError("A product with this SKU already exists.")

        return value

    class Meta:
        model = Product
        fields = "__all__"
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
        )

        """
            ModelSerializer — Product model থেকে serializer তৈরি করে।
            trim_whitespace=True — SKU ও নামের শুরু-শেষের অতিরিক্ত whitespace বাদ দেয়।
            sku__iexact — FAB-001 ও fab-001-এর মতো SKU-কে একই হিসেবে ধরে duplicate validation করে।
            self.instance — বিদ্যমান Product update করার সময় সেটিকেই duplicate হিসেবে গণনা করা থেকে বাদ দেয়।
            read_only_fields — ID ও timestamps API request দিয়ে পরিবর্তন করা যাবে না।
        """
