from cart.models import cart

def cart_count(request):
    if request.user.is_authenticated:
        count = cart.objects.filter(user=request.user).count()
    else:
        session_cart = request.session.get('cart', {})
        count = sum(session_cart.values())
    return {'cart_count': count}  # ✅ NOT JsonResponse
