# signals.py

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Avg
from .models import ProductRating, ProductApproval

def update_product_rating(product):
    ratings = ProductRating.objects.filter(product=product)
    total = ratings.count()
    average = ratings.aggregate(Avg('rating'))['rating__avg'] or 0

    product.total_ratings = total
    product.average_rating = round(average, 2)
    product.save()

@receiver(post_save, sender=ProductRating)
def on_rating_save(sender, instance, **kwargs):
    update_product_rating(instance.product)

@receiver(post_delete, sender=ProductRating)
def on_rating_delete(sender, instance, **kwargs):
    update_product_rating(instance.product)
