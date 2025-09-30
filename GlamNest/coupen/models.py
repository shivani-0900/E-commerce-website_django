from django.db import models
from django.utils import timezone
from datetime import datetime

class Coupon(models.Model):
    code = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=100)
    description = models.TextField()
    discount_amount = models.DecimalField(max_digits=6, decimal_places=2)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    min_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    first_time_only = models.BooleanField(default=False)
    applicable_brand = models.CharField(max_length=50, blank=True, null=True)
    active = models.BooleanField(default=True)

    def is_valid(self, user, cart_total, user_cart_items):
        now = timezone.now()

        if not self.active or now < self.valid_from or now > self.valid_to:
            return False

        if self.first_time_only and user.order_set.exists():
            return False

        if cart_total < self.min_order_value:
            return False

        if self.applicable_brand:
            if not any(
                hasattr(item, "product") and 
                item.product and 
                getattr(item.product, "brand_name", None) == self.applicable_brand
                for item in user_cart_items
        ):
                return False

        return True
    
# models.py
class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email

