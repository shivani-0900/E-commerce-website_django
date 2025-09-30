from django.shortcuts import render,redirect
from .models import User_Table,ProductApproval,ProductImage
from cart.models import cart
from order.models import Order,Payment_details
from django.http import HttpResponse
from django.contrib.auth import authenticate,login,logout
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Avg
from cart.models import Wishlist
from decimal import Decimal,InvalidOperation
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from User.models import User_Table
from address.models import Address
from django.urls import reverse
from django.contrib.auth.decorators import login_required

from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model

User = get_user_model()
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model

User = get_user_model()

def forgot_password_email(request):
    context = {}
    
    if request.method == 'POST':
        email = request.POST.get('email')
        if not email:
            context['error'] = "Please enter an email address."
        else:
            users = User.objects.filter(email=email)
            if not users.exists():
                context['error'] = "No user found with this email address."
            else:
                user = users.first()  # Use the first user if multiple found
                return redirect('User:reset_password_form', user_id=user.id)
    
    return render(request, 'buyer/forgot_password_email.html', context)



def reset_password_form(request, user_id):
    user = get_object_or_404(User_Table, id=user_id)
    context = {'user': user}

    if request.method == 'POST':
        password = request.POST.get('new_password')
        user.set_password(password)
        user.save()

        # Send confirmation email
        subject = 'Password Reset Successful - Glamnest'
        message = f"Hello {user.username},\n\nYour password has been successfully reset. You can now log in with your new password.\n\n- Team Glamnest"
        from_email = settings.EMAIL_HOST_USER if hasattr(settings, 'EMAIL_HOST_USER') else 'admin@glamnest.com'
        recipient_list = [user.email]
        
        send_mail(subject, message, from_email, recipient_list, fail_silently=False)

        context['success'] = "Password has been reset. A confirmation email has been sent."
    
    return render(request, 'buyer/reset_password_form.html', context)

from django.contrib.auth import update_session_auth_hash
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from User.models import User_Table
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.conf import settings

@login_required
def change_password(request):
    if request.method == 'POST':
        current = request.POST.get('current_password')
        new = request.POST.get('new_password')
        confirm = request.POST.get('confirm_password')

        user = request.user

        if not user.check_password(current):
            messages.error(request, 'incorrect')
        elif new != confirm:
            messages.error(request, 'mismatch')
        else:
            user.set_password(new)
            user.save()
            update_session_auth_hash(request, user)

            # ✅ send email
            send_mail(
                'Password Changed Successfully - GlamNest',
                f'Hi {user.username},\n\nYour password has been changed successfully.',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )

            messages.success(request, 'success')
            return redirect('User:user_login')  # ✅ or wherever your login page is

    return render(request, 'buyer/change_password.html')

# Create your views here.
def home(request):
    return render(request,'home.html')
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import User_Table  # Assuming custom user model

def user_login(request):
    if request.method == 'POST':
        usn = request.POST.get('username')
        pwd = request.POST.get('password')
        user = authenticate(request, username=usn, password=pwd)

        if user:
            if user.usertype == 'Seller' and not user.is_approved:
                return render(request, 'buyer/user_login.html', {
                    'error': 'Your seller account is pending admin approval.'
                })

            login(request, user)

            if user.is_superuser:
                request.session['a_id'] = user.id
                return redirect('User:admin_home')
            elif user.usertype == 'Buyer':
                request.session['b_id'] = user.id
                return redirect('User:user_home')
            elif user.usertype == 'Seller':
                request.session['s_id'] = user.id
                return redirect('User:seller_home')
            else:
                return render(request, 'buyer/user_login.html', {
                    'error': 'Invalid user type.'
                })

        return render(request, 'buyer/user_login.html', {
            'error': 'Invalid username or password.'
        })

    return render(request, 'buyer/user_login.html')


from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import render, redirect
from .models import User_Table  # Adjust if your model is imported differently
from django.shortcuts import resolve_url

def user_register(request):
    # Use resolve_url to safely redirect to named views or paths
    next_url = request.GET.get('next') or request.POST.get('next') or '/'

    if not next_url:
        next_url = resolve_url('User:user_home')  # Redirect to homepage by default

    if request.method == 'POST':
        usn = request.POST['username']
        em = request.POST['email']
        phn = request.POST['phone']
        gender = request.POST['gender']
        pwd = request.POST['password1']
        con_pwd = request.POST['password2']

        if pwd != con_pwd:
            return render(request, 'buyer/user_register.html', {
                'error': 'Passwords do not match.',
                'next': next_url
            })

        x = User_Table.objects.create_user(
            username=usn,
            email=em,
            phone=phn,
            gender=gender,
            password=pwd,
            usertype='Buyer',
        )
        login(request, x)

        # Merge session cart into user cart
        session_cart = request.session.get('cart', {})
        for product_id, quantity in session_cart.items():
            try:
                product = ProductApproval.objects.get(id=product_id)
                cart_item, created = cart.objects.get_or_create(user=x, product=product)
                cart_item.quantity += quantity
                cart_item.save()
            except ProductApproval.DoesNotExist:
                continue

        request.session['cart'] = {}

        # Send welcome email
        send_mail(
            subject="🎉 Welcome to GlamNest!",
            message=(f"Hi {usn},\n\nYour GlamNest account has been successfully created!\n\n"
                     "You can now log in and start shopping:\n"
                     "🔗 Login here: https://yourdomain.com/uselogin\n\n"
                     "We’re excited to have you with us 💄✨\n\n– The GlamNest Team"),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[em],
            fail_silently=False,
        )

        return redirect(next_url)

    return render(request, 'buyer/user_register.html', {'next': next_url})

from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .models import User_Table

def seller_register(request):
    if request.method == 'POST':
        usn = request.POST['username']
        em = request.POST['email']
        phn = request.POST['phone']
        brand = request.POST['brand']
        pwd = request.POST['password1']
        con_pwd = request.POST['password2']

        if pwd != con_pwd:
            messages.error(request, "Passwords do not match.")
            return render(request, 'seller/seller_register.html')

        # Create inactive seller
        x = User_Table.objects.create_user(
            username=usn,
            email=em,
            phone=phn,
            brand=brand,
            password=pwd,
            usertype='Seller',
            is_active=False  # Inactive until admin approval
        )
        x.save()

        # Send mail to seller
        subject = "GlamNest Seller Registration - Awaiting Approval"
        message = f"""
        Hi {usn},

        Thank you for registering as a seller on GlamNest.

        Your registration is successful but pending approval from the admin.
        You will be notified once your account is activated.

        Regards,
        GlamNest Team
        """
        send_mail(subject, message, settings.EMAIL_HOST_USER, [em])

        # Add success message
        messages.success(request, "✔️ Registration successful! Please wait for admin approval.")
        return render(request, 'seller/seller_register.html')

    return render(request, 'seller/seller_register.html')

    
