from django.db import models
from django.db.models.functions import Lower
from django_countries.fields import CountryField


class Buyer(models.Model):
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=150, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    country = CountryField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower("name"),
                name="unique_buyer_name_case_insensitive",
            ),
        ]

    def save(self, *args, **kwargs):
        self.name = self.name.strip()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    """
    Lower("name") — database-এ নামের lowercase expression ব্যবহার করে uniqueness পরীক্ষা করবে।
    UniqueConstraint(...) — একই নাম uppercase/lowercase বদলে পুনরায় insert করা আটকাবে।
    save() — স্বাভাবিক model save-এর আগে নামের শুরু ও শেষের whitespace সরাবে।
    super().save(...) — Django-র মূল save process চালাবে।
    """