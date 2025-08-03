from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Cart, CartItem
from products.models import Product, Variant
from wishlist.models import Wishlist, WishlistItem



def get_cart(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
        cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
    return cart

def view_cart(request):
	cart = get_cart(request)
	context={
	'cart': cart,
	}
	return render(request, 'registration/cart.html', context)


def add_to_cart(request, product_id):
    product = get_object_or_404(Product, product_id=product_id)
    cart = get_cart(request)

    variant_id = request.POST.get('variant_id')
    variant = get_object_or_404(Variant, id=variant_id)

    desired_quantity = int(request.POST.get('quantity', 1))

    # Remove from wishlist if present
    try:
        wishlist = Wishlist.objects.get(user=request.user)
        WishlistItem.objects.filter(wishlist=wishlist, product=product).delete()
    except Wishlist.DoesNotExist:
        pass

    # Check stock from variant instead of product
    stock = variant.stock
    if stock == 0:
        messages.error(request, "This variant is out of stock.")
        return redirect('product_detail', slug=product.slug)

    # Enforce maximum allowed quantity
    if desired_quantity > 6:
        messages.warning(request, "You can only add up to 6 units of this product.")
        desired_quantity = 6

    # Don't allow more than available stock
    if desired_quantity > stock:
        desired_quantity = stock
        messages.warning(request, "Only limited stock available for this variant.")

    # ✅ Include variant in get_or_create
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        variant=variant,  # ✅ Important
        defaults={'quantity': 0}  # start from 0, we'll add quantity below
    )

    cart_item.quantity = desired_quantity
    cart_item.save()

    return redirect('view_cart')

def remove_from_cart(request, item_id):
    CartItem.objects.filter(id=item_id).delete()
    return redirect('view_cart')

def increment_quantity(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    
    if item.quantity < item.product.stock:
        item.quantity += 1
        item.save()
    else:
        messages.error(request, "Maximum stock limit reached.")

    return redirect('view_cart')

def decrement_quantity(request, item_id):
    if request.method == 'POST':
        item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        if item.quantity > 1:
            item.quantity -= 1
            item.save()
        else:
            item.delete()
    return redirect('view_cart')

@login_required
def update_cart_variant(request, item_id):
    if request.method == "POST":
        variant_id = request.POST.get("variant_id")
        item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)

        if variant_id:
            item.variant = get_object_or_404(Variant, id=variant_id)
        else:
            item.variant = None
        item.save()

    return redirect('view_cart')

