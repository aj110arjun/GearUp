from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .models import Cart, CartItem, Wishlist, WishlistItem
from common.products.models import Product, ProductVariant
import json

# Helper functions
# Update this helper function in cart_wishlist/views.py
def get_or_create_cart(user):
    """Get active cart or create a new one"""
    try:
        # First, try to get an active cart
        cart = Cart.objects.get(user=user, is_active=True)
        return cart
    except Cart.DoesNotExist:
        # If no active cart exists, check for any cart
        cart = Cart.objects.filter(user=user).first()
        if cart:
            # Reactivate existing cart
            cart.is_active = True
            cart.save()
            return cart
        else:
            # Create new cart with is_active=True
            cart = Cart.objects.create(user=user, is_active=True)
            return cart
    except Cart.MultipleObjectsReturned:
        # Handle multiple active carts (shouldn't happen, but just in case)
        carts = Cart.objects.filter(user=user, is_active=True)
        # Deactivate all except the first one
        for cart in carts[1:]:
            cart.is_active = False
            cart.save()
        return carts.first()

def get_or_create_wishlist(user):
    wishlist, created = Wishlist.objects.get_or_create(user=user)
    return wishlist

# Cart Views
@login_required
def cart_view(request):
    cart = get_or_create_cart(request.user)
    cart_items = cart.items.select_related('variant__product').all()
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
    }
    return render(request, 'user/cart/cart_view.html', context)

@require_POST
@login_required
def add_to_cart(request):
    try:
        data = json.loads(request.body)
        variant_id = data.get('variant_id')
        quantity = int(data.get('quantity', 1))
        
        variant = get_object_or_404(ProductVariant, id=variant_id, is_active=True)
        
        if variant.stock_quantity < quantity:
            return JsonResponse({
                'success': False,
                'message': f'Only {variant.stock_quantity} items available in stock'
            })
        
        cart = get_or_create_cart(request.user)
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            variant=variant,
            defaults={'quantity': quantity}
        )
        
        if not created:
            cart_item.quantity += quantity
            if cart_item.quantity > variant.stock_quantity:
                cart_item.quantity = variant.stock_quantity
            cart_item.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Product added to cart successfully',
            'cart_count': cart.total_items
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'Error adding product to cart'
        })

@require_POST
@login_required
def update_cart_item(request, item_id):
    try:
        data = json.loads(request.body)
        quantity = int(data.get('quantity', 1))
        
        cart_item = get_object_or_404(
            CartItem, 
            id=item_id, 
            cart__user=request.user
        )
        
        if quantity <= 0:
            cart_item.delete()
            message = 'Item removed from cart'
        else:
            if quantity > cart_item.variant.stock_quantity:
                return JsonResponse({
                    'success': False,
                    'message': f'Only {cart_item.variant.stock_quantity} items available'
                })
            cart_item.quantity = quantity
            cart_item.save()
            message = 'Cart updated successfully'
        
        cart = get_or_create_cart(request.user)
        return JsonResponse({
            'success': True,
            'message': message,
            'cart_count': cart.total_items,
            'subtotal': cart.subtotal,
            'total_discount': cart.total_discount,
            'final_total': cart.final_total,
            'item_total': cart_item.total_price if quantity > 0 else 0
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'Error updating cart'
        })

@require_POST
@login_required
def remove_from_cart(request, item_id):
    try:
        cart_item = get_object_or_404(
            CartItem, 
            id=item_id, 
            cart__user=request.user
        )
        cart_item.delete()
        
        cart = get_or_create_cart(request.user)
        return JsonResponse({
            'success': True,
            'message': 'Item removed from cart',
            'cart_count': cart.total_items,
            'subtotal': cart.subtotal,
            'total_discount': cart.total_discount,
            'final_total': cart.final_total
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'Error removing item from cart'
        })

@login_required
def clear_cart(request):
    cart = get_or_create_cart(request.user)
    cart.items.all().delete()
    messages.success(request, 'Cart cleared successfully')
    return redirect('shop:cart')

# Wishlist Views
@login_required
def wishlist_view(request):
    wishlist = get_or_create_wishlist(request.user)
    wishlist_items = wishlist.items.select_related('product').all()
    
    context = {
        'wishlist': wishlist,
        'wishlist_items': wishlist_items,
    }
    return render(request, 'user/wishlist/wishlist_view.html', context)

@login_required
def add_to_wishlist(request, product_id):
    try:
        product = get_object_or_404(Product, id=product_id, is_active=True)
        wishlist = get_or_create_wishlist(request.user)
        
        wishlist_item, created = WishlistItem.objects.get_or_create(
            wishlist=wishlist,
            product=product
        )
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Product added to wishlist',
                'wishlist_count': wishlist.total_items
            })
        else:
            messages.success(request, 'Product added to wishlist')
            return redirect(request.META.get('HTTP_REFERER', 'products:home'))
            
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': 'Error adding product to wishlist'
            })
        else:
            messages.error(request, 'Error adding product to wishlist')
            return redirect(request.META.get('HTTP_REFERER', 'products:home'))

@login_required
def remove_from_wishlist(request, item_id):
    try:
        wishlist_item = get_object_or_404(
            WishlistItem, 
            id=item_id, 
            wishlist__user=request.user
        )
        wishlist_item.delete()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            wishlist = get_or_create_wishlist(request.user)
            return JsonResponse({
                'success': True,
                'message': 'Product removed from wishlist',
                'wishlist_count': wishlist.total_items
            })
        else:
            messages.success(request, 'Product removed from wishlist')
            return redirect('shop:wishlist')
            
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': 'Error removing product from wishlist'
            })
        else:
            messages.error(request, 'Error removing product from wishlist')
            return redirect('shop:wishlist')

@login_required
def move_to_cart(request, item_id):
    try:
        wishlist_item = get_object_or_404(
            WishlistItem, 
            id=item_id, 
            wishlist__user=request.user
        )
        
        # Get the first available variant
        variant = wishlist_item.product.variants.filter(is_active=True, stock_quantity__gt=0).first()
        
        if variant:
            cart = get_or_create_cart(request.user)
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                variant=variant,
                defaults={'quantity': 1}
            )
            
            if not created:
                cart_item.quantity += 1
                cart_item.save()
            
            # Remove from wishlist
            wishlist_item.delete()
            
            messages.success(request, 'Product moved to cart successfully')
        else:
            messages.error(request, 'Product is out of stock')
            
        return redirect('shop:wishlist')
        
    except Exception as e:
        messages.error(request, 'Error moving product to cart')
        return redirect('shop:wishlist')

# AJAX Views
@login_required
def ajax_cart_count(request):
    cart = get_or_create_cart(request.user)
    return JsonResponse({'count': cart.total_items})

@login_required
def ajax_wishlist_count(request):
    wishlist = get_or_create_wishlist(request.user)
    return JsonResponse({'count': wishlist.total_items})