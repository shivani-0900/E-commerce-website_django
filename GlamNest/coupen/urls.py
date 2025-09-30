from coupen import views
from django.urls import path

urlpatterns = [
    
 path('cart/apply-coupon/', views.apply_coupon, name='apply_coupon'),
path('cart/remove-coupon/', views.remove_coupon, name='remove_coupon'),
path('manage_coupons/', views.manage_coupons, name='manage_coupons'),  # ✅ matches /manage_coupons
path('delete_coupon/<int:coupon_id>/', views.delete_coupon, name='delete_coupon'),

 path('subscribe/', views.subscribe_newsletter, name='subscribe_newsletter'),
 path('offers', views.available_offers, name='available_offers'),

  
]
