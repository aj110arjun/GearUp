from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect

from .models import Wishlist, WishlistItem
from products.models import Product
from cart.models import Cart, CartItem

@login_required
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, product_id=product_id)
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    WishlistItem.objects.get_or_create(wishlist=wishlist, product=product)
    try:
        cart = Cart.objects.get(user=request.user)
        CartItem.objects.filter(cart=cart, product=product).delete()
    except Cart.DoesNotExist:
        pass
    return redirect('view_wishlist')

@login_required
def remove_from_wishlist(request, product_id):
    product = get_object_or_404(Product, product_id=product_id)
    wishlist = Wishlist.objects.get(user=request.user)
    WishlistItem.objects.filter(wishlist=wishlist, product=product).delete()
    return redirect('view_wishlist')

@login_required
def view_wishlist(request):
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    return render(request, 'registration/wishlist.html', {'wishlist': wishlist})

