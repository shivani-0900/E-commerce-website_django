from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

# User model
class User_Table(AbstractUser):
    USER_TYPES = [('Buyer', 'Buyer'), ('Seller', 'Seller')]
    
    usertype = models.CharField(max_length=10, choices=USER_TYPES)
    phone = models.BigIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=20)
    brand = models.CharField(max_length=40, null=True, blank=True)  # for sellers
    productype = models.CharField(max_length=100, null=True, blank=True)
    is_approved = models.BooleanField(default=False)
    new_order_alert = models.BooleanField(default=False)
    profile_image = models.ImageField(upload_to='profile_images/', default='profile_images/profile_icon.jpg')



class ProductApproval(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    PRODUCT_TYPE_CHOICES = [
        ('Skincare', 'Skincare'),
        ('Makeup', 'Makeup'),
        ('Haircare', 'Haircare'),
    ]

    CATEGORY_CHOICES = [
        # Skincare
        ('Cleanser', 'Cleanser'),
        ('Moisturizer', 'Moisturizer'),
        ('Serum', 'Serum'),
        ('Sunscreen', 'Sunscreen'),
        # Makeup
        ('Foundation', 'Foundation'),
        ('Lipstick', 'Lipstick'),
        ('Mascara', 'Mascara'),
        ('Eyeshadow', 'Eyeshadow'),
        # Haircare
        ('Shampoo', 'Shampoo'),
        ('Conditioner', 'Conditioner'),
        ('Hair Oil', 'Hair Oil'),
        ('Hair Serum', 'Hair Serum'),
    ]

    SKIN_TYPE_CHOICES = [
        ('Oily', 'Oily'),
        ('Dry', 'Dry'),
        ('Combination', 'Combination'),
        ('Sensitive', 'Sensitive'),
        ('None', 'None'),  # For non-skincare
    ]

    SKIN_TONE_CHOICES = [
        ('Fair', 'Fair'),
        ('Light', 'Light'),
        ('Medium', 'Medium'),
        ('Tan', 'Tan'),
        ('Deep', 'Deep'),
        ('None', 'None'),  # For non-makeup
    ]

    HAIR_TEXTURE_CHOICES = [
        ('Straight', 'Straight'),
        ('Wavy', 'Wavy'),
        ('Curly', 'Curly'),
        ('Coily', 'Coily'),
        ('None', 'None'),  # For non-haircare
    ]
    QUANTITY_CHOICES = [
    (15, '15 ml'),
    (30, '30 ml'),
    (50, '50 ml'),
    (75, '75 ml'),
    (100, '100 ml'),


    ]

    # --- Core Product Info ---
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='product_approvals'
    )
    product_name = models.CharField(max_length=100)
    brand_name = models.CharField(max_length=100)
    
    description = models.TextField()
    ingredients = models.TextField(null=True, blank=True)
    how_to_use = models.TextField(null=True, blank=True)
    quantity = models.PositiveSmallIntegerField(choices=QUANTITY_CHOICES, default=100,null=True, blank=True)

    price = models.DecimalField(max_digits=10, decimal_places=2)
    expiry_date = models.DateField(null=True, blank=True)
    country_of_origin = models.CharField(max_length=100, null=True, blank=True)
    brand_address = models.TextField(null=True, blank=True)
    manufacturer = models.CharField(max_length=255, null=True, blank=True)
    image = models.ImageField(upload_to='product_images/', null=True, blank=True)

    # --- Classification ---
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPE_CHOICES)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    skin_type = models.CharField(max_length=20, choices=SKIN_TYPE_CHOICES, default='None')
    skin_tone = models.CharField(max_length=20, choices=SKIN_TONE_CHOICES, default='None', blank=True)
    hair_texture = models.CharField(max_length=20, choices=HAIR_TEXTURE_CHOICES, default='None', blank=True)

    # --- Status & Meta ---
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sold_quantity = models.PositiveIntegerField(default=0)
    average_rating = models.FloatField(default=0)
    total_ratings = models.PositiveIntegerField(default=0)

    
    
class ProductImage(models.Model):
    product = models.ForeignKey(ProductApproval, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='product_images/')
    alt_text = models.CharField(max_length=255, blank=True, null=True)  # Optional description for image accessibility
    
    
    

class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.name} ({self.email})"