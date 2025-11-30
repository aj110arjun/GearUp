import random
import string
import threading
import json

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from django.urls import reverse

from decimal import Decimal

from common.user.address.models import Address
from common.user.cart_wishlist.models import Cart, CartItem
from core.services import send_order_confirmation_email
from common.products.models import ProductVariant  

from .models import Order, Payment
from .utils import create_razorpay_order, verify_payment_signature, get_payment_details

# ==================== STOCK MANAGEMENT FUNCTIONS ====================


def decrease_variant_stock(variant, quantity):
    """
    Decrease stock quantity for a product variant
    Returns True if successful, False if insufficient stock
    """
    if variant.stock_quantity >= quantity:
        variant.stock_quantity -= quantity
        variant.save()
        print(f"DEBUG: ✅ Stock decreased for {variant}. New stock: {variant.stock_quantity}")
        return True
    else:
        print(f"DEBUG: ❌ Insufficient stock for {variant}. Requested: {quantity}, Available: {variant.stock_quantity}")
        return False

def increase_variant_stock(variant, quantity):
    """
    Increase stock quantity for a product variant (for cancellations/returns)
    """
    variant.stock_quantity += quantity
    variant.save()
    print(f"DEBUG: ✅ Stock increased for {variant}. New stock: {variant.stock_quantity}")
    return True

def check_stock_availability(cart_items):
    """
    Check if all cart items have sufficient stock
    Returns (is_available, out_of_stock_items)
    """
    out_of_stock_items = []
    
    for cart_item in cart_items:
        variant = cart_item.variant
        if variant.stock_quantity < cart_item.quantity:
            out_of_stock_items.append({
                'product': variant.product.name,
                'variant': str(variant),
                'requested': cart_item.quantity,
                'available': variant.stock_quantity
            })
    
    return len(out_of_stock_items) == 0, out_of_stock_items

def validate_cart_stock(cart_items):
    """
    Validate stock for all cart items and return detailed results
    """
    validation_results = {
        'is_valid': True,
        'out_of_stock_items': [],
        'low_stock_items': [],
        'available_items': []
    }
    
    for cart_item in cart_items:
        variant = cart_item.variant
        item_info = {
            'cart_item': cart_item,
            'variant': variant,
            'product': variant.product,
            'requested_quantity': cart_item.quantity,
            'available_quantity': variant.stock_quantity
        }
        
        if variant.stock_quantity <= 0:
            validation_results['is_valid'] = False
            validation_results['out_of_stock_items'].append(item_info)
        elif variant.stock_quantity < cart_item.quantity:
            validation_results['is_valid'] = False
            validation_results['low_stock_items'].append(item_info)
        else:
            validation_results['available_items'].append(item_info)
    
    return validation_results

def process_stock_decrease(pending_cart_items):
    """Process stock decrease for all cart items with proper error handling"""
    stock_results = {
        'successful': [],
        'failed': []
    }
    
    for cart_item_data in pending_cart_items:
        variant_id = cart_item_data['variant_id']
        quantity = cart_item_data['quantity']
        
        variant = ProductVariant.objects.filter(id=variant_id).first()
        if variant:
            if decrease_variant_stock(variant, quantity):
                stock_results['successful'].append({
                    'variant': variant,
                    'quantity': quantity
                })
            else:
                stock_results['failed'].append({
                    'variant_id': variant_id,
                    'variant': variant,
                    'quantity': quantity,
                    'reason': 'insufficient_stock'
                })
        else:
            stock_results['failed'].append({
                'variant_id': variant_id,
                'variant': None,
                'quantity': quantity,
                'reason': 'variant_not_found'
            })
    
    return stock_results

