# orders/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from common.user.cart_wishlist.models import Cart, CartItem
from common.wallet.models import Wallet
from core.services import WalletService

import random
import string

from common.user.address.models import Address
from .models import Order

@login_required
def checkout(request):
    """Checkout process with individual product orders"""

    
    
    # Get active cart for user
    cart = Cart.objects.filter(user=request.user, is_active=True).first()
    
    if not cart:
        messages.error(request, 'No active cart found.')
        return redirect('shop:cart')
    
    cart_items = cart.items.select_related('variant__product').all()
    
    if not cart_items:
        messages.error(request, 'Your cart is empty.')
        return redirect('shop:cart')
    
    # Get user addresses
    addresses = Address.objects.filter(user=request.user, is_active=True)
    default_shipping = addresses.filter(is_default=True).first()
    
    # Get user wallet
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        return process_checkout(request, cart, cart_items, wallet)
    
    # Calculate cart totals
    cart_total = sum(item.total_price for item in cart_items)
    tax_amount = cart_total * Decimal('0.1')  # 10% tax
    shipping_cost = Decimal('0.00')  # Free shipping
    final_total = cart_total + tax_amount + shipping_cost
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'addresses': addresses,
        'default_shipping': default_shipping,
        'cart_total': cart_total,
        'tax_amount': tax_amount,
        'shipping_cost': shipping_cost,
        'final_total': final_total,
        'cart_item_count': cart_items.count(),
        'user': request.user,
        'wallet_balance': wallet.balance,  # Add wallet balance to context
    }
    return render(request, 'user/orders/checkout.html', context)
        
    

# orders/views.py
@transaction.atomic
def process_checkout(request, cart, cart_items, wallet):
    """Process the checkout and create individual orders"""
    try:
        # Get selected address
        shipping_address_id = request.POST.get('shipping_address')
        payment_method = request.POST.get('payment_method', 'cash_on_delivery')
        
        # Get Razorpay details if available
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_signature = request.POST.get('razorpay_signature')
        
        if not shipping_address_id:
            messages.error(request, 'Please select a shipping address.')
            return redirect('orders:checkout')
        
        try:
            shipping_address = Address.objects.get(id=shipping_address_id, user=request.user)
        except Address.DoesNotExist:
            messages.error(request, 'Selected address not found.')
            return redirect('orders:checkout')
        
        # Calculate total amount
        cart_total = sum(item.total_price for item in cart_items)
        tax_amount = cart_total * Decimal('0.1')
        shipping_cost = Decimal('0.00')
        final_total = cart_total + tax_amount + shipping_cost
        
        # Handle wallet payment
        if payment_method == 'wallet':
            if wallet.balance < final_total:
                messages.error(request, f'Insufficient wallet balance. You need ₹{final_total} but have only ₹{wallet.balance}.')
                return redirect('orders:checkout')
            
            # Deduct amount from wallet
            try:
                transaction_obj = WalletService.make_payment(
                    wallet,
                    final_total,
                    f"Order payment for {len(cart_items)} items"
                )
            except ValueError as e:
                messages.error(request, str(e))
                return redirect('orders:checkout')
        
        # Handle Razorpay payment verification
        if payment_method == 'razorpay' and razorpay_payment_id:
            try:
                # Verify payment signature
                params_dict = {
                    'razorpay_order_id': razorpay_order_id,
                    'razorpay_payment_id': razorpay_payment_id,
                    'razorpay_signature': razorpay_signature
                }
                client.utility.verify_payment_signature(params_dict)
            except Exception as e:
                messages.error(request, 'Payment verification failed. Please try again.')
                return redirect('orders:checkout')
        
        created_orders = []
        
        # Create individual order for each cart item
        for cart_item in cart_items:
            # Calculate pricing for this individual product
            subtotal = cart_item.total_price
            tax_amount_item = subtotal * Decimal('0.1')  # 10% tax
            shipping_cost_item = Decimal('0.00')  # Free shipping
            total_amount_item = subtotal + tax_amount_item + shipping_cost_item
            
            # Create order using the Order model with ForeignKey relationships
            order = Order(
                user=request.user,
                product=cart_item.variant.product,  # ForeignKey to Product
                variant=cart_item.variant,  # ForeignKey to Variant
                quantity=cart_item.quantity,
                unit_price=cart_item.variant.price,  # Store price at time of order
                subtotal=subtotal,
                tax_amount=tax_amount_item,
                shipping_cost=shipping_cost_item,
                total_amount=total_amount_item,
                payment_method=payment_method,
                shipping_address=shipping_address,
                order_status='pending',
                payment_status='paid' if payment_method in ['wallet', 'razorpay'] else 'pending',
                paid_at=timezone.now() if payment_method in ['wallet', 'razorpay'] else None,
            )
            order.save()  # This will generate order_number automatically
            
            created_orders.append(order)
        
        # Deactivate the cart instead of deleting
        cart.is_active = False
        cart.save()
        
        messages.success(request, f'Order placed successfully! {len(created_orders)} individual order(s) created.')
        return redirect('orders:list')
        
    except Exception as e:
        messages.error(request, f'Error processing your order: {str(e)}')
        return redirect('orders:checkout')
        
    

def generate_order_number():
    """Generate unique order number"""
    timestamp = int(timezone.now().timestamp())
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"ORD{timestamp}{random_str}"

# orders/views.py
@login_required
def order_list(request):
    """Display orders for logged-in user with optimized queries"""
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
    return render(request, 'orders/order_detail.html', context)

@login_required
@transaction.atomic
def cancel_order(request, order_id):
    """Cancel an order"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if not order.can_be_cancelled:
        print(request, 'This order cannot be cancelled.')
        return redirect('orders:order_list')
    
    order.order_status = 'cancelled'
    order.payment_status = 'refunded' if order.payment_status == 'paid' else 'failed'
    order.save()
    
    messages.success(request, 'Order cancelled successfully.')
    return redirect('orders:order_list')