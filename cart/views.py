from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST


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


@login_required
def view_cart(request):
    cart = get_cart(request)

    # Prepare cart data without variant stock
    cart_items_data = []
    for item in cart.items.all():
        cart_items_data.append({
            "item": item,
            "sizes": [],   # Not using variants anymore
            "colors": [],  # Not using variants anymore
        })

    context = {
        "cart": cart,
        "cart_items_data": cart_items_data,
    }
    return render(request, "registration/cart.html", context)


def add_to_cart(request, product_id):
    product = get_object_or_404(Product, product_id=product_id)
    cart = get_cart(request)

    size = request.POST.get('size')
    color = request.POST.get('color')
    quantity = int(request.POST.get('quantity', 1))

    # Find the correct variant
    variant = None
    if size and color:
        variant = Variant.objects.filter(product=product, size=size, color=color).first()
        if not variant:
            messages.error(request, "Selected variant is not available.")
            return redirect('product_detail', slug=product.slug)
    elif product.variants.count() == 1:
        # Auto-select single variant
        variant = product.variants.first()

    # Get or create cart item
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        variant=variant
    )

    # Stock check
    stock = product.stock if product else product.total_stock
    if stock <= 0:
        messages.error(request, "This product is out of stock.")
        return redirect('product_detail', slug=product.slug)

    # Quantity limit
    if quantity > 6:
        quantity = 6
        messages.warning(request, "You can only add up to 6 units of this product.")

    if quantity > stock:
        quantity = stock
        messages.warning(request, "Only limited stock available.")

    cart_item.quantity = quantity
    cart_item.save()

    # Remove from wishlist if exists
    if request.user.is_authenticated:
        WishlistItem.objects.filter(
            wishlist__user=request.user,
            product=product
        ).delete()

    messages.success(request, f"{product.name} added to cart successfully!")
    return redirect('view_cart')




def remove_from_cart(request, item_id):
    CartItem.objects.filter(id=item_id).delete()
    return redirect('view_cart')

@require_POST
def increment_quantity(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)

    # Per-user limit 5
    if item.quantity >= 5:
        messages.error(request, "Maximum 5 items per product allowed.")
    else:
        item.quantity += 1
        item.save()

    return redirect('view_cart')

@require_POST
def decrement_quantity(request, item_id):
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
        size = request.POST.get("size")
        color = request.POST.get("color")

        item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)

        # Check if both values are provided
        if not size or not color:
            messages.error(request, "Please select both size and color.")
            return redirect('view_cart')

        # Find variant matching size & color for the product
        try:
            variant = Variant.objects.get(product=item.product, size=size, color=color)
        except Variant.DoesNotExist:
            messages.error(request, "Selected variant does not exist.")
            return redirect('view_cart')

        # Update the cart item
        item.variant = variant
        item.save()
        messages.success(request, "Variant updated successfully!")

    return redirect('view_cart')

