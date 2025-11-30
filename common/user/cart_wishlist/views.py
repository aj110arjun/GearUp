from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .models import Cart, CartItem, Wishlist, WishlistItem
from common.products.models import Product, ProductVariant
import json

# Helper functions
def get_or_create_cart(user):
    cart, created = Cart.objects.get_or_create(user=user)
    return cart

def get_or_create_wishlist(user):
    wishlist, created = Wishlist.objects.get_or_create(user=user)
    return wishlist

def is_product_in_cart(user, product):
    """Check if any variant of a product is in user's cart"""
    return CartItem.objects.filter(
        cart__user=user,
        variant__product=product
    ).exists()

def is_product_in_wishlist(user, product):
    """Check if product is in user's wishlist"""
    return WishlistItem.objects.filter(
        wishlist__user=user,
        product=product
    ).exists()

def get_cart_item_for_product(user, product):
    """Get cart item for any variant of a product"""
    return CartItem.objects.filter(
        cart__user=user,
        variant__product=product
    ).first()

# Cart Views
@login_required
def cart_view(request):
    cart = get_or_create_cart(request.user)
    cart_items = cart.items.select_related('variant__product').all()
    
    # Check which products are in wishlist
    wishlist_product_ids = WishlistItem.objects.filter(
        wishlist__user=request.user
    ).values_list('product_id', flat=True)
    
    # Add wishlist status to each cart item
    for item in cart_items:
        item.in_wishlist = item.variant.product.id in wishlist_product_ids
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
    }
    return render(request, 'user/cart/cart_view.html', context)

@login_required
def add_to_cart(request, variant_id):
    from common.user.cart_wishlist.utils import get_or_create_active_cart
    
    variant = get_object_or_404(ProductVariant, id=variant_id)
    product = variant.product
    
    # Check if product is already in wishlist
    if is_product_in_wishlist(request.user, product):
        # Remove from wishlist first
        WishlistItem.objects.filter(
            wishlist__user=request.user,
            product=product
        ).delete()
        messages.info(request, f'{product.name} was moved from wishlist to cart.')
    
    # Get or create active cart
    cart = get_or_create_active_cart(request.user)
    
    # Check if item already exists in cart
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        variant=variant,
        defaults={'quantity': 1}
    )
    
    if not created:
        cart_item.quantity += 1
        cart_item.save()
        messages.success(request, f'Updated quantity for {product.name} in cart.')
    else:
        messages.success(request, f'Added {product.name} to cart.')
    
    return redirect('shop:cart')

@require_POST
@login_required
def ajax_add_to_cart(request):
    """AJAX endpoint for adding items to cart from wishlist"""
    try:
        data = json.loads(request.body)
        variant_id = data.get('variant_id')
        
        if not variant_id:
            return JsonResponse({
                'success': False,
                'message': 'Variant ID is required'
            })
        
        variant = get_object_or_404(ProductVariant, id=variant_id)
        product = variant.product
        
        # Check if product is already in wishlist
        if is_product_in_wishlist(request.user, product):
            # Remove from wishlist first
            WishlistItem.objects.filter(
                wishlist__user=request.user,
                product=product
            ).delete()
        
        # Get or create active cart
        from common.user.cart_wishlist.utils import get_or_create_active_cart
        cart = get_or_create_active_cart(request.user)
        
        # Check if item already exists in cart
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            variant=variant,
            defaults={'quantity': 1}
        )
        
        if not created:
            cart_item.quantity += 1
            cart_item.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Product added to cart successfully',
            'cart_count': cart.total_items
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error adding to cart: {str(e)}'
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
        product = cart_item.variant.product
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
    
    # Check which products are already in cart
    cart_product_ids = CartItem.objects.filter(
        cart__user=request.user
    ).values_list('variant__product_id', flat=True)
    
    for item in wishlist_items:
        item.in_cart = item.product.id in cart_product_ids
    
    context = {
        'wishlist': wishlist,
        'wishlist_items': wishlist_items,
    }
    return render(request, 'user/wishlist/wishlist_view.html', context)

@login_required
def add_to_wishlist(request, product_id):
    try:
        product = get_object_or_404(Product, id=product_id, is_active=True)
        
        # Check if product is already in cart
        if is_product_in_cart(request.user, product):
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'This product is already in your cart. Remove it from cart first to add to wishlist.'
                })
            else:
                messages.error(request, 'This product is already in your cart. Remove it from cart first to add to wishlist.')
                return redirect(request.META.get('HTTP_REFERER', 'products:home'))
        
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
        product = wishlist_item.product
        
        # Get the first available variant
        variant = product.variants.filter(is_active=True, stock_quantity__gt=0).first()
        
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

# Debug view
@login_required
def debug_cart_items(request):
    """Debug view to check cart item relationships"""
    cart = Cart.objects.filter(user=request.user, is_active=True).first()
    if not cart:
        return HttpResponse("No active cart")
    
    cart_items = cart.items.select_related('variant__product').all()
    results = []
    
    for item in cart_items:
        result = {
            'cart_item_id': item.id,
            'variant_id': item.variant_id,
            'variant_exists': bool(item.variant),
            'variant_str': str(item.variant) if item.variant else 'None',
            'product_exists': bool(item.variant.product) if item.variant else False,
            'product_id': item.variant.product.id if item.variant and item.variant.product else 'None',
            'product_name': item.variant.product.name if item.variant and item.variant.product else 'None',
        }
        results.append(result)
    
    return JsonResponse({'results': results})