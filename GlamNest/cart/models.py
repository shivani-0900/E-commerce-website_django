from django.db import models
from User.models import User_Table,ProductApproval


# Create your models here.
class cart(models.Model):
    user = models.ForeignKey(User_Table, on_delete=models.CASCADE)
    product = models.ForeignKey(ProductApproval, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    
class ProductRating(models.Model):
    product = models.ForeignKey(ProductApproval, on_delete=models.CASCADE)
    user = models.ForeignKey(User_Table, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(choices=[(i, f'{i} ★') for i in range(1, 6)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['product', 'user']

class ProductReview(models.Model):
    rating = models.OneToOneField(ProductRating, on_delete=models.CASCADE, related_name='review')
    review_text = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to='product_reviews/', null=True, blank=True)  # NEW
    helpful_votes = models.PositiveIntegerField(default=0)
    is_flagged = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

# Wishlist model
class Wishlist(models.Model):  # ✅ Renamed from Whish_list to Wishlist
    user = models.ForeignKey(User_Table, on_delete=models.CASCADE)
    product = models.ForeignKey(ProductApproval, on_delete=models.CASCADE)
    added_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'product']
