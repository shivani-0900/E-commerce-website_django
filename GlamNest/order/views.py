import json
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.utils import timezone
from django.core.mail import send_mail
from razorpay.errors import SignatureVerificationError
import razorpay
from User.models import ProductApproval

from .models import OrderItem, Order, Payment_details, get_expected_delivery_date
from cart.models import cart, Wishlist
from coupen.models import Coupon
from address.models import Address

client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Order, Payment_details
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from order.models import Order, OrderItem

@login_required
def seller_orders_view(request):
    seller = request.user

    order_items = OrderItem.objects.filter(product__seller=seller).select_related('product', 'order')

    grouped_orders = {
        'Pending': [],
        'Shipped': [],
        'Out for Delivery': [],
        'Delivered': [],
        'Returned': [],
        'Cancelled': [],
    }

    for item in order_items:
        grouped_orders.get(item.status, []).append(item)

    context = {
        'grouped_orders': grouped_orders,
    }
    return render(request, 'seller/seller_order_grouped.html', context)


from django.db.models import Q

@login_required
def seller_pending_orders_view(request):
    seller = request.user

    orders = (
        Order.objects
        .filter(items__product__seller=seller, items__status='Pending')
        .select_related('address')
        .prefetch_related('items__product', 'payments')
        .distinct()
        .order_by('-created_at')
    )

    return render(request, 'seller/pending_order.html', {'orders': orders})

@login_required
def mark_orderitem_shipped(request, item_id):
    item = get_object_or_404(OrderItem, id=item_id, seller=request.user)

    if request.method == "POST":
        shipping_company = request.POST.get("shipping_company")
        tracking_number = request.POST.get("tracking_number")

        if shipping_company and tracking_number:
            item.status = "Shipped"
            item.shipping_company = shipping_company
            item.tracking_number = tracking_number

            # Calculate expected delivery date
            pincode = item.order.address.pincode
            item.expected_delivery_date = get_expected_delivery_date(pincode)
            item.save()

            # ✅ Send Email to Buyer
            buyer_email = item.order.buyer.email
            buyer_name = item.order.buyer.username
            order_id = item.order.id

            subject = f"📦 Your Order #{order_id} Has Been Shipped!"
            message = (
                f"Hi {buyer_name},\n\n"
                f"Your item '{item.product.product_name}' has been shipped via {shipping_company}.\n"
                f"Tracking Number: {tracking_number}\n"
                f"Estimated Delivery Date: {item.expected_delivery_date.strftime('%d %B %Y')}\n\n"
                f"Thank you for shopping with us!\n"
                f"- GlamNest Team"
            )

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [buyer_email],
                fail_silently=False,
            )

    return redirect('order:seller_orders_view')

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Order
from User.models import User_Table


@login_required
def seller_completed_orders_view(request):
    seller = request.user

    orders = (
        Order.objects
        .filter(items__product__seller=seller, items__status='Delivered')
        .select_related('address')
        .prefetch_related('items__product', 'payments')
        .distinct()
        .order_by('-created_at')
    )

    return render(request, 'seller/c.html', {'orders': orders})

@login_required
def seller_cancelled_orders_view(request):
    seller = request.user

    cancelled_orders = (
        Order.objects
        .filter(items__product__seller=seller, items__status='Cancelled')
        .select_related('address')  # Optional: if Order has FK to Address
        .prefetch_related('items__product', 'payments')
        .distinct()
        .order_by('-created_at')
    )

    return render(request, 'seller/cancelled_orders.html', {'orders': cancelled_orders})

@login_required
def seller_returned_orders_view(request):
    seller = request.user

    orders = (
        Order.objects
        .filter(items__seller=seller, items__returned=True)
        .select_related('address')
        .prefetch_related('items__product', 'payments')
        .distinct()
        .order_by('-created_at')
    )

    return render(request, 'seller/returned_order.html', {'orders': orders})

def create_payment_order(request, order_id):
    if not request.user.is_authenticated:
        return HttpResponse("Unauthorized", status=401)

    # ✅ Fetch the order and validate
    order = get_object_or_404(Order, id=order_id, status='Pending')

    if not order.buyer:
        order.buyer = request.user
        order.save()

    if order.buyer != request.user:
        return HttpResponse("You do not have permission to access this order.", status=403)

    # ✅ Get current cart items
    cart_items = cart.objects.filter(user=request.user)
    if not cart_items.exists():
        return HttpResponse("Cart is empty. Please add items before proceeding to payment.", status=400)

    # ✅ Calculate totals
    cart_total = sum(item.product.price * item.quantity for item in cart_items)
    shipping = Decimal('50.00') if cart_total <= 500 else Decimal('0.00')
    discount = Decimal('0.00')

    applied_coupon = None
    if 'applied_coupon' in request.session:
        try:
            applied_coupon = Coupon.objects.get(code=request.session['applied_coupon'])
            if applied_coupon.is_valid(request.user, cart_total, cart_items):
                discount = applied_coupon.discount_amount
            else:
                request.session.pop('applied_coupon', None)
        except Coupon.DoesNotExist:
            request.session.pop('applied_coupon', None)

    grand_total = cart_total + shipping - discount

    # ✅ Update the order
    order.total_price = cart_total
    order.final_price = grand_total
    order.coupon = applied_coupon
    order.save()

    # ✅ Create OrderItem records
    for item in cart_items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            seller=item.product.seller,
            quantity=item.quantity,
            price=item.product.price * item.quantity,
            status="Pending"
        )

    # ✅ Validate amount
    amount_paise = int(grand_total * 100)
    if amount_paise < 100:
        return HttpResponse("Minimum order amount must be ₹1.", status=400)

    # ✅ Create Razorpay order
    razorpay_order = client.order.create(dict(
        amount=amount_paise,
        currency='INR',
        payment_capture='0'
    ))

    # ✅ Save payment record
    payment = Payment_details.objects.create(
        user=order.buyer,
        order=order,
        payment_method='Razorpay',
        status='Pending',
        amount_paid=grand_total,
        razorpay_order_id=razorpay_order['id'],
    )

    # ✅ Render the checkout page
    context = {
        "razorpay_key_id": settings.RAZORPAY_KEY_ID,
        "razorpay_order_id": razorpay_order['id'],
        "amount": amount_paise,
        "amount_rupees": grand_total,
        "currency": "INR",
        "order": order,
        "payment": payment,
        "callback_url": "/order/verify_payment/",
    }

    return render(request, 'order/razorpay_checkout.html', context)

