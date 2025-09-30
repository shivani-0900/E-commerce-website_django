from django.urls import path
from order import views

app_name='order'

urlpatterns = [
  



path('create_payment_order/<int:order_id>/', views.create_payment_order, name='create_payment_order'),
    path('verify_payment/', views.verify_payment, name='verify_payment'),
    path('proceed/<int:order_id>/', views.proceed_with_order, name='proceed_with_order'),

  # All Orders for the Seller
path('seller/orders/', views.seller_orders_view, name='seller_orders_view'),

# Mark a Specific OrderItem as Shipped
path('seller/item/<int:item_id>/ship/', views.mark_orderitem_shipped, name='mark_orderitem_shipped'),
path('seller/orders/pending/', views.seller_pending_orders_view, name='seller_pending_orders'),
path('seller/orders/completed/', views.seller_completed_orders_view, name='seller_completed_orders'),
path('seller/orders/cancelled/', views.seller_cancelled_orders_view, name='seller_cancelled_orders'),
path('update-status/<int:item_id>/', views.update_orderitem_status, name='update_orderitem_status'),
path('seller/returned-orders/', views.seller_returned_orders_view, name='seller_returned_orders'),




]
