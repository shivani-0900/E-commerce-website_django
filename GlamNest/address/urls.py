from django.urls import path
from . import views

urlpatterns = [
    path('addresses/', views.manage_addresses, name='manage_addresses'),
    path('address/choose-shipping-address/', views.choose_shipping_address, name='choose_shipping_address'),
        path('delete_address/<int:address_id>/', views.delete_address, name='delete_address'),
        path('order/track/<int:order_id>/', views.track_order, name='track_order'),


]