import json
import hmac
import hashlib
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import Order, Payment_details
from django.conf import settings

from django.views.decorators.csrf import csrf_exempt
import razorpay
from django.conf import settings
from django.http import JsonResponse
from .models import Payment_details
import json
from django.utils import timezone

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.utils import timezone
import json
import razorpay
from .models import Payment_details, Order
from django.conf import settings
from django.core.mail import send_mail
from django.conf import settings

@csrf_exempt
def verify_payment(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            razorpay_payment_id = data.get('razorpay_payment_id')
            razorpay_order_id = data.get('razorpay_order_id')
            razorpay_signature = data.get('razorpay_signature')

            if not (razorpay_order_id and razorpay_payment_id and razorpay_signature):
                return JsonResponse({'status': 'failure', 'message': 'Missing payment info'}, status=400)

            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

            # Verify signature
            client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            })

            payment = Payment_details.objects.get(razorpay_order_id=razorpay_order_id)
            order = payment.order

            # Mark payment and order as paid
            payment.status = "Paid"
            payment.payment_date = timezone.now()
            payment.transaction_id = razorpay_payment_id
            payment.razorpay_signature = razorpay_signature
            payment.save()

            order.status = "Paid"
            order.save()

            # Email confirmation to buyer
            send_mail(
                subject=f"✅ Payment Received for Order #{order.id}",
                message=f"Hi {order.buyer.username},\n\nYour payment was successful.\nOrder ID: {order.id}\nAmount: ₹{order.final_price}\n\nThanks for shopping with us!",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[order.buyer.email],
                fail_silently=False
            )
            order_items = order.items.select_related('seller', 'product')

            for item in order_items:
                seller_email = item.seller.email
                seller_name = item.seller.username
                product_name = item.product.product_name
                quantity = item.quantity
                total_price = item.price * item.quantity   
    
            send_mail(
                subject=f"📦 New Order Received for {product_name}",
                message=(
                    f"Hi {seller_name},\n\n"
                    f"You have received a new order:\n"
                    f"- Product: {product_name}\n"
                    f"- Quantity: {quantity}\n"
                    f"- Total Price: ₹{total_price}\n"
                    f"- Order ID: {order.id}\n\n"
                    f"Please process the order promptly.\n\nRegards,\nGlamNest Team"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[seller_email],
                fail_silently=False
            )

            # Clear cart for logged-in user or guest
            if request.user.is_authenticated:
                cart.objects.filter(user=order.buyer).delete()
            else:
                request.session['cart'] = {}
                request.session.pop('applied_coupon', None)
                request.session.modified = True

            # Redirect to home page
            return JsonResponse({'status': 'success', 'user_home': '/'})

        except razorpay.errors.SignatureVerificationError:
            return JsonResponse({'status': 'failure', 'message': 'Signature verification failed'}, status=400)

        except Payment_details.DoesNotExist:
            return JsonResponse({'status': 'failure', 'message': 'Payment not found'}, status=404)

        except Exception as e:
            return JsonResponse({'status': 'failure', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'invalid method'}, status=405)

@login_required
def proceed_with_order(request, order_id):
    # Check if user has any saved addresses
    has_address = Address.objects.filter(user=request.user).exists()
    if not has_address:
        return redirect('manage_addresses')

    # Check if an address is already selected
    selected_address_id = request.session.get('selected_address_id')
    if not selected_address_id:
        return redirect('manage_addresses')

    # Address selected → continue to payment or summary
    return redirect('order:create_payment_order', order_id=order_id)


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import ORDER_STATUS_CHOICES


@login_required
def update_status(request, item_id):
    if request.method == 'POST':
        item = get_object_or_404(OrderItem, id=item_id, seller=request.user)
        new_status = request.POST.get('status')
        if new_status in dict(ORDER_STATUS_CHOICES):
            item.status = new_status
            if new_status == 'Delivered':
                item.expected_delivery_date = timezone.now().date()
            item.save()
    return redirect('order:seller_orders_view')


from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from order.models import OrderItem
from django.utils import timezone
from django.contrib import messages

@login_required
def update_orderitem_status(request, item_id):
    item = get_object_or_404(OrderItem, pk=item_id, seller=request.user)

    if request.method == "POST":
        new_status = request.POST.get("status")
        item.status = new_status
        item.save()

        # ✅ Email Buyer
        send_mail(
            subject=f"📦 Order #{item.order.id} - Status Update",
            message=f"Hi {item.order.buyer.username},\n\nThe status of your item '{item.product.product_name}' has been updated to **{new_status}**.\n\nTracking: {item.tracking_number or 'Not available'}\n\nThank you for shopping with us!",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[item.order.buyer.email],
            fail_silently=False
        )

        messages.success(request, "Order item status updated and customer notified.")
        return redirect('order:seller_orders_view')
