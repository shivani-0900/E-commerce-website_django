from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.views.decorators.csrf import csrf_protect
from django.http import HttpResponseBadRequest
from address.models import Address
from order.models import Order
def manage_addresses(request):
    user = request.user
    order_id = request.GET.get('order_id') or request.POST.get('order_id')  # 👈 FIX HERE

    if request.method == 'POST':
        address_id = request.POST.get('address_id')
        full_name = request.POST.get('full_name')
        phone = request.POST.get('phone')
        address_line = request.POST.get('address_line')
        city = request.POST.get('city')
        state = request.POST.get('state')
        pincode = request.POST.get('pincode')
        is_default = request.POST.get('is_default') == 'on'

        if address_id:
            address = get_object_or_404(Address, id=address_id, user=user)
        else:
            address = Address(user=user)

        address.full_name = full_name
        address.phone = phone
        address.address_line = address_line
        address.city = city
        address.state = state
        address.pincode = pincode
        address.is_default = is_default
        address.save()

        if is_default:
            Address.objects.filter(user=user).exclude(id=address.id).update(is_default=False)

        # 🛠 Ensure redirect preserves order_id
        redirect_url = reverse('manage_addresses')
        if order_id:
            redirect_url += f'?order_id={order_id}'
        return redirect(redirect_url)

    # GET request
    addresses = Address.objects.filter(user=user)
    context = {
        'addresses': addresses,
        'order_id': order_id,
    }
    return render(request, 'address/add_address.html', context)

from django.contrib import messages

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.http import HttpResponseBadRequest
from address.models import Address
from order.models import OrderItem
from User.models import User_Table
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from User.models import User_Table
from address.models import Address
from order.models import Order  # adjust import as per your project
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponseBadRequest
from address.models import Address
from order.models import Order  # adjust import as needed
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

@require_POST
@login_required
def choose_shipping_address(request):
    if request.method == "POST":
        address_id = request.POST.get('address_id')
        order_id = request.POST.get('order_id')

        # ✅ Validate that both are provided and are digits
        if not address_id or not order_id or not address_id.isdigit() or not order_id.isdigit():
            return HttpResponseBadRequest("Invalid or missing address ID or order ID.")

        user_profile = request.user  # Assuming request.user is an instance of User_Table

        # Convert IDs to integers
        address_id = int(address_id)
        order_id = int(order_id)

        # ✅ Fetch and validate objects
        address = get_object_or_404(Address, id=address_id, user=user_profile)
        order = get_object_or_404(Order, id=order_id, buyer=user_profile)

        # Assign the address to the order
        order.address = address
        order.save()

        return redirect('order:create_payment_order', order_id=order.id)

    return redirect('manage_addresses')
@login_required
def delete_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    if request.method == 'POST':
        address.delete()
        messages.success(request, "Address deleted successfully.")
        return redirect('manage_addresses')
    return redirect('manage_addresses')


from django.http import JsonResponse

@login_required
def track_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, buyer=request.user)

    tracking_data = {
        "status": order.status,
        "estimated_delivery": order.estimated_delivery.strftime('%d %b %Y') if order.estimated_delivery else "Not Available",
        "placed_date": order.created_at.strftime('%d %b %Y'),
    }
    return JsonResponse(tracking_data)
