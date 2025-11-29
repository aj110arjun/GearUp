import random
import string
import threading

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone

from decimal import Decimal

from common.user.address.models import Address
from common.user.cart_wishlist.models import Cart, CartItem
from core.services import send_order_confirmation_email

from .models import Order

@login_required
def checkout(request):
    """Checkout process with individual product orders"""
    
    from common.user.cart_wishlist.utils import get_or_create_active_cart
    
    # Get or create active cart
    cart = get_or_create_active_cart(request.user)
    
    cart_items = cart.items.select_related('variant__product').all()
    
    if not cart_items:
        messages.error(request, 'Your cart is empty. Please add items before checkout.')
        return redirect('shop:cart')
    
    # Rest of the function remains the same...
    # Get user addresses
    addresses = Address.objects.filter(user=request.user, is_active=True)
    
    if request.method == 'POST':
        return process_checkout(request, cart, cart_items)
    
    # Calculate cart totals
    cart_total = sum(item.total_price for item in cart_items)
    tax_amount = cart_total * Decimal('0.1')  # 10% tax
    shipping_cost = Decimal('0.00')  # Free shipping
    final_total = cart_total + tax_amount + shipping_cost
        
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'addresses': addresses,
        'cart_total': cart_total,
        'tax_amount': tax_amount,
        'shipping_cost': shipping_cost,
        'final_total': final_total,
        'cart_item_count': cart_items.count(),
    }
    return render(request, 'user/orders/checkout.html', context)
    

# orders/views.py
@transaction.atomic
def process_checkout(request, cart, cart_items):
    """Process the checkout and create individual orders"""
    try:
        # Get selected address
        shipping_address_id = request.POST.get('shipping_address')
        payment_method = request.POST.get('payment_method', 'cash_on_delivery')
        
        if not shipping_address_id:
            messages.error(request, 'Please select a shipping address.')
            return redirect('orders:checkout')
        
        try:
            shipping_address = Address.objects.get(id=shipping_address_id, user=request.user)
        except Address.DoesNotExist:
            messages.error(request, 'Selected address not found.')
            return redirect('orders:checkout')
        
        # Check if user agreed to terms
        agree_terms = request.POST.get('agree_terms')
        if not agree_terms:
            messages.error(request, 'Please agree to the terms and conditions.')
            return redirect('orders:checkout')
        
        created_orders = []
        
        print(f"=== DEBUG: Starting checkout for {len(cart_items)} items ===")
        
        # Create individual order for each cart item
        for index, cart_item in enumerate(cart_items):
            print(f"DEBUG: Processing cart item {index + 1}: {cart_item}")
            
            # Get product variant details safely
            variant = cart_item.variant
            print(f"DEBUG: Variant: {variant}")
            print(f"DEBUG: Variant ID: {getattr(variant, 'id', 'NO ID')}")
            
            # SAFEGUARD: Check if variant exists
            if not variant:
                print("DEBUG: ERROR - Variant is None!")
                messages.error(request, 'Variant information is missing. Please contact support.')
                return redirect('orders:checkout')
            
            # Get product from variant
            try:
                product = variant.product
                print(f"DEBUG: Product: {product}")
                print(f"DEBUG: Product ID: {getattr(product, 'id', 'NO ID')}")
            except Exception as e:
                print(f"DEBUG: ERROR accessing variant.product: {str(e)}")
                messages.error(request, 'Product information is missing. Please contact support.')
                return redirect('orders:checkout')
            
            # SAFEGUARD: Check if product exists
            if not product:
                print("DEBUG: ERROR - Product is None!")
                messages.error(request, 'Product information is missing. Please contact support.')
                return redirect('orders:checkout')
            
            # Generate order number
            order_number = generate_order_number()
            print(f"DEBUG: Generated order number: {order_number}")
            
            # Calculate pricing with safeguards
            unit_price = getattr(variant, 'price', None)
            if unit_price is None:
                print("DEBUG: WARNING - Variant price is None, using 0.00")
                unit_price = Decimal('0.00')
            
            quantity = getattr(cart_item, 'quantity', 1)
            if quantity is None:
                print("DEBUG: WARNING - Cart item quantity is None, using 1")
                quantity = 1
            
            subtotal = unit_price * quantity
            tax_amount = subtotal * Decimal('0.1')
            shipping_cost = Decimal('0.00')
            total_amount = subtotal + tax_amount + shipping_cost
            
            print(f"DEBUG: Creating order with product: {product}")
            
            # Create order with ForeignKey relationships only
            order_data = {
                'user': request.user,
                'order_number': order_number,
                'product': product,  # Product ForeignKey
                'variant': variant,  # Variant ForeignKey
                'quantity': quantity,
                'unit_price': unit_price,
                'subtotal': subtotal,
                'tax_amount': tax_amount,
                'shipping_cost': shipping_cost,
                'total_amount': total_amount,
                'payment_method': payment_method,
                'shipping_address': shipping_address,
                'order_status': 'pending',
                'payment_status': 'pending' if payment_method == 'cash_on_delivery' else 'paid',
            }
            
            # Only set paid_at if payment is not COD
            if payment_method != 'cash_on_delivery':
                order_data['paid_at'] = timezone.now()
            
            print(f"DEBUG: Order data to be created:")
            for key, value in order_data.items():
                print(f"  {key}: {value} (type: {type(value)})")
            
            # Try to create the order
            try:
                order = Order.objects.create(**order_data)
                created_orders.append(order)
                print(f"DEBUG: ✅ Successfully created order {order.id}")
            except Exception as e:
                print(f"DEBUG: ❌ ERROR creating order: {str(e)}")
                import traceback
                print(traceback.format_exc())
                raise
        
        # Deactivate the cart
        cart.is_active = False
        cart.save()
        
        messages.success(request, f'Order placed successfully! {len(created_orders)} individual order(s) created.')
        return redirect('orders:order_list')
        
    except Exception as e:
        print(f"ERROR in process_checkout: {str(e)}")
        import traceback
        print(traceback.format_exc())
        messages.error(request, f'Error processing your order: {str(e)}')
        return redirect('orders:checkout')
        
    

def generate_order_number():
    """Generate unique order number"""
    timestamp = int(timezone.now().timestamp())
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"ORD{timestamp}{random_str}"

@login_required
def order_list(request):
    """Display orders for logged-in user"""
    orders = Order.objects.filter(user=request.user).select_related(
        'shipping_address'
    ).order_by('-created_at')
    
    context = {
        'orders': orders,
        'active_tab': 'orders'
    }
    return render(request, 'user/orders/order_list.html', context)

@login_required
def order_detail(request, order_id):
    """Display order details"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    context = {
        'order': order
    }
    return render(request, 'user/orders/order_detail.html', context)

@login_required
@transaction.atomic
def cancel_order(request, order_id):
    """Cancel an order"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if not order.can_be_cancelled:
        messages.error(request, 'This order cannot be cancelled.')
        return redirect('orders:order_list')
    
    order.order_status = 'cancelled'
    order.payment_status = 'refunded' if order.payment_status == 'paid' else 'failed'
    order.save()
    
    messages.success(request, 'Order cancelled successfully.')
    return redirect('orders:order_list')