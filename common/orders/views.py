# orders/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST
from django.db.models import Q, Sum, Count, F
from django.utils.decorators import method_decorator
from datetime import datetime, timedelta
from django.urls import reverse_lazy
from core.razorpay_service import RazorpayService
from django.http import JsonResponse
from django.conf import settings
from django.core.paginator import Paginator

import random
import string

from common.user.address.models import Address
from .models import Order
from .forms import OrderStatusForm
from common.user.cart_wishlist.models import Cart, CartItem
from common.wallet.models import Wallet, Transaction
from core.services import WalletService


@login_required(login_url='user_auth:signin')
@never_cache
def checkout(request):
    """Checkout process with individual product orders"""
    
    # Get active cart for user
    cart = Cart.objects.filter(user=request.user, is_active=True).first()
    
    if not cart:
        messages.error(request, 'No active cart found. Please add items to your cart first.')
        return redirect('shop:cart')
    
    cart_items = cart.items.select_related('variant__product').all()
    
    if not cart_items:
        messages.error(request, 'Your cart is empty.')
        return redirect('shop:cart')
    
    # Validate all items are available
    unavailable_items = []
    for item in cart_items:
        if not item.is_available:
            unavailable_items.append(item.variant.product.name)
    
    if unavailable_items:
        messages.error(
            request, 
            f'Some items in your cart are no longer available: {", ".join(unavailable_items)}'
        )
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
        'wallet_balance': wallet.balance,
    }
    return render(request, 'user/orders/checkout.html', context)
        
    

# orders/views.py
@transaction.atomic
def process_checkout(request, cart, cart_items, wallet):
    """Process the checkout and create individual orders"""
    
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
            product_names = ", ".join([item.variant.product.name for item in cart_items])
            transaction_obj = WalletService.make_payment(
                wallet,
                final_total,
                f"Order payment for {product_names}."
            )
        except ValueError as e:
            messages.error(request, str(e))
            return redirect('orders:checkout')
    
    # Handle Razorpay payment verification
    elif payment_method == 'razorpay':
        if not all([razorpay_payment_id, razorpay_order_id, razorpay_signature]):
            messages.error(request, 'Payment verification failed. Please try again.')
            return redirect('orders:checkout')
        
        try:
            # Initialize Razorpay service
            razorpay_service = RazorpayService()
            
            # Verify payment signature
            is_valid = razorpay_service.verify_payment(
                razorpay_payment_id,
                razorpay_order_id,
                razorpay_signature
            )
            
            if not is_valid:
                messages.error(request, 'Payment verification failed. Please try again.')
                return redirect('orders:checkout')
            
            # Optional: Fetch payment details from Razorpay
            try:
                payment_details = razorpay_service.fetch_payment(razorpay_payment_id)
                # You can store payment details in your Order model if needed
                razorpay_payment_status = payment_details.get('status')
            except:
                # If fetching fails, it's okay as we already verified the signature
                pass
                
        except Exception as e:
            messages.error(request, f'Payment verification failed: {str(e)}')
            return redirect('orders:checkout')
    
    # Handle Cash on Delivery
    elif payment_method == 'cash_on_delivery':
        # No payment processing needed for COD
        pass
    
    else:
        messages.error(request, 'Invalid payment method selected.')
        return redirect('orders:checkout')
    
    created_orders = []
    
    # Create individual order for each cart item
    for cart_item in cart_items:
        # Calculate pricing for this individual product
        subtotal = cart_item.total_price
        tax_amount_item = subtotal * Decimal('0.1')  # 10% tax
        shipping_cost_item = Decimal('0.00')  # Free shipping
        total_amount_item = subtotal + tax_amount_item + shipping_cost_item
        
        # Create order
        order = Order(
            user=request.user,
            product=cart_item.variant.product,
            variant=cart_item.variant,
            quantity=cart_item.quantity,
            unit_price=cart_item.variant.price,
            subtotal=subtotal,
            tax_amount=tax_amount_item,
            shipping_cost=shipping_cost_item,
            total_amount=total_amount_item,
            payment_method=payment_method,
            shipping_address=shipping_address,
            order_status='pending',
            payment_status='paid' if payment_method in ['wallet', 'razorpay'] else 'pending',
            paid_at=timezone.now() if payment_method in ['wallet', 'razorpay'] else None,
            # Store Razorpay details if applicable
            razorpay_payment_id=razorpay_payment_id if payment_method == 'razorpay' else None,
            razorpay_order_id=razorpay_order_id if payment_method == 'razorpay' else None,
        )
        order.save()
        
        created_orders.append(order)
    
    # Deactivate the cart
    cart.delete()
    
    # If only one order was created, redirect to its success page
    if len(created_orders) == 1:
        messages.success(request, 'Order placed successfully!')
        return redirect('orders:order_success', order_id=created_orders[0].id)
    else:
        # If multiple orders, redirect to orders list
        messages.success(request, f'Order placed successfully! {len(created_orders)} individual order(s) created.')
        return redirect('orders:order_list')
        
    

