from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Avg, Count
from .models import Cart, CartItem, Wishlist, WishlistItem
from common.products.models import Product, ProductVariant
from django.db import transaction
import json

# Helper functions
# Update this helper function in cart_wishlist/views.py
def get_or_create_cart(user):
    """Get active cart or create a new one"""
    try:
        cart = Cart.objects.get(user=user, is_active=True)
        return cart
    except Cart.DoesNotExist:
        cart = Cart.objects.filter(user=user).first()
        if cart:
            cart.is_active = True
            cart.save()
            return cart
        else:
            cart = Cart.objects.create(user=user, is_active=True)
            return cart
    except Cart.MultipleObjectsReturned:
        carts = Cart.objects.filter(user=user, is_active=True)
        for cart in carts[1:]:
            cart.is_active = False
            cart.save()
        return carts.first()

def get_or_create_wishlist(user):
    wishlist, created = Wishlist.objects.get_or_create(user=user)
    return wishlist

# Cart Views
@login_required
@transaction.atomic
def cart_view(request):
    """View to display shopping cart and automatically move out-of-stock items to wishlist"""
    cart = get_or_create_cart(request.user)
    
    cart_items = cart.items.select_related('variant__product').prefetch_related('variant__product__variants').all()
    out_of_stock_moved = 0
    
    # Check for out-of-stock items and move them to wishlist
    for item in list(cart_items):
        if item.variant.stock_quantity < 1 or item.variant.is_deleted:
            product = item.variant.product
            wishlist = get_or_create_wishlist(request.user)
            WishlistItem.objects.get_or_create(wishlist=wishlist, product=product)
            CartItem.objects.filter(cart=cart, variant__product=product).delete()
            out_of_stock_moved += 1
            
    if out_of_stock_moved > 0:
        messages.info(request, f'{out_of_stock_moved} item(s) were moved to your wishlist as they were unavailable or out of stock.')
        cart_items = cart.items.select_related('variant__product').prefetch_related('variant__product__variants').all()
        cart.refresh_from_db()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('ajax') == 'true':
        # Return JSON for AJAX requests
        return JsonResponse({
            'success': True,
            'cart_count': cart.total_items,
            'subtotal': float(cart.subtotal),
            'total_discount': float(cart.total_discount),
            'shipping_cost': float(cart.shipping_cost),
            'final_total': float(cart.final_total),
            'items_count': cart_items.count()
        })

    context = {
        'cart': cart,
        'cart_items': cart_items,
    }
    return render(request, 'user/cart/cart_view.html', context)

@login_required
def get_cart_data(request):
    """API endpoint to get current cart data"""
    cart = get_or_create_cart(request.user)
    cart_items = cart.items.all()
    
    return JsonResponse({
        'success': True,
        'cart_count': cart.total_items,
        'subtotal': float(cart.subtotal),
        'total_discount': float(cart.total_discount),
        'shipping_cost': float(cart.shipping_cost),
        'final_total': float(cart.final_total),
        'items_count': cart_items.count()
    })

@require_POST
@login_required
@transaction.atomic
def add_to_cart(request):
    try:
        data = json.loads(request.body)
        variant_id = data.get('variant_id')
        quantity = int(data.get('quantity', 1))
        
        # Get variant
        variant = get_object_or_404(ProductVariant, id=variant_id, is_active=True, is_deleted=False)
        product = variant.product
        
        # Check stock
        if variant.stock_quantity < 1:
            return JsonResponse({
                'success': False,
                'message': 'Product is out of stock'
            })
        
        # Get or create cart
        cart = get_or_create_cart(request.user)
        
        # Check if item already exists in cart
        existing_item = CartItem.objects.filter(cart=cart, variant=variant).first()
        removed = False
        added = False
        
        if existing_item:
            # If item exists, remove it (toggle functionality)
            existing_item.delete()
            removed = True
            message = 'Product removed from cart'
        else:
            # Add new item to cart
            CartItem.objects.create(
                cart=cart,
                variant=variant,
                quantity=min(quantity, variant.stock_quantity)
            )
            added = True
            message = 'Product added to cart successfully'
            
            # MUTUAL EXCLUSIVITY: Remove from wishlist if adding to cart
            wishlist = get_or_create_wishlist(request.user)
            WishlistItem.objects.filter(wishlist=wishlist, product=product).delete()
        
        # Refresh cart to get updated totals
        cart.refresh_from_db()
        wishlist = get_or_create_wishlist(request.user)
        
        return JsonResponse({
            'success': True,
            'added': added,
            'removed': removed,
            'message': message,
            'cart_count': cart.total_items,
            'wishlist_count': wishlist.total_items
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error processing request: {str(e)}'
        })
    
