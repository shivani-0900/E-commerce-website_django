# orders/utils.py

from datetime import timedelta
from django.utils import timezone

def get_expected_delivery_date(pincode):
    return timezone.now().date() + timedelta(days=5)


# from orders.utils import get_expected_delivery_date
from django.core.management.base import BaseCommand
from .models import OrderItem
import requests

def update_order_item_status(order_item):
    tracking_number = order_item.tracking_number
    carrier_code = order_item.shipping_company.lower() or 'dhl'

    headers = {
        "Tracking-Api-Key": "YOUR_TRACKINGMORE_API_KEY",
        "Content-Type": "application/json"
    }

    url = f"https://api.trackingmore.com/v4/trackings/{carrier_code}/{tracking_number}"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        tracking_status = data.get('data', {}).get('status', '').lower()

        # Mapping external status to internal choices
        if 'out for delivery' in tracking_status:
            order_item.status = 'Out for Delivery'
        elif 'delivered' in tracking_status:
            order_item.status = 'Delivered'
            order_item.expected_delivery_date = timezone.now().date()
        elif 'returned' in tracking_status or 'return' in tracking_status:
            order_item.status = 'Returned'

        order_item.save()
