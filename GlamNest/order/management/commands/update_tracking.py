
# orders/management/commands/update_tracking.py

from django.core.management.base import BaseCommand
from order.models import OrderItem
from order.utils import update_order_item_status

class Command(BaseCommand):
    help = 'Update order item shipping status from TrackingMore'

    def handle(self, *args, **kwargs):
        shipped_items = OrderItem.objects.filter(status='Shipped').exclude(tracking_number__isnull=True)
        for item in shipped_items:
            update_order_item_status(item)
            self.stdout.write(f"Updated status for order item {item.id}")