@require_POST
@login_required
@transaction.atomic
def toggle_cart_item(request):
    """Toggle cart item - add if not exists, remove if exists"""
    try:
        data = json.loads(request.body)
        variant_id = data.get('variant_id')
        
        variant = get_object_or_404(ProductVariant, id=variant_id, is_active=True, is_deleted=False)
        
        if variant.stock_quantity < 1:
            return JsonResponse({
                'success': False,
                'message': 'Product is out of stock'
            })
        
        cart = get_or_create_cart(request.user)
        existing_item = CartItem.objects.filter(cart=cart, variant=variant).first()
        removed = False
        added = False
        
        if existing_item:
            # Remove from cart
            existing_item.delete()
            removed = True
            message = 'Product removed from cart'
        else:
            # Add to cart
            CartItem.objects.create(
                cart=cart,
                variant=variant,
                quantity=1
            )
            added = True
            message = 'Product added to cart'
            
            # MUTUAL EXCLUSIVITY: Remove from wishlist if adding to cart
            wishlist = get_or_create_wishlist(request.user)
            WishlistItem.objects.filter(wishlist=wishlist, product=variant.product).delete()
        
        # Refresh and get totals
        cart.refresh_from_db()
        wishlist = get_or_create_wishlist(request.user)
        
        return JsonResponse({
            'success': True,
            'added': added,
            'removed': removed,
            'message': message,
            'cart_count': cart.total_items,
            'wishlist_count': wishlist.total_items
        })
        
    except Exception as e:
        print(f"Error in toggle_cart_item: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Error toggling cart item'
        })

@require_POST
@login_required
@transaction.atomic
def update_cart_variant_ajax(request):
    try:
        data = json.loads(request.body)
        item_id = data.get('item_id')
        new_variant_id = data.get('variant_id')
        
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        new_variant = get_object_or_404(ProductVariant, id=new_variant_id, product=cart_item.variant.product, is_active=True, is_deleted=False)
        
        # Check stock for new variant
        if new_variant.stock_quantity < 1:
            return JsonResponse({'success': False, 'message': 'Selected variant is out of stock'})

        # Check if another cart item already has this variant
        existing_item = CartItem.objects.filter(cart=cart_item.cart, variant=new_variant).exclude(id=item_id).first()
        
        merged = False
        if existing_item:
            # Merge quantities if same variant already in cart
            existing_item.quantity += cart_item.quantity
            # Check stock for merged quantity
            if existing_item.quantity > new_variant.stock_quantity:
                existing_item.quantity = new_variant.stock_quantity
            # Apply project max quantity limit (5)
            if existing_item.quantity > 5:
                existing_item.quantity = 5
                
            existing_item.save()
            cart_item.delete()
            message = 'Items merged in cart'
            item_id = str(existing_item.id)
            quantity = existing_item.quantity
            merged = True
        else:
            # Check stock for new variant
            if cart_item.quantity > new_variant.stock_quantity:
                cart_item.quantity = new_variant.stock_quantity
            
            cart_item.variant = new_variant
            cart_item.save()
            message = 'Variant updated'
            quantity = cart_item.quantity

        cart = cart_item.cart
        cart.refresh_from_db()
        
        return JsonResponse({
            'success': True,
            'message': message,
            'merged': merged,
            'item_id': item_id,
            'item_quantity': quantity,
            'item_unit_price': float(new_variant.get_discounted_price()),
            'item_total': float(new_variant.get_discounted_price() * quantity),
            'cart_count': cart.total_items,
            'subtotal': float(cart.subtotal),
            'total_discount': float(cart.total_discount),
            'final_total': float(cart.final_total),
            'shipping_cost': float(cart.shipping_cost),
        })
    except Exception as e:
        print(f"Error updating variant: {str(e)}")
        return JsonResponse({'success': False, 'message': 'Error updating variant'})

