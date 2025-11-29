from common.user.cart_wishlist.models import Cart


def get_or_create_active_cart(user):
    """Get active cart for user or create a new one"""
    # First try to find an active cart
    cart = Cart.objects.filter(user=user, is_active=True).first()
    
    if cart:
        return cart
    
    # If no active cart, find any existing cart and activate it
    cart = Cart.objects.filter(user=user).first()
    if cart:
        cart.is_active = True
        cart.save()
        return cart
    
    # If no cart exists at all, create a new one
    cart = Cart.objects.create(
        user=user,
        is_active=True,
        total_price=0,
        total_discount=0
    )
    return cart