# ==================== ORDER VIEWS ====================

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
    
    # Check stock availability before showing checkout page
    stock_validation = validate_cart_stock(cart_items)
    if not stock_validation['is_valid']:
        messages.error(request, 'Some items in your cart have stock issues. Please update your cart.')
        
        for item in stock_validation['out_of_stock_items']:
            messages.error(request, 
                f"❌ {item['product'].name} - {item['variant']} is out of stock.")
        
        for item in stock_validation['low_stock_items']:
            messages.warning(request, 
                f"⚠️ {item['product'].name} - {item['variant']}: Only {item['available_quantity']} available (you requested {item['requested_quantity']})")
        
        return redirect('shop:cart')
    
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
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'stock_validation': stock_validation,
    }
    return render(request, 'user/orders/checkout.html', context)

@login_required
@transaction.atomic
def process_checkout(request, cart, cart_items):
    """Process the checkout and create individual orders with stock management"""
    try:
        # Get selected address
        shipping_address_id = request.POST.get('shipping_address')
        payment_method = request.POST.get('payment_method', 'cash_on_delivery')
        
        if not shipping_address_id:
            messages.error(request, 'Please select a shipping address.')
            return redirect('orders:checkout')
        
        shipping_address = Address.objects.filter(id=shipping_address_id, user=request.user).first()
        if not shipping_address:
            messages.error(request, 'Selected address not found.')
            return redirect('orders:checkout')
        
        # Check if user agreed to terms
        agree_terms = request.POST.get('agree_terms')
        if not agree_terms:
            messages.error(request, 'Please agree to the terms and conditions.')
            return redirect('orders:checkout')
        
        # Double-check stock availability before processing
        stock_validation = validate_cart_stock(cart_items)
        if not stock_validation['is_valid']:
            messages.error(request, 'Some items are now out of stock. Please update your cart.')
            return redirect('shop:cart')
        
        created_orders = []
        
        print(f"=== DEBUG: Starting checkout for {len(cart_items)} items ===")
        
        # Create individual order for each cart item and decrease stock
        for index, cart_item in enumerate(cart_items):
            print(f"DEBUG: Processing cart item {index + 1}: {cart_item}")
            
            # Get product variant details safely
            variant = cart_item.variant
            print(f"DEBUG: Variant: {variant}")
            print(f"DEBUG: Variant ID: {getattr(variant, 'id', 'NO ID')}")
            print(f"DEBUG: Current stock: {variant.stock_quantity}")
            
            # SAFEGUARD: Check if variant exists
            if not variant:
                print("DEBUG: ERROR - Variant is None!")
                messages.error(request, 'Variant information is missing. Please contact support.')
                return redirect('orders:checkout')
            
            # Get product from variant
            product = variant.product
            if not product:
                print("DEBUG: ERROR - Product is None!")
                messages.error(request, 'Product information is missing. Please contact support.')
                return redirect('orders:checkout')
            
            # Generate order number
            order_number = generate_order_number()
            print(f"DEBUG: Generated order number: {order_number}")
            
            # Calculate pricing with safeguards
            unit_price = variant.price if variant.price else Decimal('0.00')
            quantity = cart_item.quantity if cart_item.quantity else 1
            
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
            
            # Create the order
            order = Order.objects.create(**order_data)
            created_orders.append(order)
            print(f"DEBUG: ✅ Successfully created order {order.id}")
            
            # DECREASE STOCK after successful order creation
            if payment_method == 'cash_on_delivery':
                # For COD, decrease stock immediately
                stock_decreased = decrease_variant_stock(variant, quantity)
                if not stock_decreased:
                    # Rollback transaction if stock decrease fails
                    raise Exception(f"Insufficient stock for {variant}. Available: {variant.stock_quantity}, Requested: {quantity}")
        
        # ✅ FIX: Delete the entire cart and its items
        # This will automatically delete all related CartItem objects due to CASCADE
        cart.delete()
        print(f"DEBUG: ✅ Cart and all cart items deleted successfully")
        
        # Optional: Send order confirmation email in background
        email_thread = threading.Thread(
            target=send_order_confirmation_email,
            args=(request.user.email, created_orders)
        )
        email_thread.start()
        print(f"DEBUG: ✅ Order confirmation email process started")
        
        messages.success(request, f'Order placed successfully! {len(created_orders)} individual order(s) created.')
        print(f"DEBUG: ✅ Checkout process completed successfully")
        return redirect('orders:order_list')
        
    except Exception as e:
        print(f"ERROR in process_checkout: {str(e)}")
        import traceback
        print(traceback.format_exc())
        messages.error(request, f'Error processing your order: {str(e)}')
        return redirect('orders:checkout')

