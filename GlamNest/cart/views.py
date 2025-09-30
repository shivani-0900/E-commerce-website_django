from django.shortcuts import render
from django.shortcuts import render,redirect
from order.models import Order,OrderItem
from User.models import ProductApproval
from .models import cart
from address.models import Address
from django.db.models import Sum
import json
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt  # or use csrf token from JS as above
from django.contrib.auth.decorators import login_required
from coupen.models  import Coupon
from django.shortcuts import render, redirect
from decimal import Decimal
from django.utils import timezone

from django.db.models import Count
from User.models import ProductApproval
# from order.models import OrderItem  # adjust if in another app

from django.utils import timezone
# Create your views here.
#add to cart
# Add to cart view
from django.contrib import messages
from django.shortcuts import get_object_or_404
from User.models import ProductApproval
from .models import cart as CartModel

from django.contrib import messages

from django.http import JsonResponse

from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from .models import cart  # Import the corrected Cart model
from django.urls import reverse
@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(ProductApproval, id=product_id)

    if request.user.is_authenticated:
        try:
            user_profile = User_Table.objects.get(id=request.user.id)
        except User_Table.DoesNotExist:
            messages.error(request, "User profile not found.")
            return redirect('home')

        cart_item, created = cart.objects.get_or_create(user=user_profile, product=product)
        if not created:
            cart_item.quantity += 1
        else:
            cart_item.quantity = 1  # Just in case default isn't set
        cart_item.save()

    else:
        cart_session = request.session.get('cart', {})
        pid = str(product_id)
        cart_session[pid] = cart_session.get(pid, 0) + 1
        request.session['cart'] = cart_session
        request.session.modified = True  # ensures session is saved

    messages.success(request, f"{product.product_name} added to cart!")
    return redirect('view_cart')
@login_required
def get_cart_count(request):
    total_quantity = cart.objects.filter(user=request.user).aggregate(total=Sum('quantity'))['total'] or 0
    return JsonResponse({'count': total_quantity})


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from .models import cart
from User.models import User_Table
from decimal import Decimal



def view_cart(request):
    cart_items = []
    cart_total = Decimal('0.00')
    cart_count = 0
    discount = Decimal('0.00')
    shipping = Decimal('0.00')
    applied_coupon = None
    available_coupons = []
    grand_total = Decimal('0.00')
    order = None
    order_id = None

    user_profile = None
    if request.user.is_authenticated:
        try:
            user_profile = User_Table.objects.get(id=request.user.id)
        except User_Table.DoesNotExist:
            pass

        if user_profile:
            user_cart = cart.objects.filter(user=user_profile)
            for entry in user_cart:
                subtotal = entry.product.price * entry.quantity
                cart_items.append({
                    'id': entry.id,
                    'product': entry.product,
                    'quantity': entry.quantity,
                    'subtotal': subtotal
                })

    else:
        session_cart = request.session.get('cart', {})
        product_ids = session_cart.keys()
        products = ProductApproval.objects.filter(id__in=product_ids)
        for product in products:
            quantity = session_cart.get(str(product.id), 1)
            subtotal = product.price * quantity
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'subtotal': subtotal
            })

    # Calculate total and shipping
    cart_total = sum(item['subtotal'] for item in cart_items)
    cart_count = sum(item['quantity'] for item in cart_items)
    shipping = Decimal('0.00') if cart_total >= 500 else Decimal('50.00')

    # Coupons: only for authenticated users
    if request.user.is_authenticated and user_profile:
        available_coupons = [
            c for c in Coupon.objects.filter(active=True)
            if c.is_valid(user_profile, cart_total, cart_items)
        ]

        # Check for applied coupon
        coupon_code = request.session.get('applied_coupon')
        if coupon_code:
            try:
                applied_coupon = Coupon.objects.get(code=coupon_code.strip(), active=True)
                if applied_coupon.is_valid(user_profile, cart_total, cart_items):
                    discount = applied_coupon.discount_amount
                else:
                    request.session.pop('applied_coupon', None)
                    applied_coupon = None
            except Coupon.DoesNotExist:
                request.session.pop('applied_coupon', None)
                applied_coupon = None

        # Save or update order with discount
        order = Order.objects.filter(buyer=user_profile, status='Pending').first()

        if not order:
            order = Order.objects.create(
                buyer=user_profile,
                status='Pending',
                address=None,
                total_price=cart_total,
                discount_applied=discount,
                final_price=cart_total + shipping - discount,
                total_amount=cart_total + shipping - discount
            )
        else:
            order.total_price = cart_total
            order.discount_applied = discount
            order.final_price = cart_total + shipping - discount
            order.total_amount = cart_total + shipping - discount
            order.save()

        order_id = order.id

    # Ensure no negative grand_total
    grand_total = max(cart_total + shipping - discount, 0)

    return render(request, 'carts/view_cart.html', {
        'cart_items': cart_items,
        'cart_total': cart_total,
        'cart_count': cart_count,
        'shipping': shipping,
        'discount': discount,
        'grand_total': grand_total,
        'available_coupons': available_coupons,
        'applied_coupon': applied_coupon,
        'order': order,
        'order_id': order_id,
    })