#Admin Home


from django.shortcuts import render
from .models import User_Table, ProductApproval  # Adjust import if needed

from datetime import datetime
from django.shortcuts import render
from .models import User_Table, ProductApproval  # Make sure to import your Product model

from datetime import timedelta, datetime
from django.utils.timezone import now
from django.db.models import Sum
from django.db.models import Sum

def admin_home(request):
    pending_sellers = User_Table.objects.filter(usertype='Seller', is_approved=False).count()
    unapproved_products = ProductApproval.objects.filter(status__iexact='pending').count()
    total_buyers = User_Table.objects.filter(usertype='Buyer').count()
    total_sellers = User_Table.objects.filter(usertype='Seller', is_approved=True).count()
    total_products = ProductApproval.objects.count()

    # New stats
    total_orders = Order.objects.count()
    total_revenue = Order.objects.aggregate(total=Sum('final_price'))['total'] or 0

    recent_products = ProductApproval.objects.order_by('-created_at')[:5]
    recent_sellers = User_Table.objects.filter(usertype='Seller').order_by('-date_joined')[:5]

    recent_activities = []
    for product in recent_products:
        recent_activities.append({
            'action': f"{product.status.title()} Product",
            'name': product.product_name,
            'date': product.created_at
        })
    for seller in recent_sellers:
        action = "Approved Seller" if seller.is_approved else "Registered Seller"
        recent_activities.append({
            'action': action,
            'name': seller.username,
            'date': seller.date_joined
        })

    recent_activities.sort(key=lambda x: x['date'], reverse=True)
    recent_activities = recent_activities[:8]

    context = {
        'pending_sellers': pending_sellers,
        'unapproved_products': unapproved_products,
        'total_buyers': total_buyers,
        'total_sellers': total_sellers,
        'total_products': total_products,
        'recent_activities': recent_activities,
        'product_list': ProductApproval.objects.all(),
        'total_orders': total_orders,
        'total_revenue': total_revenue,
    }
    return render(request, 'admin/admin_home.html', context)

def help(request):
    return render(request,'admin/help.html')

def  help_home(request):
    return render(request,'buyer/help_home.html')

def unapproved_sellers(request):
    
    sellers = User_Table.objects.filter(usertype='Seller', is_approved=False)
    return render(request, 'admin/seller_approve_admin.html', {'sellers': sellers})

from django.core.mail import send_mail
from django.conf import settings

from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponse
from .models import User_Table  # Adjust import based on your project structure

def approve_sellers(request, id):
    seller = get_object_or_404(User_Table, id=id)
    
    seller.is_approved = True
    seller.is_active = True  # ✅ Allow login
    seller.save()

    # Send approval email
    subject = "Approval Confirmation - GlamNest"
    message = f"""
    Dear {seller.username},

    Congratulations! Your seller account has been approved by the admin.

    You can now log in and start listing your products.

    Best regards,
    GlamNest Team
    """
    try:
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [seller.email],
            fail_silently=False
        )
        messages.success(request, f"Seller '{seller.username}' approved successfully.")
    except Exception as e:
        messages.error(request, f"Seller '{seller.username}' approved but failed to send email: {e}")
        return HttpResponse(f"Seller approved but failed to send email: {e}")

    return redirect('User:unapproved_sellers')


def reject_seller(request, id):
    seller = get_object_or_404(User_Table, id=id)

    # Send rejection email
    subject = "Seller Application Update - GlamNest"
    message = f"Dear {seller.username},\n\nWe regret to inform you that your seller application has been rejected.\n\nFor more information, contact support.\n\nBest regards,\nGlamNest Team"
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [seller.email]

    try:
        send_mail(subject, message, from_email, recipient_list, fail_silently=False)
        messages.success(request, f"Seller '{seller.username}' rejected successfully.")
    except Exception as e:
        messages.error(request, f"Seller '{seller.username}' rejected but failed to send email: {e}")
        return HttpResponse(f"Seller rejected but failed to send email: {e}")

    seller.delete()  # Optional: delete if rejected
    return redirect('User:admin_home')
def view_seller(request):
    seller=User_Table.objects.filter(usertype="Seller")
    return render(request,'admin/View_Seller.html',{'seller':seller})

def view_buyer(request):
    buyer=User_Table.objects.filter(usertype="Buyer")
    return render(request,'admin/View_Buyer.html',{'buyer':buyer})



#seller home
from django.utils import timezone
from django.db.models import Sum, F
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from User.models import ProductApproval, User_Table
from order.models import OrderItem
from datetime import datetime

from django.utils import timezone
from django.db.models import Sum
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from User.models import ProductApproval
from order.models import OrderItem
from datetime import datetime
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.utils import timezone

from django.db.models import Sum, F, DecimalField, ExpressionWrapper, Q
from django.utils import timezone
from datetime import timedelta
from cart.models import ProductRating, ProductReview  # adjust import path if needed
from django.db.models import F, Sum, DecimalField, ExpressionWrapper
from django.utils.timezone import now
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from order.models import OrderItem
from .models import ProductApproval # adjust import paths as needed


@login_required
def seller_home(request):
    seller = request.user

    # Approved products by seller
    seller_products = ProductApproval.objects.filter(seller=seller, status__iexact='approved')
    total_products = seller_products.count()

    # Pending orders
    pending_orders = OrderItem.objects.filter(seller=seller, status__iexact='Pending').count()

    # Total amount from delivered orders
    amount_expr = ExpressionWrapper(
        F('price') * F('quantity'),
        output_field=DecimalField(max_digits=20, decimal_places=2)
    )

    delivered_items = OrderItem.objects.filter(
        seller=seller,
        status='Delivered'
    )

    total_amount_data = delivered_items.aggregate(total_amount=Sum(amount_expr))
    total_amount = total_amount_data['total_amount'] or Decimal('0.00')
    formatted_total_amount = f"₹{total_amount:,.2f}"

    # New reviews in last 7 days
    seven_days_ago = now() - timedelta(days=7)
    new_reviews = ProductReview.objects.filter(
        rating__product__seller=seller,
        created_at__gte=seven_days_ago
    ).count()

    # Recent 5 delivered orders
    recent_orders = delivered_items.select_related('order', 'product').order_by('-order__created_at')[:5]

    # Top 5 customers by spend
    top_customers = delivered_items.values(
        'order__buyer__id',
        'order__buyer__username',
            'order__buyer__profile_image'   # 👈 add this

    ).annotate(
        total_spent=Sum(amount_expr)
    ).order_by('-total_spent')[:5]

    context = {
        'total_products': total_products,
        'pending_orders': pending_orders,
        'total_amount': formatted_total_amount,
        'new_reviews': new_reviews,
        'current_month': now().strftime("%B %Y"),
        'recent_orders': recent_orders,
        'top_customers': top_customers,
         "MEDIA_URL": settings.MEDIA_URL,  
    }

    return render(request, 'seller/seller_home.html', context)