@require_POST
@login_required
@transaction.atomic
def create_razorpay_order_view(request):
    """Create Razorpay order for online payment with stock management"""
    from common.user.cart_wishlist.utils import get_or_create_active_cart
    
    # Get cart and items
    cart = get_or_create_active_cart(request.user)
    cart_items = cart.items.select_related('variant__product').all()
    
    if not cart_items:
        return JsonResponse({
            'success': False,
            'message': 'Your cart is empty'
        })
    
    # Get selected address
    shipping_address_id = request.POST.get('shipping_address')
    if not shipping_address_id:
        return JsonResponse({
            'success': False,
            'message': 'Please select a shipping address'
        })
    
    shipping_address = Address.objects.filter(id=shipping_address_id, user=request.user).first()
    if not shipping_address:
        return JsonResponse({
            'success': False,
            'message': 'Selected address not found'
        })
    
    # Check stock availability before creating orders
    stock_validation = validate_cart_stock(cart_items)
    if not stock_validation['is_valid']:
        error_message = "Some items in your cart are out of stock. Please update your cart."
        return JsonResponse({
            'success': False,
            'message': error_message
        })
    
    # Calculate total amount
    cart_total = sum(item.total_price for item in cart_items)
    tax_amount = cart_total * Decimal('0.1')
    shipping_cost = Decimal('0.00')
    total_amount = cart_total + tax_amount + shipping_cost
    
    # Create orders in database first (but don't decrease stock yet for Razorpay)
    created_orders = []
    for cart_item in cart_items:
        variant = cart_item.variant
        product = variant.product
        
        order_number = generate_order_number()
        
        order = Order.objects.create(
            user=request.user,
            order_number=order_number,
            product=product,
            variant=variant,
            quantity=cart_item.quantity,
            unit_price=variant.price,
            subtotal=cart_item.total_price,
            tax_amount=cart_item.total_price * Decimal('0.1'),
            shipping_cost=Decimal('0.00'),
            total_amount=cart_item.total_price * Decimal('1.1'),  # Including tax
            payment_method='razorpay',
            shipping_address=shipping_address,
            order_status='pending',
            payment_status='pending',  # Will be updated after payment success
        )
        created_orders.append(order)
    
    # Create Razorpay order (amount in paise)
    amount_in_paise = int(total_amount * 100)
    razorpay_order = create_razorpay_order(
        amount=amount_in_paise,
        receipt=created_orders[0].order_number if created_orders else 'ORDER'
    )
    
    if not razorpay_order:
        # Delete created orders if Razorpay order creation fails
        for order in created_orders:
            order.delete()
        return JsonResponse({
            'success': False,
            'message': 'Failed to create payment order'
        })
    
    # Update orders with Razorpay order ID
    for order in created_orders:
        order.razorpay_order_id = razorpay_order['id']
        order.save()
    
    # Store order IDs and cart items in session for later retrieval
    request.session['pending_orders'] = [order.id for order in created_orders]
    request.session['razorpay_order_id'] = razorpay_order['id']
    # Store cart items info for stock management after payment
    request.session['pending_cart_items'] = [
        {
            'variant_id': str(item.variant.id),
            'quantity': item.quantity
        } for item in cart_items
    ]
    
    return JsonResponse({
        'success': True,
        'razorpay_order_id': razorpay_order['id'],
        'amount': amount_in_paise,
        'currency': 'INR',
        'key': settings.RAZORPAY_KEY_ID,
        'name': 'GearUp Store',
        'description': f'Order #{created_orders[0].order_number}',
        'prefill': {
            'name': f"{request.user.first_name} {request.user.last_name}",
            'email': request.user.email,
            'contact': request.user.phone if hasattr(request.user, 'phone') else ''
        },
        'notes': {
            'order_numbers': [order.order_number for order in created_orders]
        }
    })

