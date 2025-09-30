import requests

API_KEY = 'il0zw30h-f2ic-3kth-f104-48ow8wld12s3'
BASE_URL = 'https://api.trackingmore.com/v2/trackings/get'

HEADERS = {
    'Content-Type': 'application/json',
    'Trackingmore-Api-Key': API_KEY,
}

def get_tracking_info(carrier_code, tracking_number):
    """
    Get tracking info from TrackingMore for a given carrier and tracking number.
    
    carrier_code: string - carrier short code (like 'dhl', 'ups', 'fedex')
    tracking_number: string - shipment tracking number
    
    Returns JSON data or None on failure.
    """
    url = f'{BASE_URL}/{carrier_code}/{tracking_number}'

    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"TrackingMore API error: {response.status_code} {response.text}")
        return None
from order.models import OrderItem

def update_order_item_status(order_item):
    carrier_code = CARRIER_CODE_MAP.get(order_item.shipping_company)
    tracking_number = order_item.tracking_number
    
    if not carrier_code or not tracking_number:
        return  # No valid carrier or tracking number
    
    tracking_data = get_tracking_info(carrier_code, tracking_number)
    if tracking_data and tracking_data.get('data'):
        # Parse the tracking status from the response
        last_status = tracking_data['data']['origin_info']['trackinfo'][-1]['status']
        # last_status example: "Delivered", "In Transit", "Exception", etc.
        
        # Update order item status based on API info
        if 'delivered' in last_status.lower():
            order_item.status = 'Delivered'
        elif 'shipped' in last_status.lower() or 'in transit' in last_status.lower():
            order_item.status = 'Shipped'
        elif 'exception' in last_status.lower():
            order_item.status = 'Cancelled'  # Or some error status
        else:
            order_item.status = 'Pending'  # Default fallback
        
        order_item.save()
