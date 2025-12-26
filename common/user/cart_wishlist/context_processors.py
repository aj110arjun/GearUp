from .models import Cart, Wishlist

def cart_wishlist_counts(request):
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            cart_count = cart.total_items
        except Cart.DoesNotExist:
            cart_count = 0
            
        try:
            wishlist = Wishlist.objects.get(user=request.user)
            wishlist_count = wishlist.total_items
        except Wishlist.DoesNotExist:
            wishlist_count = 0
            
        return {
            'cart_count': cart_count,
            'wishlist_count': wishlist_count
        }
    return {
        'cart_count': 0,
        'wishlist_count': 0
    }