@login_required
def payment_success(request):
    """Handle successful Razorpay payment and decrease stock"""
    payment_id = request.GET.get('payment_id')
    order_id = request.GET.get('order_id')
    signature = request.GET.get('signature')
    
    if payment_id and order_id and signature:
        # Verify payment signature
        is_valid = verify_payment_signature(order_id, payment_id, signature)
        
        if is_valid:
            # Get orders and cart items from session
            pending_order_ids = request.session.get('pending_orders', [])
            razorpay_order_id = request.session.get('razorpay_order_id')
            pending_cart_items = request.session.get('pending_cart_items', [])
            
            if not pending_order_ids:
                messages.error(request, 'Order session expired. Please contact support.')
                return redirect('orders:order_list')
            
            # Update orders and decrease stock
            orders = Order.objects.filter(id__in=pending_order_ids, user=request.user)
            
            with transaction.atomic():
                # Decrease stock for all ordered items
                stock_results = process_stock_decrease(pending_cart_items)
                
                # Log any failures (but don't stop the process)
                if stock_results['failed']:
                    print(f"WARNING: {len(stock_results['failed'])} stock decreases failed")
                    for failure in stock_results['failed']:
                        print(f"  - Variant {failure['variant_id']}: {failure['reason']}")
                
                # Update order statuses
                for order in orders:
                    order.payment_status = 'paid'
                    order.order_status = 'confirmed'
                    order.paid_at = timezone.now()
                    order.save()
                
                # Create payment record
                payment_details = get_payment_details(payment_id)
                Payment.objects.create(
                    order=orders.first(),
                    razorpay_payment_id=payment_id,
                    razorpay_order_id=order_id,
                    razorpay_signature=signature,
                    amount=sum(order.total_amount for order in orders),
                    currency='INR',
                    status='completed',
                    payment_method=payment_details.get('method') if payment_details else 'razorpay',
                    bank=payment_details.get('bank') if payment_details else None,
                    wallet=payment_details.get('wallet') if payment_details else None
                )
            
            # Clear cart
            from common.user.cart_wishlist.utils import get_or_create_active_cart
            cart = get_or_create_active_cart(request.user)
            cart.items.all().delete()
            
            # Clear session data
            session_keys = ['pending_orders', 'razorpay_order_id', 'pending_cart_items']
            for key in session_keys:
                if key in request.session:
                    del request.session[key]
            
            # Send confirmation email
            email_thread = threading.Thread(
                target=send_order_confirmation_email,
                args=(request.user.email, list(orders))
            )
            email_thread.start()
            
            messages.success(request, f'Payment successful! {orders.count()} order(s) confirmed.')
            return render(request, 'user/orders/payment_success.html', {'orders': orders})
        else:
            messages.error(request, 'Payment verification failed')
    else:
        messages.error(request, 'Invalid payment response')
    
    return redirect('orders:order_list')

@login_required
def payment_failure(request):
    """Handle failed payment - delete pending orders"""
    order_id = request.GET.get('order_id')
    error_code = request.GET.get('error_code')
    error_description = request.GET.get('error_description')
    
    # Clean up pending orders on payment failure
    pending_order_ids = request.session.get('pending_orders', [])
    if pending_order_ids:
        Order.objects.filter(id__in=pending_order_ids, user=request.user).delete()
    
    # Clear session data
    session_keys = ['pending_orders', 'razorpay_order_id', 'pending_cart_items']
    for key in session_keys:
        if key in request.session:
            del request.session[key]
    
    messages.error(request, f'Payment failed. {error_description}')
    return render(request, 'user/orders/payment_failure.html')