@require_POST
@login_required
@transaction.atomic
def update_cart_item_ajax(request):
    try:
        data = json.loads(request.body)
        item_id = data.get('item_id')
        quantity = int(data.get('quantity', 1))
        
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        
        if cart_item.variant.is_deleted:
            cart_item.delete()
            return JsonResponse({'success': False, 'message': 'Product no longer available'})
            
        if quantity <= 0:
            cart_item.delete()
            message = 'Item removed'
        else:
            if quantity > cart_item.variant.stock_quantity:
                return JsonResponse({'success': False, 'message': f'Only {cart_item.variant.stock_quantity} available'})
            cart_item.quantity = quantity
            cart_item.save()
            message = 'Quantity updated'
            
        cart = get_or_create_cart(request.user)
        wishlist = get_or_create_wishlist(request.user)
        
        return JsonResponse({
            'success': True,
            'message': message,
            'item_quantity': cart_item.quantity if quantity > 0 else 0,
            'cart_count': cart.total_items,
            'wishlist_count': wishlist.total_items,
            'subtotal': float(cart.subtotal),
            'total_discount': float(cart.total_discount),
            'final_total': float(cart.final_total),
            'shipping_cost': float(cart.shipping_cost),
            'total_savings': float(cart.total_discount)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': 'Error updating cart'})

@login_required
@transaction.atomic
def update_cart_item(request, item_id):
    try:
        data = json.loads(request.body)
        quantity = int(data.get('quantity', 1))
        
        cart_item = get_object_or_404(
            CartItem, 
            id=item_id, 
            cart__user=request.user
        )
        
        if cart_item.variant.is_deleted:
            cart_item.delete()
            return JsonResponse({
                'success': False,
                'message': 'This product is no longer available'
            })
            
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
            
            # MUTUAL EXCLUSIVITY: Remove from wishlist if in cart
            wishlist = get_or_create_wishlist(request.user)
            WishlistItem.objects.filter(wishlist=wishlist, product=cart_item.variant.product).delete()
        
        cart = get_or_create_cart(request.user)
        wishlist = get_or_create_wishlist(request.user)
        
        return JsonResponse({
            'success': True,
            'message': message,
            'cart_count': cart.total_items,
            'wishlist_count': wishlist.total_items,
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
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.method == 'POST':
            return JsonResponse({
                'success': True,
                'message': 'Item removed from cart',
                'cart_count': cart.total_items,
                'subtotal': cart.subtotal,
                'total_discount': cart.total_discount,
                'final_total': cart.final_total
            })
        
        from django.contrib import messages
        messages.success(request, 'Item removed from cart')
        return redirect('shop:cart')
        
    except Exception as e:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.method == 'POST':
            return JsonResponse({
                'success': False,
                'message': 'Error removing item from cart'
            })
        from django.contrib import messages
        messages.error(request, 'Error removing item from cart')
        return redirect('shop:cart')

@login_required
def clear_cart(request):
    cart = get_or_create_cart(request.user)
    cart.items.all().delete()
    messages.success(request, 'Cart cleared successfully')
    return redirect('shop:cart')

@login_required
@transaction.atomic
def move_to_wishlist(request, item_id):
    """Move cart item to wishlist - supports both AJAX and Routing"""
    try:
        cart_item = get_object_or_404(
            CartItem, 
            id=item_id, 
            cart__user=request.user
        )
        product = cart_item.variant.product
        wishlist = get_or_create_wishlist(request.user)
        
        # Add to wishlist
        WishlistItem.objects.get_or_create(wishlist=wishlist, product=product)
        
        # Remove all variants of this product from cart to ensure mutual exclusivity
        CartItem.objects.filter(cart__user=request.user, variant__product=product).delete()
        
        cart = get_or_create_cart(request.user)
        cart.refresh_from_db()
        wishlist.refresh_from_db()
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.method == 'POST':
            return JsonResponse({
                'success': True,
                'message': 'Product moved to wishlist successfully',
                'cart_count': cart.total_items,
                'wishlist_count': wishlist.total_items,
                'subtotal': float(cart.subtotal),
                'total_discount': float(cart.total_discount),
                'final_total': float(cart.final_total)
            })
        
        from django.contrib import messages
        messages.success(request, 'Product moved to wishlist successfully')
        return redirect('shop:cart')
        
    except Exception as e:
        print(f"Error in move_to_wishlist: {str(e)}")
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.method == 'POST':
            return JsonResponse({
                'success': False,
                'message': 'Error moving product to wishlist'
            })
        from django.contrib import messages
        messages.error(request, 'Error moving product to wishlist')
        return redirect('shop:cart')

@require_POST
@login_required
@transaction.atomic
def move_all_to_wishlist(request):
    """AJAX endpoint to move all cart items to wishlist"""
    try:
        cart = get_or_create_cart(request.user)
        cart_items = cart.items.all()
        
        if not cart_items:
            return JsonResponse({
                'success': False,
                'message': 'Cart is empty'
            })
            
        wishlist = get_or_create_wishlist(request.user)
        
        # Move all unique products to wishlist
        products_to_move = set()
        for item in cart_items:
            products_to_move.add(item.variant.product)
            
        for product in products_to_move:
            WishlistItem.objects.get_or_create(wishlist=wishlist, product=product)
            
        # Clear the cart
        cart.items.all().delete()
        
        cart.refresh_from_db()
        wishlist.refresh_from_db()
        
        return JsonResponse({
            'success': True,
            'message': f'Moved {len(products_to_move)} products to wishlist',
            'cart_count': cart.total_items,
            'wishlist_count': wishlist.total_items,
            'subtotal': float(cart.subtotal),
            'total_discount': float(cart.total_discount),
            'final_total': float(cart.final_total)
        })
        
    except Exception as e:
        print(f"Error in move_all_to_wishlist: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Error moving all items to wishlist'
        })

# Wishlist Views
@login_required
def wishlist_view(request):
    wishlist = get_or_create_wishlist(request.user)
    wishlist_items = wishlist.items.select_related('product').prefetch_related('product__variants').annotate(
        avg_rating_sort=Avg('product__reviews__rating', filter=Q(product__reviews__is_approved=True)),
        review_count_sort=Count('product__reviews', filter=Q(product__reviews__is_approved=True))
    ).all()
    
    # Enrich the product objects with the annotated values for the properties to use
    for item in wishlist_items:
        item.product.avg_rating_sort = item.avg_rating_sort
        item.product.review_count_sort = item.review_count_sort
    
    context = {
        'wishlist': wishlist,
        'wishlist_items': wishlist_items,
    }
    return render(request, 'user/wishlist/wishlist_view.html', context)

@require_POST
@login_required
@transaction.atomic
def toggle_wishlist(request):
    """AJAX endpoint to toggle product in wishlist"""
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        
        product = get_object_or_404(Product, id=product_id, is_active=True)
        wishlist = get_or_create_wishlist(request.user)
        
        existing_item = WishlistItem.objects.filter(wishlist=wishlist, product=product).first()
        
        if existing_item:
            # Remove from wishlist
            existing_item.delete()
            status = 'removed'
            message = 'Product removed from wishlist'
        else:
            # Add to wishlist
            WishlistItem.objects.create(wishlist=wishlist, product=product)
            status = 'added'
            message = 'Product added to wishlist'
            
            # MUTUAL EXCLUSIVITY: Remove from cart if adding to wishlist
            # Find any cart items containing variants of this product
            cart = get_or_create_cart(request.user)
            CartItem.objects.filter(cart=cart, variant__product=product).delete()
        
        wishlist.refresh_from_db()
        cart = get_or_create_cart(request.user)
        
        return JsonResponse({
            'success': True,
            'status': status,
            'message': message,
            'wishlist_count': wishlist.total_items,
            'cart_count': cart.total_items
        })
        
    except Exception as e:
        print(f"Error in toggle_wishlist: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Error toggling wishlist item'
        })


@login_required
@transaction.atomic
def add_to_wishlist(request, product_id):
    try:
        product = get_object_or_404(Product, id=product_id, is_active=True)
        wishlist = get_or_create_wishlist(request.user)
        
        wishlist_item, created = WishlistItem.objects.get_or_create(
            wishlist=wishlist,
            product=product
        )
        
        if created:
            # MUTUAL EXCLUSIVITY: Remove from cart if adding to wishlist
            # Find any cart items containing variants of this product
            cart = get_or_create_cart(request.user)
            CartItem.objects.filter(cart=cart, variant__product=product).delete()
        
        cart = get_or_create_cart(request.user)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Product added to wishlist',
                'wishlist_count': wishlist.total_items,
                'cart_count': cart.total_items
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


@require_POST  # Add this decorator
@login_required
def remove_from_wishlist(request, item_id):
    """AJAX endpoint to remove item from wishlist"""
    try:
        wishlist_item = get_object_or_404(
            WishlistItem, 
            id=item_id, 
            wishlist__user=request.user
        )
        wishlist_item.delete()
        
        wishlist = get_or_create_wishlist(request.user)
        wishlist.refresh_from_db()
        
        return JsonResponse({
            'success': True,
            'status': 'removed',
            'message': 'Product removed from wishlist',
            'wishlist_count': wishlist.total_items
        })
        
    except Exception as e:
        print(f"Error in remove_from_wishlist: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Error removing product from wishlist'
        })

@require_POST
@login_required
@transaction.atomic
def move_to_cart(request, item_id):
    """AJAX endpoint to move wishlist item to cart"""
    try:
        wishlist_item = get_object_or_404(
            WishlistItem, 
            id=item_id, 
            wishlist__user=request.user
        )
        
        # Get variant (either specified or first available)
        variant = None
        if request.body:
            try:
                data = json.loads(request.body)
                variant_id = data.get('variant_id')
                if variant_id:
                    variant = wishlist_item.product.variants.filter(id=variant_id, is_active=True, is_deleted=False).first()
            except json.JSONDecodeError:
                pass
        
        if not variant:
            variant = wishlist_item.product.variants.filter(is_active=True, is_deleted=False, stock_quantity__gt=0).first()
        
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
            
            cart.refresh_from_db()
            wishlist = get_or_create_wishlist(request.user)
            wishlist.refresh_from_db()
            
            return JsonResponse({
                'success': True,
                'message': 'Product moved to cart successfully',
                'cart_count': cart.total_items,
                'wishlist_count': wishlist.total_items
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Product is out of stock'
            })
            
    except Exception as e:
        print(f"Error in move_to_cart: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Error moving product to cart'
        })