@login_required
def request_return(request, item_id):
    item = get_object_or_404(OrderItem, id=item_id, order__buyer=request.user)

    if item.status == "Delivered" and not item.returned:
        item.returned = True
        item.status = "Returned"  # Optional: also update status
        item.save()
        messages.success(request, f"Return request for Order Item #{item.id} has been submitted.")
    else:
        messages.error(request, "Return request cannot be processed.")

    return redirect('User:view_order', order_id=item.order.id)

@login_required
def cancel_order_item(request, item_id):
    item = get_object_or_404(OrderItem, id=item_id, order__buyer=request.user)

    if item.status == 'Pending':
        item.status = 'Cancelled'
        item.save()
        messages.success(request, "Order has been cancelled successfully.")
    else:
        messages.error(request, "Cannot cancel this order item.")

    return redirect('User:view_order', order_id=item.order.id)


from decimal import Decimal, InvalidOperation
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import User_Table, ProductApproval, ProductImage

def add_product_seller(request):
    if request.method == 'POST':
        try:
            s_id = request.session.get('s_id')
            seller_data = User_Table.objects.get(id=s_id)

            # Required Fields
            product_name = request.POST.get('product_name')
            description = request.POST.get('description')
            price_str = request.POST.get('price')
            product_type = request.POST.get('product_type')
            category = request.POST.get('category')

            # Basic validation
            if not all([product_name, description, price_str, product_type, category]):
                messages.error(request, "Please fill in all required fields.")
                return redirect('User:add_product_seller')
            quantity = None  # Default to None unless needed

            # Only required for Skincare and Haircare
            if product_type in ['Skincare', 'Haircare']:
                quantity_str = request.POST.get('quantity')
                if not quantity_str:
                    messages.error(request, f"Please select a quantity for {product_type}.")
                    return redirect('User:add_product_seller')
                try:
                    quantity = int(quantity_str)
                except (ValueError, TypeError):
                    messages.error(request, "Quantity must be a valid number.")
                    return redirect('User:add_product_seller')

            # Price validation
            try:
                price = Decimal(price_str)
            except InvalidOperation:
                messages.error(request, "Price must be a valid decimal number.")
                return redirect('User:add_product_seller')

            # Optional fields
            ingredients = request.POST.get('ingredients')
            how_to_use = request.POST.get('how_to_use')
            expiry_date = request.POST.get('expiry_date') or None
            country_of_origin = request.POST.get('country_of_origin')
            brand_address = request.POST.get('brand_address')
            manufacturer = request.POST.get('manufacturer')

            # Conditional fields
            skin_type = request.POST.get('skin_type') if product_type == 'Skincare' else 'None'
            skin_tone = request.POST.get('skin_tone') if product_type == 'Makeup' else 'None'
            hair_texture = request.POST.get('hair_texture') if product_type == 'Haircare' else 'None'

            # Create product
            product = ProductApproval.objects.create(
                seller=seller_data,
                product_name=product_name,
                brand_name=seller_data.brand,
                description=description,
                ingredients=ingredients,
                how_to_use=how_to_use,
                quantity=quantity,
                price=price,
                expiry_date=expiry_date,
                country_of_origin=country_of_origin,
                brand_address=brand_address,
                manufacturer=manufacturer,
                product_type=product_type,
                category=category,
                skin_type=skin_type,
                skin_tone=skin_tone,
                hair_texture=hair_texture,
                status='pending',
            )

            # Handle images
            images = request.FILES.getlist('images')
            if images:
                product.image = images[0]  # Set first as main image
                product.save()
                for image in images:
                    ProductImage.objects.create(product=product, image=image)

            messages.success(request, "Product added successfully with images.")
            return redirect('User:add_product_seller')

        except User_Table.DoesNotExist:
            messages.error(request, "Seller not found. Please log in again.")
            return redirect('User:User_login')

        except Exception as e:
            messages.error(request, f"An unexpected error occurred: {str(e)}")
            return redirect('User:add_product_seller')

    # GET method
    quantity_choices = ProductApproval.QUANTITY_CHOICES if hasattr(ProductApproval, 'QUANTITY_CHOICES') else []
    try:
        s_id = request.session.get('s_id')
        seller_data = User_Table.objects.get(id=s_id)
        brand_name = seller_data.brand
    except User_Table.DoesNotExist:
        brand_name = ''

    return render(request, 'seller/S_add_product.html', {
        'quantity_choices': quantity_choices,
        'brand_name': brand_name,
    })


def unapproved_products(request):
    products = ProductApproval.objects.filter(status='pending')
    return render(request, 'admin/product_approve_admin.html', {'products': products})

from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.http import HttpResponse
from .models import ProductApproval  # Adjust import based on your project structure

def approve_product(request, id):
    try:
        product = ProductApproval.objects.get(id=id)
        product.status = 'approved'
        product.save()
        messages.success(request, f"Product '{product.product_name}' approved successfully.")  # Assuming product has a 'name' field
        return redirect('User:unapproved_products')
    except ProductApproval.DoesNotExist:
        messages.error(request, "Product not found.")
        return HttpResponse("Product not found")

def reject_product(request, id):
    try:
        product = ProductApproval.objects.get(id=id)
        product.status = 'rejected'
        product.save()
        messages.success(request, f"Product '{product.product_name}' rejected successfully.")  # Assuming product has a 'name' field
        return redirect('User:admin_home')
    except ProductApproval.DoesNotExist:
        messages.error(request, "Product not found.")
        return HttpResponse("Product not found")
def seller_product_list(request):
    seller = request.user.id 
    products = ProductApproval.objects.filter(seller=seller)
    # print(products)
    return render(request, 'seller/seller_products_list.html', {"data":products})
from django.shortcuts import render
from .models import ProductApproval
from cart.models import cart,Wishlist
from random import sample