@csrf_exempt
@require_POST
def payment_webhook(request):
    """Handle Razorpay webhooks for payment status updates"""
    # Get webhook data
    webhook_body = request.body.decode('utf-8')
    webhook_data = json.loads(webhook_body)
    
    # Verify webhook signature (optional but recommended)
    # received_signature = request.headers.get('X-Razorpay-Signature')
    
    event = webhook_data.get('event')
    payload = webhook_data.get('payload', {})
    payment_entity = payload.get('payment', {})
    order_entity = payload.get('order', {})
    
    if event == 'payment.captured':
        # Payment successful
        razorpay_payment_id = payment_entity.get('id')
        razorpay_order_id = order_entity.get('id')
        amount = payment_entity.get('amount') / 100  # Convert from paise
        
        # Find orders
        orders = Order.objects.filter(razorpay_order_id=razorpay_order_id)
        
        if orders.exists():
            with transaction.atomic():
                # Update orders
                for order in orders:
                    order.payment_status = 'completed'
                    order.order_status = 'confirmed'
                    order.paid_at = timezone.now()
                    order.save()
                
                # Create payment record
                Payment.objects.create(
                    order=orders.first(),
                    razorpay_payment_id=razorpay_payment_id,
                    razorpay_order_id=razorpay_order_id,
                    amount=amount,
                    currency='INR',
                    status='completed',
                    payment_method=payment_entity.get('method'),
                    bank=payment_entity.get('bank'),
                    wallet=payment_entity.get('wallet')
                )
            
            print(f"Webhook: Payment successful for {orders.count()} orders")
        
    elif event == 'payment.failed':
        # Payment failed
        razorpay_order_id = order_entity.get('id')
        
        orders = Order.objects.filter(razorpay_order_id=razorpay_order_id)
        for order in orders:
            order.payment_status = 'failed'
            order.save()
        
        print(f"Webhook: Payment failed for order {razorpay_order_id}")
    
    return JsonResponse({'status': 'success'})

# ==================== ORDER MANAGEMENT VIEWS ====================

@login_required
def order_list(request):
    """Display orders for logged-in user with pagination"""
    orders_list = Order.objects.filter(user=request.user).select_related(
        'product', 'variant', 'shipping_address'
    ).order_by('-created_at')
    
    # Pagination - 5 orders per page
    paginator = Paginator(orders_list, 5)
    page = request.GET.get('page')
    
    try:
        orders = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        orders = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page of results
        orders = paginator.page(paginator.num_pages)
    
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
    """Cancel an order and restore stock"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if not order.can_be_cancelled:
        messages.error(request, 'This order cannot be cancelled.')
        return redirect('orders:order_list')
    
    # Restore stock when order is cancelled
    if order.variant and order.order_status in ['pending', 'confirmed']:
        stock_restored = increase_variant_stock(order.variant, order.quantity)
        if stock_restored:
            messages.info(request, f'Stock has been restored for {order.product.name}.')
        else:
            messages.warning(request, f'Stock restoration failed for {order.product.name}.')
    
    order.order_status = 'cancelled'
    order.payment_status = 'refunded' if order.payment_status == 'paid' else 'failed'
    order.save()
    
    messages.success(request, 'Order cancelled successfully.')
    return redirect('orders:order_list')

@login_required
def track_order(request, order_id):
    """Track order status and shipping information"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Mock tracking data - integrate with actual shipping provider
    tracking_info = {
        'status': order.order_status,
        'estimated_delivery': order.created_at + timezone.timedelta(days=7),
        'carrier': 'GearUp Express',
        'tracking_number': f"GE{order.order_number}",
        'updates': [
            {
                'date': order.created_at,
                'status': 'Order Placed',
                'description': 'Your order has been received and is being processed.'
            }
        ]
    }
    
    # Add more updates based on order status
    if order.order_status in ['confirmed', 'processing']:
        tracking_info['updates'].append({
            'date': order.created_at + timezone.timedelta(hours=2),
            'status': 'Processing',
            'description': 'Your order is being prepared for shipment.'
        })
    
    if order.order_status in ['shipped', 'delivered']:
        tracking_info['updates'].append({
            'date': order.created_at + timezone.timedelta(days=1),
            'status': 'Shipped',
            'description': 'Your order has been shipped and is on its way.'
        })
    
    if order.order_status == 'delivered':
        tracking_info['updates'].append({
            'date': order.delivered_at or order.created_at + timezone.timedelta(days=5),
            'status': 'Delivered',
            'description': 'Your order has been delivered successfully.'
        })
    
    context = {
        'order': order,
        'tracking_info': tracking_info
    }
    return render(request, 'user/orders/track_order.html', context)

