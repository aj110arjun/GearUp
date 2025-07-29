from django.shortcuts import render, redirect, get_object_or_404
from .models import Cart, CartItem
from products.models import Product


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

    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    return redirect('view_cart')

def remove_from_cart(request, item_id):
    CartItem.objects.filter(id=item_id).delete()
    return redirect('view_cart')