def user_home(request):
    approved_products = ProductApproval.objects.filter(status='approved')
    featured_products = sample(list(approved_products), min(10, len(approved_products)))  # show 10 random ones

    wishlist_count = cart_count = 0
    if request.user.is_authenticated:
        wishlist_count = Wishlist.objects.filter(user=request.user).count()
        cart_count = cart.objects.filter(user=request.user).count()

    return render(request, 'buyer/user_home.html', {
        'featured_products': featured_products,
        'wishlist_count': wishlist_count,
        'cart_count': cart_count
    })




from django.contrib import messages

def user_profile(request, id):
    user_obj = get_object_or_404(User_Table, id=id)
    address_obj = Address.objects.filter(user=user_obj, is_default=True).first()
    if not address_obj:
        address_obj = Address.objects.filter(user=user_obj).first()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'reset':
            messages.info(request, "Changes discarded.")
            return redirect(reverse('User:user_profile', kwargs={'id': user_obj.id}))

        elif action == 'update':
            try:
                user_obj.username = request.POST.get('username')
                user_obj.phone = request.POST.get('phone')
                user_obj.email = request.POST.get('email')

                # ✅ handle profile image
                if 'profile_image' in request.FILES:
                    user_obj.profile_image = request.FILES['profile_image']

                user_obj.save()

                address_line = request.POST.get('address')
                if address_obj:
                    address_obj.address_line = address_line
                    address_obj.save()
                else:
                    Address.objects.create(user=user_obj, address_line=address_line, is_default=True)

                messages.success(request, "Profile updated successfully.")
            except Exception as e:
                messages.error(request, f"Error updating profile: {e}")

            return redirect(reverse('User:user_profile', kwargs={'id': user_obj.id}))

    context = {
        'data': user_obj,
        'address': address_obj or Address(address_line=''),
    }
    return render(request, 'buyer/view_profile.html', context)
@login_required
def my_orders(request):
    orders = (
        Order.objects
        .filter(buyer=request.user)  # ✅ Directly use request.user
        .select_related('address')
        .prefetch_related('items__product', 'payments')
        .order_by('-created_at')
    )
    return render(request, 'buyer/my_order.html', {'orders': orders})



from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from decimal import Decimal

@login_required
def view_order(request, order_id):
    # Ensure the logged-in buyer can only view their own order
    order = get_object_or_404(Order, id=order_id, buyer=request.user)
    
    # Prefetch related product and avoid multiple DB hits
    items = order.items.select_related('product').all()
    payment_info = Payment_details.objects.filter(order=order).first()

    # Attach user reviews for each item
    for item in items:
        try:
            rating = ProductRating.objects.get(product=item.product, user=request.user)
            review = ProductReview.objects.get(rating=rating)
            item.user_review = {
                'rating': rating.rating,
                'review': review.review_text,
                'image': review.image,
                'created_at': review.created_at,
            }
        except (ProductRating.DoesNotExist, ProductReview.DoesNotExist):
            item.user_review = None

    # Shipping cost calculation
    shipping = Decimal('0.00') if order.total_price >= 500 else Decimal('50.00')
    
    # Use discount if available
    discount = order.discount_applied or Decimal('0.00')
    
    # Get estimated delivery date
    estimated_delivery = (
        items[0].expected_delivery_date if items and items[0].expected_delivery_date else None
    )

    # Tracking steps
    tracking_steps = [
        {
            'label': 'Order Confirmed',
            'note': 'Your Order has been placed.',
            'time': order.created_at.strftime('%a, %d %b \'%y - %I:%M%p'),
        },
        {
            'label': 'Shipped',
            'note': f"Your item has been shipped. Tracking No: "
                    f"{items[0].tracking_number if items and items[0].tracking_number else 'N/A'}",
            'time': items[0].expected_delivery_date.strftime('%a, %d %b \'%y') 
                    if items and items[0].expected_delivery_date else '',
        }
    ]

    if order.status == 'Out for Delivery':
        tracking_steps.append({
            'label': 'Out For Delivery',
            'note': 'Your item is out for delivery',
            'time': timezone.now().strftime('%a, %d %b \'%y - %I:%M%p'),
        })

    if order.status == 'Delivered':
        tracking_steps.append({
            'label': 'Delivered',
            'note': 'Your item has been delivered',
            'time': order.updated_at.strftime('%a, %d %b \'%y - %I:%M%p'),
        })

    context = {
        'order': order,
        'items': items,
        'shipping': shipping,
        'discount': discount,
        'final_price': order.total_price + shipping - discount,
        'tracking_steps': tracking_steps,
        'estimated_delivery': estimated_delivery,
        'payment_info': payment_info,
    }

    return render(request, 'buyer/view_orders.html', context)


from cart.models import ProductReview,ProductRating
@login_required
def submit_review(request, product_id, order_id):
    product = get_object_or_404(ProductApproval, id=product_id)
    order = get_object_or_404(Order, id=order_id, buyer=request.user)

    # ✅ Ensure buyer actually purchased this product
    if not OrderItem.objects.filter(order=order, product=product).exists():
        messages.error(request, "You cannot review a product you haven’t purchased.")
        return redirect('User:view_order', order_id=order_id)

    if request.method == 'POST':
        try:
            rating_value = int(request.POST.get('rating'))
        except (TypeError, ValueError):
            rating_value = 0

        review_text = request.POST.get('review', '').strip()
        image = request.FILES.get('image')

        # ✅ Validate rating value
        if not 1 <= rating_value <= 5:
            messages.error(request, "Invalid rating value.")
            return redirect('User:view_order', order_id=order_id)

        # ✅ Save rating (create or update)
        rating, created = ProductRating.objects.get_or_create(
            product=product,
            user=request.user,
            defaults={'rating': rating_value}
        )
        if not created:
            rating.rating = rating_value
            rating.save()

        # ✅ Save review linked to rating
        review, _ = ProductReview.objects.get_or_create(rating=rating)
        review.review_text = review_text   # 🔥 FIXED (was review.review)
        if image:
            review.image = image
        review.save()

        messages.success(request, "Your review has been submitted successfully.")
        return redirect('User:view_order', order_id=order_id)

    return render(request, 'buyer/submit_review.html', {
        'product': product,
        'order': order,
    })

    from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from User.models import ProductApproval
from cart.models import ProductReview  # or wherever ProductReview is defined

@login_required
def seller_reviews(request):
    seller = request.user

    # Get all approved products by this seller
    seller_products = ProductApproval.objects.filter(seller=seller)

    # Get all reviews related to these products
    reviews = ProductReview.objects.filter(
        rating__product__in=seller_products
    ).select_related('rating__product', 'rating__user')

    context = {
        'reviews': reviews
    }
    return render(request, 'seller/seller_reviews.html', context)

