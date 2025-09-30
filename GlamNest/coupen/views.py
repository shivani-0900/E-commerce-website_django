from django.shortcuts import render,redirect
from django.contrib import messages
from coupen.models import Coupon
from cart.models import cart
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Coupon
from django.utils.dateparse import parse_datetime
from datetime import datetime
from decimal import Decimal
from decimal import Decimal, InvalidOperation
from .models import Coupon, NewsletterSubscriber
from django.contrib import messages
from django.core.mail import send_mail
from django.utils.timezone import make_aware
from django.urls import reverse


@require_POST
def apply_coupon(request):
    if not request.user.is_authenticated:
        login_url = reverse('User:user_login')
        messages.error(
            request,
            f'⚠️ Please <a href="{login_url}">login</a> to apply a coupon.',
            extra_tags='safe'
        )
        return redirect(request.META.get('HTTP_REFERER', 'view_cart'))

    code = request.POST.get('coupon_code', '').strip().upper()
    referer = request.META.get('HTTP_REFERER', '')

    if not code:
        messages.error(request, "No coupon code provided.")
        return redirect('view_cart')

    now = timezone.now()
    coupon = Coupon.objects.filter(code=code).first()
    cart_items = cart.objects.filter(user=request.user)
    cart_total = sum(item.product.price * item.quantity for item in cart_items)

    if not cart_items:
        messages.error(request, "Your cart is empty.")
        return redirect('view_cart')

    if not coupon:
        messages.error(request, "❌ Invalid coupon code.")
        return redirect('available_offers' if 'offers' in referer else 'view_cart')

    # ✅ Check if coupon is currently active
    if not (coupon.active and coupon.valid_from <= now <= coupon.valid_to):
        messages.error(request, f"❌ '{coupon.code}' is not active right now.")
        return redirect('available_offers' if 'offers' in referer else 'view_cart')

    # ✅ Check custom eligibility logic
    if coupon.is_valid(request.user, cart_total, cart_items):
        request.session['applied_coupon'] = coupon.code
        messages.success(request, f"🎉 Coupon '{coupon.code}' applied successfully!")
    else:
        messages.error(request, "❌ You are not eligible for this offer.")

    return redirect('available_offers' if 'offers' in referer else 'view_cart')

@require_POST
def remove_coupon(request):
    if 'applied_coupon' in request.session:
        del request.session['applied_coupon']
        messages.success(request, "✅ Coupon removed.")
    return redirect('view_cart')

def manage_coupons(request):
    if not request.user.is_authenticated or request.user.usertype != 'Seller':
        messages.error(request, "You do not have permission to access this page.")
        return redirect('User:seller_home')

    if request.method == 'POST':
        try:
            code = request.POST['code'].strip().upper()
            title = request.POST['title']
            description = request.POST['description']
            discount_amount = Decimal(request.POST['discount_amount'])
            valid_from = make_aware(datetime.strptime(request.POST['valid_from'], '%Y-%m-%dT%H:%M'))
            valid_to = make_aware(datetime.strptime(request.POST['valid_to'], '%Y-%m-%dT%H:%M'))
            min_order_value = Decimal(request.POST.get('min_order_value') or '0')
            first_time_only = request.POST.get('first_time_only') == 'on'
            applicable_brand = request.POST.get('applicable_brand') or None
            active = request.POST.get('active') == 'on'

            coupon = Coupon.objects.create(
                code=code,
                title=title,
                description=description,
                discount_amount=discount_amount,
                valid_from=valid_from,
                valid_to=valid_to,
                min_order_value=min_order_value,
                first_time_only=first_time_only,
                applicable_brand=applicable_brand,
                active=active,
            )

            # ✉️ Send email to all subscribers
            subscribers = NewsletterSubscriber.objects.all()
            if subscribers:
                subject = f"🎉 New Coupon: {coupon.code} — Save ₹{coupon.discount_amount} at Glamnest!"
                html_message = f"""
                    <h3>Hi there,</h3>
                    <p>We’ve got something special for you 💖</p>
                    <p><strong>Use coupon <code>{coupon.code}</code> to get ₹{coupon.discount_amount} off your next order!</strong></p>
                    <ul>
                      <li>🛍️ <strong>Title:</strong> {coupon.title}</li>
                      <li>📝 <strong>Description:</strong> {coupon.description}</li>
                      <li>📅 <strong>Valid from:</strong> {coupon.valid_from.strftime('%d %b %Y, %I:%M %p')}</li>
                      <li>📅 <strong>Valid until:</strong> {coupon.valid_to.strftime('%d %b %Y, %I:%M %p')}</li>
                    </ul>
                    <p>Happy Shopping!<br>– The Glamnest Team</p>
                """

                send_mail(
                    subject=subject,
                    message='',
                    from_email='noreply@glamnest.com',
                    recipient_list=[sub.email for sub in subscribers],
                    html_message=html_message,
                    fail_silently=False,
                )

            messages.success(request, f"✅ Coupon '{coupon.code}' added and newsletter sent.")

        except (KeyError, ValueError, InvalidOperation) as e:
            messages.error(request, f"❌ Error creating coupon: {str(e)}")

        return redirect('manage_coupons')

    coupons = Coupon.objects.all().order_by('-valid_from')
    return render(request, 'seller/manage_coupons.html', {'coupons': coupons})


def delete_coupon(request, coupon_id):
    if not request.user.is_authenticated or request.user.usertype != 'Seller':
        messages.error(request, "You do not have permission to delete coupons.")
        return redirect('home')

    coupon = get_object_or_404(Coupon, id=coupon_id)
    coupon.delete()
    messages.success(request, f"🗑️ Coupon '{coupon.code}' deleted.")
    return redirect('manage_coupons')


def subscribe_newsletter(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if email and not NewsletterSubscriber.objects.filter(email=email).exists():
            NewsletterSubscriber.objects.create(email=email)
            messages.success(request, "You've successfully subscribed!")
        else:
            messages.error(request, "You're already subscribed or the email is invalid.")
        return redirect('User:user_home')  # Replace 'home' with your homepage's URL name
from django.utils import timezone
from .models import Coupon

def available_offers(request):
    now = timezone.now()
    
    # Fetch all coupons to display them with status badges
    offers = Coupon.objects.all().order_by('-valid_from')
    
    return render(request, 'buyer/offers.html', {
        'offers': offers,
        'now': now
    })
