from django.shortcuts import render, redirect, get_object_or_404
from .models import Cart, CartItem
from products.models import Product
from django.contrib import messages



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
    cart = get_cart(request)  # however you get the cart

    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

    # Optional: get desired quantity from form
    desired_quantity = int(request.POST.get('quantity', 1))

    if product.stock == 0:
        messages.error(request, "This product is out of stock.")
        return redirect('product_detail', slug=product.slug)
    if desired_quantity > product.stock:
        desired_quantity = product.stock

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

