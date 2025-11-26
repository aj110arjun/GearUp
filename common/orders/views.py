# orders/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone

from decimal import Decimal

from common.user.address.models import Address
from .forms import CheckoutForm
from .models import Order


@login_required
def checkout(request):
    """Checkout process with individual product orders"""
    try:
        from common.user.cart_wishlist.models import Cart, CartItem
        
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
        
        if request.method == 'POST':
            return process_checkout(request, cart, cart_items)
        
        # Calculate cart totals
        cart_total = sum(item.total_price for item in cart_items)
        tax_amount = cart_total * Decimal('0.1')  # 10% tax
        shipping_cost = Decimal('0.00')  # Free shipping as per your cart
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
        }
        return render(request, 'user/orders/checkout.html', context)
        
    except Exception as e:
        print(request, f'An error occurred while loading checkout: {str(e)}')
        return redirect('shop:cart')

@transaction.atomic
def process_checkout(request, cart, cart_items):
    """Process the checkout and create individual orders"""
    try:
        # Get or create default address
        shipping_address, created = Address.objects.get_or_create(
            user=request.user,
            is_default=True,
            defaults={
                'full_name': f"{request.user.first_name} {request.user.last_name}",
                'address_line1': 'Default Address',
                'city': 'Default City',
                'state': 'Default State',
                'zip_code': '00000',
                'country': 'Default Country',
                'address_type': 'home'
            }
        )
        
        created_orders = []
        
        # Create individual order for each cart item
        for cart_item in cart_items:
            # Calculate pricing for this individual product
            subtotal = cart_item.total_price
            tax_amount = subtotal * Decimal('0.1')  # 10% tax
            shipping_cost = Decimal('0.00')  # Free shipping
            total_amount = subtotal + tax_amount + shipping_cost
            
            order = Order.objects.create(
                user=request.user,
                product_id=cart_item.variant.product.id,
                product_name=cart_item.variant.product.name,
                product_sku=cart_item.variant.sku or f"SKU-{cart_item.variant.id}",
                product_price=cart_item.variant.price,
                product_image=cart_item.variant.product.image.url if cart_item.variant.product.image else '',
                quantity=cart_item.quantity,
                unit_price=cart_item.variant.price,
                subtotal=subtotal,
                tax_amount=tax_amount,
                shipping_cost=shipping_cost,
                total_amount=total_amount,
                payment_method='credit_card',  # Default payment method
                shipping_address=shipping_address,
                billing_address=shipping_address,  # Same as shipping for now
                order_status='confirmed',
                payment_status='paid',
                paid_at=timezone.now(),
            )
            
            created_orders.append(order)
        
        # Deactivate the cart instead of deleting
        cart.is_active = False
        cart.save()
        
        messages.success(request, f'Order placed successfully! {len(created_orders)} individual order(s) created.')
        return redirect('orders:order_list')
        
    except Exception as e:
        print(request, f'Error processing your order: {str(e)}')
        return redirect('orders:checkout')

@login_required
def order_list(request):
    """Display orders for logged-in user (works with AbstractUser)"""
    # request.user is your UserModel instance
    orders = Order.objects.filter(user=request.user).select_related(
        'shipping_address'
    ).order_by('-created_at')
    
    context = {
        'orders': orders,
        'active_tab': 'orders'
    }
    return render(request, 'orders/order_list.html', context)

@login_required
@transaction.atomic
def create_order_from_cart(request):
    """Create individual orders from cart"""
    try:
        from shop.models import Cart, CartItem
        
        # request.user is your custom UserModel
        cart = get_object_or_404(Cart, user=request.user, is_active=True)
        cart_items = cart.items.select_related('product').all()
        
        if not cart_items:
            messages.error(request, 'Your cart is empty.')
            return redirect('shop:cart')
        
        # Get default address from your Address model
        shipping_address = Address.objects.filter(user=request.user, is_default=True).first()
        
        if not shipping_address:
            messages.error(request, 'Please set up your shipping address.')
            return redirect('address:address_list')
        
        created_orders = []
        
        # Create individual order for each cart item
        for cart_item in cart_items:
            # Calculate pricing
            subtotal = cart_item.product.price * cart_item.quantity
            tax_amount = subtotal * Decimal('0.1')
            shipping_cost = Decimal('5.00')
            total_amount = subtotal + tax_amount + shipping_cost
            
            # Create order using your custom UserModel
            order = Order.objects.create(
                user=request.user,  # This is your UserModel instance
                product_id=cart_item.product.id,
                product_name=cart_item.product.name,
                product_price=cart_item.product.price,
                product_image=cart_item.product.image.url if cart_item.product.image else '',
                quantity=cart_item.quantity,
                unit_price=cart_item.product.price,
                subtotal=subtotal,
                tax_amount=tax_amount,
                shipping_cost=shipping_cost,
                total_amount=total_amount,
                payment_method='credit_card',
                shipping_address=shipping_address,
            )
            
            created_orders.append(order)
        
        # Clear cart
        cart.items.all().delete()
        cart.is_active = False
        cart.save()
        
        messages.success(request, f'Successfully created {len(created_orders)} order(s)!')
        return redirect('orders:order_list')
        
    except Exception as e:
        messages.error(request, f'Error creating orders: {str(e)}')
        return redirect('shop:cart')