@require_POST
@login_required
@transaction.atomic
def move_all_to_cart(request):
    """AJAX endpoint to move all wishlist items to cart"""
    try:
        wishlist = get_or_create_wishlist(request.user)
        wishlist_items = wishlist.items.all()
        
        if not wishlist_items:
            return JsonResponse({
                'success': False,
                'message': 'Wishlist is empty'
            })
            
        cart = get_or_create_cart(request.user)
        moved_count = 0
        
        for item in wishlist_items:
            # Get the first available variant
            variant = item.product.variants.filter(is_active=True, is_deleted=False, stock_quantity__gt=0).first()
            if variant:
                cart_item, created = CartItem.objects.get_or_create(
                    cart=cart,
                    variant=variant,
                    defaults={'quantity': 1}
                )
                if not created:
                    cart_item.quantity += 1
                    cart_item.save()
                
                # Item is removed from wishlist by signal or explicitly
                item.delete()
                moved_count += 1
        
        cart.refresh_from_db()
        wishlist.refresh_from_db()
        
        return JsonResponse({
            'success': True,
            'message': f'Moved {moved_count} items to cart',
            'cart_count': cart.total_items,
            'wishlist_count': wishlist.total_items
        })
        
    except Exception as e:
        print(f"Error in move_all_to_cart: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Error moving all items to cart'
        })

@require_POST
@login_required
@transaction.atomic
def clear_wishlist(request):
    """AJAX endpoint to clear the entire wishlist"""
    try:
        wishlist = get_or_create_wishlist(request.user)
        wishlist.items.all().delete()
        wishlist.refresh_from_db()
        
        return JsonResponse({
            'success': True,
            'message': 'Wishlist cleared successfully',
            'wishlist_count': 0
        })
        
    except Exception as e:
        print(f"Error in clear_wishlist: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Error clearing wishlist'
        })

# AJAX Views
@login_required
def ajax_cart_count(request):
    cart = get_or_create_cart(request.user)
    return JsonResponse({'count': cart.total_items})

@login_required
def ajax_wishlist_count(request):
    wishlist = get_or_create_wishlist(request.user)
    return JsonResponse({'count': wishlist.total_items})

def get_csrf_token(request):
    from django.middleware.csrf import get_token
    return JsonResponse({'csrfToken': get_token(request)})