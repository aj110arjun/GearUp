from django import template
from ..models import WishlistItem, CartItem

register = template.Library()

@register.filter
def is_in_wishlist(product, user):
    """Check if product is in user's wishlist"""
    if not user.is_authenticated:
        return False
    return WishlistItem.objects.filter(
        wishlist__user=user,
        product=product
    ).exists()

@register.filter
def is_in_cart(product, user):
    """Check if any variant of product is in user's cart"""
    if not user.is_authenticated:
        return False
    return CartItem.objects.filter(
        cart__user=user,
        variant__product=product
    ).exists()

@register.filter
def get_cart_quantity(product, user):
    """Get total quantity of product in cart (across all variants)"""
    if not user.is_authenticated:
        return 0
    cart_items = CartItem.objects.filter(
        cart__user=user,
        variant__product=product
    )
    return sum(item.quantity for item in cart_items)