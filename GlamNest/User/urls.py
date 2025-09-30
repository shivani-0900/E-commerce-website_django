from django.urls import path
from User import views
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy


app_name="User"
urlpatterns = [
    path('',views.user_home,name="user_home"),
    path('uselogin',views.user_login,name="user_login"),
    path('userreg',views.user_register,name="user_register"),
    path('sellerreg',views.seller_register,name="seller_register"),
    path('contact/submit/', views.contact_submit, name='contact_submit'),
    path('view_order/<int:order_id>', views.view_order, name='view_order'),
        path('request-return/<int:item_id>/', views.request_return, name='request_return'),
    path('cancel-order/<int:item_id>/', views.cancel_order_item, name='cancel_order_item'),

    path('send-order-email/<int:order_id>/', views.send_order_summary_email, name='send_order_summary_email'),
    path('send-order-sms/<int:order_id>/', views.send_order_summary_sms, name='send_order_summary_sms'),
    

    
    #admin
    path('admin_home/',views.admin_home,name="admin_home"),
    path('unapproved',views.unapproved_sellers,name="unapproved_sellers"),
    path('approve_seller/<int:id>',views.approve_sellers,name="approve_sellers"),
    path('reject_seller/<int:id>',views.reject_seller,name="reject_seller"),
    path('view_seller',views.view_seller,name="view_seller"),
    path('view_buyer',views.view_buyer,name="view_buyer"),
    path('search/', views.search_results, name='search_results'),
    path('api/suggestions/', views.product_suggestions, name='product_suggestions'),
    
    path('help', views.help, name='help'),
    path('help_home', views.help_home, name='help_home'),
    
    
    
    #seller home
        path('reviews/', views.seller_reviews, name='seller_reviews'),

    path('seller_home',views.seller_home,name="seller_home"),
    path('add_product',views.add_product_seller,name="add_product_seller"),
    path('unapprove_products',views.unapproved_products,name="unapproved_products"),
    path('seller_product_list',views.seller_product_list,name="seller_product_list"),
    path('approve_product/<int:id>/', views.approve_product, name='approve_product'),
    path('reject/<int:id>/', views.reject_product, name='reject_product'),
    path('edit-product/<int:pk>/', views.edit_product, name='edit_product'),
    path('delete-product/<int:pk>/', views.delete_product, name='delete_product'),
    path('seller_profile/', views.seller_profile_view, name='seller_profile'),

    
    
    
    
    # user home
    path('user_home',views.user_home,name="user_home"),
    path('view_profile/<int:id>',views.user_profile,name="user_profile"),
    path('myorders', views.my_orders, name='my_orders'),  # single order with payments

    path('logout', views.logout_all, name='logout_all'),
    path('forgot-password/', views.forgot_password_email, name='forgot_password_email'),
    path('reset-password/<int:user_id>/', views.reset_password_form, name='reset_password_form'),
    path('change-password/', views.change_password, name='change_password'),

    
    #skincare
    path('skincare',views.skincare,name="skincare"),
    
    #makeups
    path('makeups',views.makeups,name="makeups"),
    
    # haicare
    path('haircare',views.haircare,name="haircare"),
    
    #brands
   
    path('loreal',views.lorealparis,name="lorealparis"),
    path('lakmae',views.lakmae,name="lakmae"),
    path('nykaa',views.nykaa,name="nykaa"),
    path('maybelline',views.maybelline,name="maybelline"),
    path('swissbeauty',views.swiss_beauty,name="swiss_beauty"),
    
    
    
     #LOREALPARIS
    path('L_skincare',views.skincare_loreal,name="skincare_loreal"),
    path('L_makeup',views.makeup_loreal,name="makeup_loreal"),
    path('L_haircare',views.haircare_loreal,name="haircare_loreal"),
    path('lorealcontact',views.contact_submit_loreal,name="contact_submit_loreal"),
    
    
    #maybelline
    path('M_skincare',views.maybelline_skincare,name="maybelline_skincare"),
    path('M_makeup',views.maybelline_makeup,name="maybelline_makeup"),
    path('M_haircare',views.maybelline_haircare,name="maybelline_haircare"),
    
    #lakmae
    path('lakme_skincare',views.lakme_skincare,name="lakme_skincare") , 
    path('lakme_haircare',views.lakme_haircare,name="lakme_haircare") , 
    path('lakme_makeup',views.lakme_makeup,name="lakme_makeup") , 
    


    
    
    
    
    path('view_wishlist',views.view_wishlist,name="view_wishlist"),
    path('add-to-wishlist/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),  
    
    
    #shop all homepage
    path('shopall',views.shop_all_home,name="shop_all_home") , 
    
    path('product_detail/<int:id>/', views.product_detail, name="product_detail"),
    
        path('search-suggestions/', views.search_suggestions, name='search_suggestions'),

      path('wishlist/remove/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),

    # forgot password
    path('password-reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
path('reset/done/', 
     auth_views.PasswordResetCompleteView.as_view(
         template_name='rest_password/password_reset_complete.html',
     ), 
     name='password_reset_complete'),

path(
        'password-change/',
        auth_views.PasswordChangeView.as_view(
            success_url=reverse_lazy('user_home')  # Redirect here after password change
        ),
        name='password_change'
    ),
     path(
        'password-change/done/',
        auth_views.PasswordChangeDoneView.as_view(),
        name='password_change_done'
    ),
     
     
path('submit-review/<int:product_id>/<int:order_id>/', views.submit_review, name='submit_review'),
    path('track-order/<int:item_id>/', views.track_order, name='track_order'),
   path('request-return/<int:item_id>/', views.request_return, name='request_return'),
    path('cancel-order/<int:item_id>/', views.cancel_order, name='cancel_order_item'),
    # path('contact-support/', views.contact_support, name='contact_support'),
]