def generate_order_number():
    """Generate unique order number"""
    timestamp = int(timezone.now().timestamp())
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"ORD{timestamp}{random_str}"

# orders/views.py
@login_required(login_url='user_auth:signin')
@never_cache
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

@login_required(login_url='user_auth:signin')
@never_cache
def order_detail(request, order_id):
    """Display order details"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    context = {
        'order': order
    }
    return render(request, 'user/orders/order_details.html', context)

@login_required(login_url='user_auth:signin')
@never_cache
@transaction.atomic
def cancel_order(request, order_id):
    """Cancel an order"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    wallet = get_object_or_404(Wallet, user=request.user)
    transaction = Transaction.objects.filter(wallet=wallet)


    
    if not order.can_be_cancelled:
        print(request, 'This order cannot be cancelled.')
        return redirect('orders:order_list')
    
    if order.payment_status == 'paid' and order.payment_method in ['razorpay', 'wallet']:
        
        order.order_status = 'cancelled'
        wallet.balance += order.total_amount
        transaction.create(
            wallet=wallet,
            transaction_type='refund',
            description=f'Your Refund for order #{order.order_number} has been credited on your wallet',
            amount=order.total_amount,
            status='refunded'
        )
        
        wallet.save()

    order.payment_status = 'refunded' if order.payment_status == 'paid' else 'failed'
    order.save()
    
    messages.success(request, 'Order cancelled successfully.')
    return redirect('orders:order_list')



# ============ ADMIN VIEWS ============