@login_required
def download_invoice(request, order_id):
    """Generate and download order invoice"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # For now, return a simple message
    # You can implement PDF generation here using libraries like reportlab or weasyprint
    messages.info(request, f'Invoice download for order #{order.order_number} will be available soon.')
    return redirect('orders:order_detail', order_id=order_id)

@login_required
def reorder(request, order_id):
    """Reorder a previous order"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    from common.user.cart_wishlist.utils import get_or_create_active_cart
    
    # Get or create active cart
    cart = get_or_create_active_cart(request.user)
    
    # Check if variant is still available and in stock
    if order.variant and order.variant.is_active and order.variant.stock_quantity > 0:
        # Add item to cart
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            variant=order.variant,
            defaults={'quantity': order.quantity}
        )
        
        if not created:
            cart_item.quantity += order.quantity
            cart_item.save()
        
        messages.success(request, f'{order.product.name} added to cart successfully.')
    else:
        messages.error(request, f'{order.product.name} is currently unavailable.')
    
    return redirect('shop:cart')

# ==================== UTILITY FUNCTIONS ====================

def generate_order_number():
    """Generate unique order number"""
    timestamp = int(timezone.now().timestamp())
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"ORD{timestamp}{random_str}"

# ==================== ADMIN ORDER VIEWS ====================

@login_required
def admin_order_list(request):
    """Admin view for all orders (staff only)"""
    if not request.user.is_staff:
        messages.error(request, 'Access denied.')
        return redirect('orders:order_list')
    
    orders_list = Order.objects.all().select_related(
        'user', 'product', 'variant', 'shipping_address'
    ).order_by('-created_at')
    
    # Filtering
    status_filter = request.GET.get('status')
    if status_filter:
        orders_list = orders_list.filter(order_status=status_filter)
    
    # Pagination
    paginator = Paginator(orders_list, 20)
    page = request.GET.get('page')
    
    try:
        orders = paginator.page(page)
    except PageNotAnInteger:
        orders = paginator.page(1)
    except EmptyPage:
        orders = paginator.page(paginator.num_pages)
    
    context = {
        'orders': orders,
        'status_filter': status_filter,
        'total_orders': orders_list.count(),
    }
    return render(request, 'admin/orders/order_list.html', context)

@login_required
def update_order_status(request, order_id):
    """Update order status (staff only)"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'message': 'Access denied.'})
    
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        new_status = request.POST.get('status')
        
        if new_status in dict(Order.ORDER_STATUS_CHOICES):
            order.order_status = new_status
            
            # Update timestamps for specific statuses
            if new_status == 'delivered' and not order.delivered_at:
                order.delivered_at = timezone.now()
            elif new_status == 'cancelled' and not order.cancelled_at:
                order.cancelled_at = timezone.now()
            
            order.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Order status updated to {new_status}.'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Invalid status.'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})