@login_required
def track_order(request, item_id):
    item = get_object_or_404(OrderItem, pk=item_id, order__buyer=request.user)

    tracking_steps = [
        {
            "label": "Order Confirmed",
            "note": "Your order has been placed.",
            "time": item.order.created_at.strftime('%d %b, %Y - %I:%M %p')
        },
        {
            "label": "Shipped",
            "note": f"Shipped via {item.shipping_company or 'Courier'}",
            "time": item.expected_delivery_date.strftime('%d %b, %Y') if item.expected_delivery_date else "N/A"
        },
    ]

    if item.status == "Out for Delivery":
        tracking_steps.append({
            "label": "Out For Delivery",
            "note": "Your item is out for delivery",
            "time": timezone.now().strftime('%d %b, %Y - %I:%M %p')
        })

    if item.status == "Delivered":
        tracking_steps.append({
            "label": "Delivered",
            "note": "Your item has been delivered",
            "time": item.order.updated_at.strftime('%d %b, %Y - %I:%M %p')
        })

    return render(request, 'buyer/trach_order.html', {
        'item': item,
        'tracking_steps': tracking_steps,
        'estimated_delivery': item.expected_delivery_date
    })


@login_required
def request_return(request, item_id):
    item = get_object_or_404(OrderItem, pk=item_id, order__buyer=request.user)
    
    if item.status == 'Delivered' and not item.returned:
        item.returned = True  # Assuming you have a `returned` field in your OrderItem model
        item.save()
        messages.success(request, "Return request has been initiated.")
    
    return redirect('User:view_order', order_id=item.order.id)

@login_required
def cancel_order(request, item_id):
    item = get_object_or_404(OrderItem, pk=item_id, order__buyer=request.user)

    if item.status == 'Pending':
        item.status = 'Cancelled'
        item.save()
        messages.success(request, "Order has been cancelled.")
    
    return redirect('User:view_order', order_id=item.order.id)


from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from order.models import Order

def send_order_summary_email(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    subject = f"Order #{order.id} Summary"
    message = f"""
Hello {order.buyer.username},

Thank you for your order.

Order ID: {order.id}
Total: ₹{order.final_price}
Items:
"""
    for item in order.items.all():
        message += f"- {item.product.product_name} x{item.quantity} - ₹{item.price}\n"

    message += f"""
Shipping To:
{order.address.house}, {order.address.area}
{order.address.city}, {order.address.state} - {order.address.pincode}
Phone: {order.address.phone}

Thanks,
Your Company Name
"""

    send_mail(
        subject,
        message,
        'noreply@yourdomain.com',  # From
        [order.buyer.email],       # To
    )
    messages.success(request, "Order summary sent to user's email.")
    return redirect('your_order_detail_view_name', order_id=order.id)

import os
from twilio.rest import Client
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from order.models import Order  # Adjust path as needed
from dotenv import load_dotenv

load_dotenv()

def send_order_summary_sms(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    phone_number = str(order.address.phone)

    # Ensure only digits are used
    phone_number = ''.join(filter(str.isdigit, phone_number))
    if len(phone_number) != 10:
        messages.error(request, "Invalid phone number format.")
        return redirect('your_order_detail_view_name', order_id=order.id)

    # Message content
    body = f"Hi {order.buyer.username}, your Order #{order.id} of ₹{order.final_price} has been placed successfully."

    try:
        client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))
        client.messages.create(
            body=body,
            from_=os.getenv('TWILIO_PHONE_NUMBER'),
            to=f'+91{phone_number}'
        )
        messages.success(request, "Order summary sent to user's phone.")
    except Exception as e:
        messages.error(request, f"Failed to send SMS: {e}")

    return redirect('User:view_order', order_id=order.id)


from django.shortcuts import render
from django.core.paginator import Paginator
from .models import ProductApproval

def skincare(request):
    # Filter only approved skincare products
    products = ProductApproval.objects.filter(status='approved', product_type='Skincare')

    # Get filter parameters
    selected_categories = request.GET.getlist('category')
    selected_skin_types = request.GET.getlist('skin_type')
    selected_price = request.GET.get('price')

    # Apply filters
    if selected_categories:
        products = products.filter(category__in=selected_categories)
    if selected_skin_types:
        products = products.filter(skin_type__in=selected_skin_types)
    if selected_price:
        try:
            products = products.filter(price__lte=float(selected_price))
        except ValueError:
            pass

    # Pagination
    paginator = Paginator(products, 6)  # Show 6 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Filter options from model
    all_categories = [choice for choice in ProductApproval.CATEGORY_CHOICES if choice[0] in dict(ProductApproval.CATEGORY_CHOICES) and choice[0] in [p.category for p in ProductApproval.objects.filter(product_type='Skincare')]]
    skin_types = ProductApproval.SKIN_TYPE_CHOICES

    context = {
        'products': page_obj,
        'categories': all_categories,
        'skin_types': skin_types,
        'selected_category': selected_categories,
        'selected_skin_type': selected_skin_types,
        'selected_price': selected_price
    }
    return render(request, 'categories/Skincare.html', context)


from django.shortcuts import render
from django.db.models import Avg
from .models import ProductApproval  # Adjust import based on your project structure
from django.core.paginator import Paginator
from django.db.models import Avg
from .models import ProductApproval

