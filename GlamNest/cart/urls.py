from cart import views
from django.urls import path
from .views import update_cart_quantity


urlpatterns = [
     #Add to cart
    path('cart/add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),

    path('cart/get-cart-count/', views.get_cart_count, name='get_cart_count'),
path('get-wishlist-count/', views.get_wishlist_count, name='get_wishlist_count'),
path('cart-count/', views.cart_count, name='cart_count'),
path('wishlist-count/', views.wishlist_count, name='wishlist_count'),

    path('view_cart/', views.view_cart, name='view_cart'),
    path('update-quantity/', views.update_cart_quantity, name='update_cart_quantity'),    #payment
    # path('checkout/', views.checkout, name='checkout'),  # Placeholder
    # path('shop/', views.shop, name='shop'),  
    path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('proceed',views.proceed_to_checkout,name="proceed_to_checkout"),
]