@require_POST
def update_cart_quantity(request):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'User not authenticated.'}, status=401)

    data = json.loads(request.body)
    item_id = data.get('item_id')
    quantity = data.get('quantity')

    try:
        cart_item = cart.objects.get(id=item_id, user=request.user)
        cart_item.quantity = quantity
        cart_item.save()
    except cart.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Cart item not found.'}, status=404)

    cart_items = cart.objects.filter(user=request.user)
    cart_total = sum(item.product.price * item.quantity for item in cart_items)
    cart_count = sum(item.quantity for item in cart_items)

    discount = 0.0
    shipping = 0.0 if cart_total > 500 else 50.0
    try:
        if 'applied_coupon' in request.session:
            coupon = Coupon.objects.get(code=request.session['applied_coupon'])
            if coupon.is_valid(request.user, cart_total, cart_items):
                discount = float(coupon.discount_amount)
            else:
                request.session.pop('applied_coupon', None)
    except Coupon.DoesNotExist:
        request.session.pop('applied_coupon', None)

    final_total = float(cart_total + shipping - discount)

    return JsonResponse({
        'success': True,
        'cart_total': float(cart_total),
        'cart_count': cart_count,
        'shipping': shipping,
        'discount': discount,
        'final_total': final_total,
    })

from django.shortcuts import redirect
from django.urls import reverse
from decimal import Decimal
from .models import cart
from order.models import Order,OrderItem
@login_required
def proceed_to_checkout(request):
    user_profile = User_Table.objects.get(id=request.user.id)
    cart_items = cart.objects.filter(user=user_profile)

    if not cart_items:
        return redirect('view_cart')

    # Calculate totals
    cart_total = sum(item.product.price * item.quantity for item in cart_items)
    shipping = Decimal('50.00') if cart_total <= 500 else Decimal('0.00')
    discount = Decimal('0.00')  # Update this if applying coupons later
    grand_total = cart_total + shipping - discount

    # Check if a pending order already exists
    order = Order.objects.filter(buyer=user_profile, status='Pending').first()

    if not order:
        order = Order.objects.create(
            buyer=user_profile,
            total_price=cart_total,
            discount_applied=discount,
            final_price=grand_total,
            status='Pending'
        )

        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                seller=item.product.seller,
                quantity=item.quantity,
                price=item.product.price,
                status='Pending'
            )

    return redirect(f"{reverse('manage_addresses')}?order_id={order.id}")



from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from .models import cart  # Make sure your model is named `cart` or `Cart`

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from cart.models import cart  # Use your actual model name
from django.conf import settings
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import cart
from User.models import ProductApproval  # Update with actual model path


@require_POST
def remove_from_cart(request, product_id):
    product_id_str = str(product_id)

    if request.user.is_authenticated:
        try:
            cart_item = get_object_or_404(cart, user=request.user, product_id=product_id)
            cart_item.delete()
            messages.success(request, "Item removed from your cart.")
        except Exception:
            messages.error(request, "Could not remove item from cart.")
    else:
        session_cart = request.session.get('cart', {})
        if product_id_str in session_cart:
            del session_cart[product_id_str]
            request.session['cart'] = session_cart
            messages.success(request, "Item removed from your cart.")
        else:
            messages.warning(request, "Item not found in your cart.")

    return redirect('view_cart')



def get_best_sellers(limit=5):
    return (
        ProductApproval.objects.filter(status='approved')
        .annotate(order_count=Count('orderitem'))
        .order_by('-order_count')[:limit]
    )
    
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Wishlist


@login_required
def get_wishlist_count(request):
    count = Wishlist.objects.filter(user=request.user).count()
    return JsonResponse({'wishlist_count': count})
def cart_count(request):
    if request.user.is_authenticated:
        count = cart.objects.filter(user=request.user).count()
    else:
        session_cart = request.session.get('cart', {})
        count = sum(session_cart.values())
    return JsonResponse({'count': count})


def wishlist_count(request):
    if request.user.is_authenticated:
        count = Wishlist.objects.filter(user=request.user).count()
    else:
        wishlist = request.session.get('wishlist', [])
        count = len(wishlist)
    return JsonResponse({'count': count})