def makeups(request):
    # Get only approved makeup products
    products = ProductApproval.objects.filter(status='approved', product_type='Makeup')

    # Get filter parameters from request
    selected_categories = request.GET.getlist('category')
    selected_skin_tones = request.GET.getlist('skin_tone')
    selected_brands = request.GET.getlist('brand')
    selected_price = request.GET.get('price')
    selected_rating = request.GET.get('rating')

    # Apply filters
    if selected_categories:
        products = products.filter(category__in=selected_categories)

    if selected_skin_tones:
        products = products.filter(skin_tone__in=selected_skin_tones)

    if selected_brands:
        products = products.filter(seller__brand__in=selected_brands)

    if selected_price:
        try:
            products = products.filter(price__lte=float(selected_price))
        except ValueError:
            pass  # Optionally: add a message to context

    if selected_rating:
        try:
            rating_value = int(selected_rating)
            products = products.annotate(avg_rating=Avg('productrating__rating')).filter(avg_rating__gte=rating_value).order_by('-avg_rating')
        except ValueError:
            pass

    # Pagination (6 per page)
    paginator = Paginator(products, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Fetch dynamic filter choices
    makeup_products = ProductApproval.objects.filter(product_type='Makeup', status='approved')
    all_categories = [choice for choice in ProductApproval.CATEGORY_CHOICES if choice[0] in makeup_products.values_list('category', flat=True)]
    skin_tones = ProductApproval.SKIN_TONE_CHOICES
    brands = makeup_products.values_list('seller__brand', flat=True).distinct()

    context = {
        'products': page_obj,
        'categories': all_categories,
        'skin_tones': skin_tones,
        'brands': brands,
        'selected_category': selected_categories,
        'selected_skin_tone': selected_skin_tones,
        'selected_brand': selected_brands,
        'selected_price': selected_price,
        'selected_rating': selected_rating,
    }

    return render(request, 'categories/Makeup.html', context)

from django.db.models import Avg
from django.shortcuts import render
from .models import ProductApproval


from django.core.paginator import Paginator
from django.db.models import Avg
from django.shortcuts import render
from .models import ProductApproval
from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Avg
from .models import ProductApproval

def haircare(request):
    # Start with approved Haircare products
    products = ProductApproval.objects.filter(status='approved', product_type='Haircare')

    # Get filter parameters
    selected_types = request.GET.getlist('type')
    selected_hair_textures = request.GET.getlist('hair_texture')
    selected_brands = request.GET.getlist('brand')
    selected_price = request.GET.get('price')
    selected_rating = request.GET.get('rating')

    # Apply filters
    if selected_types:
        products = products.filter(category__in=selected_types)

    if selected_hair_textures:
        products = products.filter(hair_texture__in=selected_hair_textures)

    if selected_brands:
        products = products.filter(seller__brand__in=selected_brands)

    if selected_price:
        try:
            products = products.filter(price__lte=float(selected_price))
        except ValueError:
            pass

    if selected_rating:
        try:
            rating_value = int(selected_rating)
            products = products.annotate(avg_rating=Avg('productrating__rating')).filter(avg_rating__gte=rating_value)
        except ValueError:
            pass

    # Pagination (6 per page)
    paginator = Paginator(products, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Filter options
    all_types = [choice for choice in ProductApproval.CATEGORY_CHOICES if choice[0] in [p.category for p in ProductApproval.objects.filter(product_type='Haircare')]]
    hair_textures = ProductApproval.HAIR_TEXTURE_CHOICES
    brands = ProductApproval.objects.filter(product_type='Haircare', status='approved').values_list('seller__brand', flat=True).distinct()

    context = {
        'products': page_obj,
        'types': all_types,
        'hair_textures': hair_textures,
        'brands': brands,
        'selected_type': selected_types,
        'selected_hair_texture': selected_hair_textures,
        'selected_brand': selected_brands,
        'selected_price': selected_price,
        'selected_rating': selected_rating,
    }

    return render(request, 'categories/haircare.html', context)


#Brands
def lorealparis(request):
    products = ProductApproval.objects.filter(
        brand_name__iexact="L'Oréal Paris",
        status='approved'
    )
    return render(request, 'brands/lorealparis.html', {'products': products})

def skincare_loreal(request):
    skin_type = request.GET.get('skin_type')
    brand_filter = "L'Oréal Paris"

    filters = {
        'status': 'approved',
        'product_type': 'Skincare',
        'seller__brand__iexact': brand_filter,
    }

    if skin_type:
        filters['skin_type__iexact'] = skin_type

    skincare_products = ProductApproval.objects.filter(**filters)

    return render(request, 'loreal/L_skincare.html', {'products': skincare_products})
def makeup_loreal(request):
    skin_type = request.GET.get('skin_type')
    skin_tone = request.GET.get('skin_tone')
    price_range = request.GET.get('price')

    filters = {
        'status': 'approved',
        'product_type': 'Makeup',
        'seller__brand__iexact': 'L\'Oréal Paris'  # Adjust as per DB value
    }

    if skin_type:
        filters['skin_type__iexact'] = skin_type
    if skin_tone:
        filters['skin_tone__iexact'] = skin_tone

    products = ProductApproval.objects.filter(**filters)

    if price_range == 'low':
        products = products.filter(price__lt=500)
    elif price_range == 'mid':
        products = products.filter(price__gte=500, price__lte=1000)
    elif price_range == 'high':
        products = products.filter(price__gt=1000)

    return render(request, 'loreal/L_makeup.html', {'products': products})

def haircare_loreal(request):
    hair_texture = request.GET.get('hair_texture')
    category = request.GET.get('category')
    price_range = request.GET.get('price')

    filters = {
        'status': 'approved',
        'product_type': 'Haircare',
        'seller__brand__iexact': "L'Oréal Paris"  # brand filter
    }

    if hair_texture:
        filters['hair_texture__iexact'] = hair_texture
    if category:
        filters['category__iexact'] = category

    products = ProductApproval.objects.filter(**filters)

    if price_range == 'low':
        products = products.filter(price__lt=500)
    elif price_range == 'mid':
        products = products.filter(price__gte=500, price__lte=1000)
    elif price_range == 'high':
        products = products.filter(price__gt=1000)

    context = {
        'products': products,
        'selected_texture': hair_texture,
        'selected_category': category,
        'selected_price': price_range,
    }

    return render(request, 'loreal/L_haircare.html', context)

from django.shortcuts import render
from .models import ProductApproval
# --- Main Lakme Products Listing ---
def lakmae(request):
    products = ProductApproval.objects.filter(
        brand_name__iexact="Lakmé",
        status='approved'
    )
    return render(request, 'brands/lakmae.html',{'products':products})

# --- Skincare ---
def lakme_skincare(request):
    skin_type = request.GET.get('skin_type')
    brand_filter = "Lakmé"

    filters = {
        'status': 'approved',
        'product_type': 'Skincare',
        'seller__brand__iexact': brand_filter,
    }

    if skin_type:
        filters['skin_type__iexact'] = skin_type

    skincare_products = ProductApproval.objects.filter(**filters)

    return render(request, 'lakme/lakme_skincare.html', {'products': skincare_products})


# --- Makeup ---
def lakme_makeup(request):
    skin_type = request.GET.get('skin_type')
    skin_tone = request.GET.get('skin_tone')
    price_range = request.GET.get('price')

    filters = {
        'status': 'approved',
        'product_type': 'Makeup',
        'seller__brand__iexact': 'Lakmé'
    }

    if skin_type:
        filters['skin_type__iexact'] = skin_type
    if skin_tone:
        filters['skin_tone__iexact'] = skin_tone

    products = ProductApproval.objects.filter(**filters)

    if price_range == 'low':
        products = products.filter(price__lt=500)
    elif price_range == 'mid':
        products = products.filter(price__gte=500, price__lte=1000)
    elif price_range == 'high':
        products = products.filter(price__gt=1000)

    return render(request, 'lakme/lakme_makeup.html', {'products': products})


# --- Haircare ---
def lakme_haircare(request):
    hair_texture = request.GET.get('hair_texture')
    category = request.GET.get('category')
    price_range = request.GET.get('price')

    filters = {
        'status': 'approved',
        'product_type': 'Haircare',
        'seller__brand__iexact': 'Lakmé'
    }

    if hair_texture:
        filters['hair_texture__iexact'] = hair_texture
    if category:
        filters['category__iexact'] = category

    products = ProductApproval.objects.filter(**filters)

    if price_range == 'low':
        products = products.filter(price__lt=500)
    elif price_range == 'mid':
        products = products.filter(price__gte=500, price__lte=1000)
    elif price_range == 'high':
        products = products.filter(price__gt=1000)

    context = {
        'products': products,
        'selected_texture': hair_texture,
        'selected_category': category,
        'selected_price': price_range,
    }

    return render(request, 'lakme/lakme_haircare.html', context)



def nykaa(request):
    products = ProductApproval.objects.filter(
        brand_name__iexact="Nykaa",
        status='approved'
    )
    
    return render (request,'brands/nykaa.html',{'products':products})

def nykaa_skin(request):
    skin_type = request.GET.get('skin_type', None)

    skincare_products = ProductApproval.objects.filter(
        status='approved',
        product_type='Skincare',
        seller__brand__iexact='Maybelline'  # Only products from Maybelline sellers
    )

    if skin_type:
        skincare_products = skincare_products.filter(
            skin_type__iexact=skin_type
        )

    return render(request, 'maybelline/M_skincare.html', {'products': skincare_products})
    
def maybelline(request):
    products = ProductApproval.objects.filter(
        brand_name__iexact="Maybelline",
        status='approved'
    )
    return render (request,'brands/maybelline.html',{'products':products})

def maybelline_skincare(request):
    skin_type = request.GET.get('skin_type', None)

    skincare_products = ProductApproval.objects.filter(
        status='approved',
        product_type='Skincare',
        seller__brand__iexact='Maybelline'  # Only products from Maybelline sellers
    )

    if skin_type:
        skincare_products = skincare_products.filter(
            skin_type__iexact=skin_type
        )

    return render(request, 'maybelline/M_skincare.html', {'products': skincare_products})

def maybelline_makeup(request):
    skin_type = request.GET.get('skin_type')
    skin_tone = request.GET.get('skin_tone')
    price_range = request.GET.get('price')

    filters = {
        'status': 'approved',
        'product_type': 'Makeup',
        'seller__brand__iexact': 'Maybelline'  # 🔍 Filter by brand
    }

    if skin_type:
        filters['skin_type__iexact'] = skin_type
    if skin_tone:
        filters['skin_tone__iexact'] = skin_tone

    products = ProductApproval.objects.filter(**filters)

    if price_range == 'low':
        products = products.filter(price__lt=500)
    elif price_range == 'mid':
        products = products.filter(price__gte=500, price__lte=1000)
    elif price_range == 'high':
        products = products.filter(price__gt=1000)

    return render(request, 'maybelline/M_makeup.html', {'products': products})

def maybelline_haircare(request):
    hair_texture = request.GET.get('hair_texture')
    category = request.GET.get('category')
    price_range = request.GET.get('price')

    filters = {
        'status': 'approved',
        'product_type': 'Haircare',
        'seller__brand__iexact': 'Maybelline'
    }

    if hair_texture:
        filters['hair_texture__iexact'] = hair_texture
    if category:
        filters['category__iexact'] = category

    products = ProductApproval.objects.filter(**filters)

    if price_range == 'low':
        products = products.filter(price__lt=500)
    elif price_range == 'mid':
        products = products.filter(price__gte=500, price__lte=1000)
    elif price_range == 'high':
        products = products.filter(price__gt=1000)

    context = {
        'products': products,
        'selected_texture': hair_texture,
        'selected_category': category,
        'selected_price': price_range,
    }

    return render(request, 'maybelline/M_haircare.html', context)


def swiss_beauty(request):
    return render (request,'brands/swiss_beauty.html')




#whislist
def view_wishlist(request):
    wishlist_items = Wishlist.objects.filter(user=request.user)
    return render(request, 'carts/wishlist.html', {'wishlist_items': wishlist_items})


def remove_from_wishlist(request, product_id):
    # Find the wishlist item for this user and product
    wishlist_item = Wishlist.objects.filter(user=request.user, product_id=product_id).first()
    if wishlist_item:
        wishlist_item.delete()
    # Redirect back to wishlist page
    return redirect('User:view_wishlist')
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from django.http import JsonResponse


def add_to_wishlist(request, product_id):
    if not request.user.is_authenticated:
        return JsonResponse({'message': 'Please login to add to wishlist'}, status=401)

    wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product_id=product_id)
    if not created:
        return JsonResponse({'message': 'Already in wishlist'})

    count = Wishlist.objects.filter(user=request.user).count()
    return JsonResponse({'message': 'Added to wishlist', 'wishlist_count': count})



def shop_all_home(request):
    approved_products = ProductApproval.objects.filter(status='approved')
    return render(request, 'buyer/shop_all.html', {'products': approved_products})
from django.db.models import Avg, Count

from django.shortcuts import render, redirect
from django.db.models import Avg
from cart.models import ProductApproval, ProductRating, ProductReview
from django.db.models import Avg

def product_detail(request, id):
    try:
        product = ProductApproval.objects.get(id=id, status='approved')
    except ProductApproval.DoesNotExist:
        return redirect('home')

    images = product.images.all()
    ratings = ProductRating.objects.filter(product=product).select_related('user')
    reviews = ProductReview.objects.filter(rating__product=product).select_related('rating', 'rating__user')
    
    avg_rating = ratings.aggregate(Avg('rating'))['rating__avg'] or 0
    total_ratings = ratings.count()

    return render(request, 'buyer/product_detail.html', {
        'product': product,
        'images': images,
        'ratings': ratings,
        'reviews': reviews,
        'avg_rating': round(avg_rating, 1),
        'total_ratings': total_ratings,
    })



# products/views.py
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .models import ProductApproval


@require_GET
def search_suggestions(request):
    query = request.GET.get('q', '').strip()
    suggestions = []

    if query:
        # Search product names or brands matching the query (case-insensitive)
        products = ProductApproval.objects.filter(product_name__icontains=query, status='approved')[:10]

        # Extract product names for suggestions
        suggestions = list(products.values_list('product_name', flat=True))

    return JsonResponse({'suggestions': suggestions})



#logout
def logout_all(request):
    logout(request)
    return redirect('/user_home') 

@login_required
def edit_product(request, pk):
    product = get_object_or_404(ProductApproval, pk=pk, seller=request.user)

    # Predefined lists
    categories = [
        "Cleanser", "Moisturizer", "Serum", "Sunscreen", "Foundation",
        "Lipstick", "Mascara", "Eyeshadow", "Shampoo", "Conditioner",
        "Hair Oil", "Hair Serum"
    ]
    skin_types = ["Oily", "Dry", "Combination", "Sensitive", "None"]
    skin_tones = ["Fair", "Light", "Medium", "Tan", "Deep", "None"]
    hair_textures = ["Straight", "Wavy", "Curly", "Coily", "None"]

    QUANTITY_CHOICES = [
    (15, '15 ml'),
    (30, '30 ml'),
    (50, '50 ml'),
    (75, '75 ml'),
    (100, '100 ml'),
    ]
    if request.method == 'POST':
        product.product_name = request.POST.get('product_name')
        product.description = request.POST.get('description')
        product.category = request.POST.get('category')
        product.price = request.POST.get('price')
        product.quantity = request.POST.get('quantity')
        product.product_type = request.POST.get('product_type')  # If present in form
        product.skin_type = request.POST.get('skin_type')        # If present in form
        product.skin_tone = request.POST.get('skin_tone')        # If present in form
        product.hair_texture = request.POST.get('hair_texture')  # If present in form

        # Handle optional new image upload
        if request.FILES.get('image'):
            product.image = request.FILES['image']

        product.save()
        return redirect('User:seller_product_list')  # Or use reverse('product_detail', args=[product.pk])

    return render(request, 'seller/edit_product.html', {
        'product': product,
        'categories': categories,
        'skin_types': skin_types,
        'skin_tones': skin_tones,
        'hair_textures': hair_textures,
        'quantity_choices': QUANTITY_CHOICES,
    })
@login_required
def delete_product(request, pk):
    product = get_object_or_404(ProductApproval, pk=pk, seller=request.user)
    
    # Only allow POST for deletion to prevent accidental deletes
    if request.method == 'POST':
        product.delete()
        return redirect('User:seller_product_list')

    # Redirect if accessed via GET (optional)
    return redirect('User:seller_product_list')

from django.utils import timezone
from django.db.models import Q
from itertools import chain
from operator import attrgetter

from coupen.models import Coupon
@login_required
def seller_profile_view(request):
    seller = request.user  
    if seller.usertype != "Seller":
        return render(request, 'unauthorized.html')

    products = ProductApproval.objects.filter(seller=seller).order_by('-created_at')

    # Get recent product additions/updates
    product_activities = products.values(
        'product_name', 'created_at'
    )[:5]

    # Get recent orders fulfilled by this seller
    order_activities = OrderItem.objects.filter(seller=seller).order_by('-order__created_at')[:5]

    # Get coupons created (if you track seller relationship)
    coupons = Coupon.objects.filter(applicable_brand=seller.brand).order_by('-valid_from')[:5]

    # Combine all activities with labels
    activity_list = []

    for p in product_activities:
        activity_list.append({
            'action': f'Added new product "{p["product_name"]}"',
            'time': p['created_at'],
        })

    for o in order_activities:
        activity_list.append({
            'action': f'Fulfilled Order #{o.order.id} - {o.product.product_name}',
            'time': o.order.created_at,
        })

    for c in coupons:
        activity_list.append({
            'action': f'Created coupon "{c.code}"',
            'time': c.valid_from,
        })

    # Sort by latest time
    activity_list = sorted(activity_list, key=lambda x: x['time'], reverse=True)[:10]

    return render(request, 'seller/seller_profile.html', {
        'seller': seller,
        'products': products,
        'activities': activity_list,
    })

from django.shortcuts import render
from django.db.models import Q
from .models import ProductApproval
from django.core.paginator import Paginator

def search_results(request):
    query = request.GET.get('q', '').strip()
    products = ProductApproval.objects.filter(
        Q(status='approved') &
        (
            Q(product_name__icontains=query) |
            Q(brand_name__icontains=query) |
            Q(category__icontains=query) |
            Q(product_type__icontains=query)
        )
    ).select_related('seller')
    
    paginator = Paginator(products, 12)  # 12 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'query': query,
        'products': page_obj,
        'page_obj': page_obj,
    }
    return render(request, 'buyer/search_results.html', context)