@staff_member_required(login_url='auth_dashboard:signin')
def admin_order_list(request):
    """Admin order listing with advanced filters"""
    orders = Order.objects.all().select_related(
        'user', 
        'product', 
        'variant', 
        'shipping_address'
    ).order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        orders = orders.filter(
            Q(order_number__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(product__name__icontains=search_query) |
            Q(shipping_address__phone__icontains=search_query)
        )
    
    # Status filters
    order_status_filter = request.GET.get('order_status', '')
    if order_status_filter:
        orders = orders.filter(order_status=order_status_filter)
    
    payment_status_filter = request.GET.get('payment_status', '')
    if payment_status_filter:
        orders = orders.filter(payment_status=payment_status_filter)
    
    payment_method_filter = request.GET.get('payment_method', '')
    if payment_method_filter:
        orders = orders.filter(payment_method=payment_method_filter)
    
    # Date filters
    date_filter = request.GET.get('date_filter', '')
    today = timezone.now().date()
    
    if date_filter == 'today':
        orders = orders.filter(created_at__date=today)
    elif date_filter == 'week':
        week_ago = today - timedelta(days=7)
        orders = orders.filter(created_at__date__gte=week_ago)
    elif date_filter == 'month':
        month_ago = today - timedelta(days=30)
        orders = orders.filter(created_at__date__gte=month_ago)
    elif date_filter == 'year':
        year_ago = today - timedelta(days=365)
        orders = orders.filter(created_at__date__gte=year_ago)
    
    # Custom date range
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date and end_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            orders = orders.filter(created_at__date__range=[start_date, end_date])
        except ValueError:
            pass
    
    # Amount filters
    min_amount = request.GET.get('min_amount')
    max_amount = request.GET.get('max_amount')
    if min_amount:
        try:
            orders = orders.filter(total_amount__gte=Decimal(min_amount))
        except:
            pass
    if max_amount:
        try:
            orders = orders.filter(total_amount__lte=Decimal(max_amount))
        except:
            pass
    
    # Sorting
    sort_by = request.GET.get('sort', '-created_at')
    valid_sort_fields = [
        'created_at', '-created_at',
        'total_amount', '-total_amount',
        'order_number', '-order_number',
        'user__email', '-user__email'
    ]
    if sort_by in valid_sort_fields:
        orders = orders.order_by(sort_by)
    
    # Calculate statistics
    total_orders = orders.count()
    total_revenue = orders.aggregate(total=Sum('total_amount'))['total'] or 0
    average_order_value = total_revenue / total_orders if total_orders > 0 else 0
    
    # Count by status
    status_counts = orders.values('order_status').annotate(count=Count('id'))
    status_stats = {item['order_status']: item['count'] for item in status_counts}
    
    # Payment status counts
    payment_counts = orders.values('payment_status').annotate(count=Count('id'))
    payment_stats = {item['payment_status']: item['count'] for item in payment_counts}
    
    # Pagination
    paginator = Paginator(orders, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'orders': page_obj,
        'search_query': search_query,
        'order_status_filter': order_status_filter,
        'payment_status_filter': payment_status_filter,
        'payment_method_filter': payment_method_filter,
        'date_filter': date_filter,
        'start_date': start_date,
        'end_date': end_date,
        'min_amount': min_amount,
        'max_amount': max_amount,
        'sort_by': sort_by,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'average_order_value': average_order_value,
        'status_stats': status_stats,
        'payment_stats': payment_stats,
        'ORDER_STATUS_CHOICES': Order.ORDER_STATUS_CHOICES,
        'PAYMENT_STATUS_CHOICES': Order.PAYMENT_STATUS_CHOICES,
        'PAYMENT_METHOD_CHOICES': Order.PAYMENT_METHOD_CHOICES,
    }
    
    return render(request, 'admin/orders/order_list.html', context)


@staff_member_required(login_url='auth_dashboard:signin')
def admin_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    # Define status transitions
    status_transitions = {
        'pending': ['confirmed', 'cancelled'],
        'confirmed': ['processing', 'cancelled'],
        'processing': ['shipped', 'cancelled'],
        'shipped': ['delivered', 'returned', 'cancelled'],
        'delivered': ['returned'],
        'cancelled': [],
        'returned': [],
    }
    
    # Get current status and available next statuses
    current_status = order.order_status
    available_statuses = status_transitions.get(current_status, [])
    
    # Determine completed statuses (statuses before current status in the flow)
    status_flow = ['pending', 'confirmed', 'processing', 'shipped', 'delivered']
    if current_status in status_flow:
        current_index = status_flow.index(current_status)
        completed_statuses = status_flow[:current_index]
    else:
        completed_statuses = []
    
    context = {
        'order': order,
        'available_statuses': available_statuses,
        'completed_statuses': completed_statuses,
        'ORDER_STATUS_CHOICES': Order.ORDER_STATUS_CHOICES,
        'PAYMENT_STATUS_CHOICES': Order.PAYMENT_STATUS_CHOICES,
        'title': f'Order #{order.order_number}',
    }
    
    return render(request, 'admin/orders/order_detail.html', context)

@login_required
@require_POST
def create_razorpay_order(request):
    """Create Razorpay order for frontend"""
    try:
        # Get cart total
        cart = Cart.objects.filter(user=request.user, is_active=True).first()
        if not cart or not cart.items.exists():
            return JsonResponse({
                'success': False,
                'error': 'Cart is empty'
            })
        
        cart_items = cart.items.select_related('variant__product').all()
        cart_total = sum(item.total_price for item in cart_items)
        tax_amount = cart_total * Decimal('0.1')
        shipping_cost = Decimal('0.00')
        final_total = cart_total + tax_amount + shipping_cost
        
        # Create Razorpay order
        razorpay_service = RazorpayService()
        
        # Generate a unique receipt
        receipt = f"receipt_order_{int(timezone.now().timestamp())}_{request.user.id}"
        
        # Create order in Razorpay
        order = razorpay_service.create_order(
            amount=float(final_total),
            receipt=receipt
        )
        
        return JsonResponse({
            'success': True,
            'order_id': order['id'],
            'amount': order['amount'],
            'currency': order['currency'],
            'key_id': settings.RAZORPAY_KEY_ID,
            'receipt': order['receipt']
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@staff_member_required(login_url='auth_dashboard:signin')
@require_POST
def admin_order_update_status(request, order_id):
    """Update order status - handles POST requests only"""
    order = get_object_or_404(Order, id=order_id)
    
    new_status = request.POST.get('order_status')
    notes = request.POST.get('notes', '').strip()
    
    # Define status transitions
    status_transitions = {
        'pending': ['confirmed', 'cancelled'],
        'confirmed': ['processing', 'cancelled'],
        'processing': ['shipped', 'cancelled'],
        'shipped': ['delivered', 'returned', 'cancelled'],
        'delivered': ['returned'],
        'cancelled': [],
        'returned': [],
    }
    
    if not new_status:
        messages.error(request, 'Please select a status.')
        return redirect('orders:admin_order_detail', order_id=order_id)
    
    current_status = order.order_status
    available_statuses = status_transitions.get(current_status, [])
    
    if new_status not in available_statuses:
        messages.error(request, f'Invalid status transition from {current_status} to {new_status}.')
        return redirect('orders:admin_order_detail', order_id=order_id)
    
    # Store old status for comparison
    old_status = order.order_status
    
    # Process refund if order is being cancelled and was paid
    if new_status == 'cancelled' and order.payment_status == 'paid':
        try:
            # Get user's wallet
            wallet = Wallet.objects.get(user=order.user)
            
            # Refund amount to wallet
            refund_amount = order.total_amount
            transaction = WalletService.make_refund(
                wallet=wallet,
                amount=refund_amount,
                description=f"Refund for cancelled order #{order.order_number}",
                reference_id=str(order.id)
            )
            
            # Update order payment status to refunded
            order.payment_status = 'refunded'
            
            messages.success(request, f'Order #{order.order_number} cancelled and ₹{refund_amount} refunded to customer wallet.')
            
        except Wallet.DoesNotExist:
            # Create wallet for user if it doesn't exist
            wallet = Wallet.objects.create(
                user=order.user,
                balance=order.total_amount
            )
            order.payment_status = 'refunded'
            messages.success(request, f'Order #{order.order_number} cancelled and ₹{order.total_amount} refunded to newly created wallet.')
            
        except Exception as e:
            messages.error(request, f'Order cancelled but refund failed: {str(e)}')
            # Still mark as cancelled but payment status remains paid
            order.payment_status = 'paid'
    
    # Process refund if order is returned and was paid
    elif new_status == 'returned' and order.payment_status == 'paid':
        try:
            # Get user's wallet
            wallet = Wallet.objects.get(user=order.user)
            
            # Refund amount to wallet
            refund_amount = order.total_amount
            transaction = WalletService.make_refund(
                wallet=wallet,
                amount=refund_amount,
                description=f"Refund for returned order #{order.order_number}",
                reference_id=str(order.id)
            )
            
            # Update order payment status to refunded
            order.payment_status = 'refunded'
            
            messages.success(request, f'Order #{order.order_number} marked as returned and ₹{refund_amount} refunded to customer wallet.')
            
        except Wallet.DoesNotExist:
            # Create wallet for user if it doesn't exist
            wallet = Wallet.objects.create(
                user=order.user,
                balance=order.total_amount
            )
            order.payment_status = 'refunded'
            messages.success(request, f'Order #{order.order_number} returned and ₹{order.total_amount} refunded to newly created wallet.')
            
        except Exception as e:
            messages.error(request, f'Order returned but refund failed: {str(e)}')
            # Still mark as returned but payment status remains paid
    
    # Update order status
    order.order_status = new_status
    
    # Update timestamps based on status
    if new_status == 'delivered':
        order.delivered_at = timezone.now()
    elif new_status == 'cancelled':
        order.cancelled_at = timezone.now()
    elif new_status == 'returned':
        order.returned_at = timezone.now()
    
    order.save()
    
    # Create order status history (optional but recommended)
    try:
        from .models import OrderStatusHistory
        
        OrderStatusHistory.objects.create(
            order=order,
            old_status=old_status,
            new_status=new_status,
            changed_by=request.user,
            notes=notes or f"Status changed by admin"
        )
    except:
        pass  # If OrderStatusHistory model doesn't exist, skip
    
    return redirect('orders:admin_order_detail', order_id=order_id)


@staff_member_required(login_url='auth_dashboard:signin')
@require_POST
def admin_order_update_payment_status(request, order_id):
    """Update payment status"""
    order = get_object_or_404(Order, id=order_id)
    
    new_payment_status = request.POST.get('payment_status')
    
    if not new_payment_status:
        messages.error(request, 'Please select a payment status.')
        return redirect('orders:admin_order_detail', order_id=order_id)
    
    old_payment_status = order.payment_status
    order.payment_status = new_payment_status
    
    # Update payment timestamp if paid
    if new_payment_status == 'paid' and old_payment_status != 'paid':
        order.paid_at = timezone.now()
    
    order.save()
    
    messages.success(request, f'Payment status updated from {old_payment_status} to {new_payment_status}.')
    
    return redirect('orders:admin_order_detail', order_id=order_id)


@staff_member_required(login_url='auth_dashboard:signin')
@require_POST
def admin_order_cancel(request, order_id):
    """Cancel an order"""
    order = get_object_or_404(Order, id=order_id)
    
    if order.order_status == 'cancelled':
        messages.warning(request, 'Order is already cancelled.')
        return redirect('orders:admin_order_detail', order_id=order_id)
    
    if not order.can_be_cancelled:
        messages.error(request, 'This order cannot be cancelled at this stage.')
        return redirect('orders:admin_order_detail', order_id=order_id)
    
    reason = request.POST.get('cancellation_reason', '').strip()
    
    # Update order status
    old_status = order.order_status
    order.order_status = 'cancelled'
    order.cancelled_at = timezone.now()
    
    # Update payment status if paid
    if order.payment_status == 'paid':
        order.payment_status = 'refunded'
    
    order.save()
    
    # Here you could:
    # 1. Create cancellation record
    # 2. Process refund if needed
    # 3. Send cancellation email
    # 4. Restock inventory
    
    messages.success(request, f'Order #{order.order_number} has been cancelled.')
    
    return redirect('orders:admin_order_detail', order_id=order_id)

# orders/views.py
@login_required(login_url='user_auth:signin')
@never_cache
def order_success(request, order_id=None):
    """Order success page"""
    context = {}
    
    if order_id:
        # Get the specific order if provided
        order = get_object_or_404(Order, id=order_id, user=request.user)
        context['order'] = order
        context['title'] = f'Order #{order.order_number} - Success'
    else:
        # Get the latest order for the user
        latest_order = Order.objects.filter(user=request.user).order_by('-created_at').first()
        if latest_order:
            context['order'] = latest_order
            context['title'] = f'Order #{latest_order.order_number} - Success'
    
    return render(request, 'user/orders/order_success.html', context)


@staff_member_required(login_url='auth_dashboard:signin')
def admin_order_export(request):
    """Export orders to CSV/Excel"""
    # You can implement export functionality here
    # Using django-import-export or pandas
    
    messages.info(request, 'Export functionality coming soon.')
    return redirect('orders:admin_order_list')