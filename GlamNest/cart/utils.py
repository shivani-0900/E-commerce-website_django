from User.models import ProductApproval

def get_best_sellers_related_to_cart(cart_items, limit=5):
    """
    Returns best-selling related products based on product_type and category.
    Excludes products already in the cart.
    """
    if not cart_items:
        return ProductApproval.objects.filter(status='approved').order_by('-sold_quantity')[:limit]

    product_types = set()
    categories = set()
    excluded_ids = set()

    for item in cart_items:
        product = item.product if hasattr(item, 'product') else item
        product_types.add(product.product_type)
        categories.add(product.category)
        excluded_ids.add(product.id)

    related_products = ProductApproval.objects.filter(
        status='approved',
        product_type__in=product_types,
        category__in=categories
    ).exclude(id__in=excluded_ids).order_by('-sold_quantity')[:limit]

    return related_products
