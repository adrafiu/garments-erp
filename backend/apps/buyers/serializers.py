from rest_framework import serializers

from .models import Buyer


class BuyerSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        max_length=200,
        trim_whitespace=True,
    )

    def validate_name(self, value):
        normalized_name = value.strip().casefold()

        existing_buyers = Buyer.objects.filter(name__iexact=normalized_name)

        if self.instance:
            existing_buyers = existing_buyers.exclude(pk=self.instance.pk)

        if existing_buyers.exists():
            raise serializers.ValidationError(
                "A buyer with this company name already exists."
            )

        return value.strip()

    """
    validate_name() — name field-এর custom validation চালায়।
    casefold() — নামের uppercase/lowercase পার্থক্য উপেক্ষা করতে সাহায্য করে।
    name__iexact — database-এ case-insensitive নাম খোঁজে।
    exclude(pk=self.instance.pk) — বিদ্যমান Buyer নিজেকে update করার সময় নিজেকেই duplicate হিসেবে ধরে না।
    ValidationError — duplicate নাম পেলে API-তে error ফেরত দেয়।
    """

    class Meta:
        model = Buyer
        fields = "__all__"