from django.http import JsonResponse

def product_suggestions(request):
    query = request.GET.get('q', '').strip()
    suggestions = []

    if query:
        products = ProductApproval.objects.filter(
            Q(status='approved') &
            (
                Q(product_name__icontains=query) |
                Q(brand_name__icontains=query) |
                Q(category__icontains=query) |
                Q(product_type__icontains=query)
            )
        )[:5]  # Limit to 5 suggestions
        suggestions = [product.product_name for product in products]

    return JsonResponse({'suggestions': suggestions})


from django.core.mail import send_mail
from django.shortcuts import render, redirect
from .models import ContactMessage
from django.contrib import messages

def contact_submit(request):
    if request.method == 'POST':
        name = request.POST['name']
        email = request.POST['email']
        message_content = request.POST['message']

        # Save to DB
        ContactMessage.objects.create(
            name=name,
            email=email,
            message=message_content
        )

        # Email to admin
        send_mail(
            subject=f"New Contact Message from {name}",
            message=f"Name: {name}\nEmail: {email}\n\nMessage:\n{message_content}",
            from_email=email,  # or use DEFAULT_FROM_EMAIL
            recipient_list=['shivani.k2125@gmail.com'],  # Glamenst owner's email
            fail_silently=False,
        )

        messages.success(request, 'Your message was sent successfully!')
        return redirect('User:user_home')  # or wherever your contact form lives

    return redirect('User:user_home')


def contact_submit_loreal(request):
    if request.method == 'POST':
        name = request.POST['name']
        email = request.POST['email']
        message_content = request.POST['message']

        # Save to DB
        ContactMessage.objects.create(
            name=name,
            email=email,
            message=message_content
        )

        # Email to admin
        send_mail(
            subject=f"New Contact Message from {name}",
            message=f"Name: {name}\nEmail: {email}\n\nMessage:\n{message_content}",
            from_email=email,  # or use DEFAULT_FROM_EMAIL
            recipient_list=['shivani.k2125@gmail.com'],  # Glamenst owner's email
            fail_silently=False,
        )

        messages.success(request, 'Your message was sent successfully!')
        return redirect('User:lorealparis')  # or wherever your contact form lives

    return redirect('User:lorealparis')
