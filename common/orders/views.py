import os
import random
import string

from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST
from django.db.models import Q, Sum, Count, F
from django.utils.decorators import method_decorator
from datetime import datetime, timedelta
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.http import require_POST, require_http_methods
from django.http import HttpResponse
from django.template.loader import render_to_string

from io import BytesIO
from decimal import Decimal
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

from common.user.address.models import Address
from common.admin.transactions.models import AdminTransaction
from .models import Order, Coupon
from .forms import OrderStatusForm, ReturnRequestForm
from common.user.cart_wishlist.models import Cart, CartItem
from common.wallet.models import Wallet, Transaction

from core.services import (
    WalletService, 
    send_order_placed_email, 
    send_payment_success_email, 
    send_payment_failed_email
)
from core.razorpay_service import RazorpayService


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
    shipping_cost = Decimal(str(cart_items.count() * 20))  # 20 RS per order
    final_total = cart_total + tax_amount + shipping_cost
    
    # Check if COD is available (blocked for orders >= 1000)
    cod_available = final_total < Decimal('1000')
    
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
        'cod_available': cod_available,
        'available_coupons': [
            coupon for coupon in Coupon.objects.filter(
                is_active=True, 
                valid_from__lte=timezone.now(),
                valid_until__gte=timezone.now()
            ) if coupon.is_valid()[0] and coupon.can_be_used_by_user(request.user)[0]
        ]
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
    payment_failed = request.POST.get('payment_failed') == 'true'
    
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
    
    # Get coupon details if applied
    coupon_code = request.POST.get('coupon_code', '').strip()
    coupon_discount = Decimal(request.POST.get('coupon_discount', '0'))
    coupon_obj = None
    
    if coupon_code and coupon_discount > 0:
        try:
            coupon_obj = Coupon.objects.get(code=coupon_code.upper())
            # Verify coupon is still valid
            is_valid, message = coupon_obj.is_valid()
            if not is_valid:
                messages.warning(request, f'Coupon {coupon_code} is no longer valid: {message}')
                coupon_code = ''
                coupon_discount = Decimal('0')
                coupon_obj = None
        except Coupon.DoesNotExist:
            messages.warning(request, f'Coupon {coupon_code} not found')
            coupon_code = ''
            coupon_discount = Decimal('0')
            coupon_obj = None
    
    # Calculate tax on original cart total
    tax_amount = cart_total * Decimal('0.1')
    shipping_cost = Decimal(str(cart_items.count() * 20))
    
    # Calculate final total before coupon
    total_before_coupon = cart_total + tax_amount + shipping_cost
    
    # Apply coupon discount to final total
    final_total = total_before_coupon - coupon_discount
    if final_total < 0:
        final_total = Decimal('0')
    
    # Handle wallet payment
    if payment_method == 'wallet':
        if wallet.balance < final_total:
            messages.error(request, f'Insufficient wallet balance. You need ₹{final_total} but have only ₹{wallet.balance}.')
            return redirect('orders:checkout')
    
    # Create orders even if payment failed
    created_orders = []
    
    # Calculate discount per item proportionally
    total_items_price = sum(item.total_price for item in cart_items)
    
    for cart_item in cart_items:
        subtotal = cart_item.total_price
        
        # Apply proportional coupon discount to this item's share
        item_coupon_discount = Decimal('0')
        if coupon_discount > 0 and total_items_price > 0:
            item_coupon_discount = (subtotal / total_items_price) * coupon_discount
        
        # Tax remains on the full subtotal before coupon
        tax_amount_item = subtotal * Decimal('0.1')
        shipping_cost_item = Decimal('20.00')
        
        # Final amount for this item is (Subtotal + Tax + Shipping) - Coupon Discount
        item_total_before_coupon = subtotal + tax_amount_item + shipping_cost_item
        total_amount_item = item_total_before_coupon - item_coupon_discount
        if total_amount_item < 0:
            total_amount_item = Decimal('0')
        

        # Determine payment status
        if payment_failed:
            payment_status = 'failed'
        elif payment_method == 'wallet' and wallet.balance >= final_total:
            payment_status = 'paid'
        elif payment_method == 'razorpay' and razorpay_payment_id:
            payment_status = 'paid'  # Will be updated after verification
        elif payment_method == 'cash_on_delivery':
            payment_status = 'pending'
        else:
            payment_status = 'pending'
        
        # Create order
        order = Order(
            user=request.user,
            product=cart_item.variant.product,
            variant=cart_item.variant,
            quantity=cart_item.quantity,
            unit_price=cart_item.unit_price,  # Use discounted price
            subtotal=subtotal,
            tax_amount=tax_amount_item,
            shipping_cost=shipping_cost_item,
            total_amount=total_amount_item,
            payment_method=payment_method,
            shipping_address=shipping_address,
            order_status='pending',
            payment_status=payment_status,
            paid_at=timezone.now() if payment_status == 'paid' else None,
            razorpay_payment_id=razorpay_payment_id if payment_method == 'razorpay' else None,
            razorpay_order_id=razorpay_order_id if payment_method == 'razorpay' else None,
            payment_attempts=1 if payment_failed else 0,
            last_payment_attempt=timezone.now() if payment_failed else None,
            payment_failure_reason="Payment failed during checkout" if payment_failed else None,
            # Coupon fields
            coupon_code=coupon_code if coupon_code else None,
            coupon_discount=item_coupon_discount if coupon_code else Decimal('0'),
        )
        order.save()
        
        # Decrement stock quantity
        if order.variant:
            order.variant.stock_quantity -= order.quantity
            order.variant.save()
            
        created_orders.append(order)

    # Deactivate the cart
    cart.delete()
    
    # Send order confirmation email
    send_order_placed_email(request.user, created_orders)
    
    # Record coupon usage if coupon was applied
    if coupon_obj and created_orders:
        from .models import CouponUsage
        # Record one usage entry for the entire cart checkout
        CouponUsage.objects.create(
            coupon=coupon_obj,
            user=request.user,
            order=created_orders[0],  # Link to first order
            discount_amount=coupon_discount
        )
        # Increment coupon usage count
        coupon_obj.increment_usage()
    

    # If payment failed, redirect to payment failed page
    if payment_failed:
        send_payment_failed_email(request.user, created_orders, reason="Payment failed during checkout initial attempt")
        if len(created_orders) >= 1:
            return redirect('orders:payment_failed', order_id=created_orders[0].order_id)
    
    # Handle successful payment verification
    if payment_method == 'razorpay' and razorpay_payment_id:
        try:
            razorpay_service = RazorpayService()
            is_valid = razorpay_service.verify_payment(
                razorpay_payment_id,
                razorpay_order_id,
                razorpay_signature
            )
            
            if not is_valid:
                # Update all created orders to failed status
                for order in created_orders:
                    order.payment_status = 'failed'
                    order.payment_attempts += 1
                    order.last_payment_attempt = timezone.now()
                    order.payment_failure_reason = "Payment verification failed"
                    order.save()
                
                send_payment_failed_email(request.user, created_orders, reason="Payment verification failed")
                
                if len(created_orders) >= 1:
                    return redirect('orders:payment_failed', order_id=created_orders[0].order_id)
            
            # Create AdminTransaction for successful Razorpay payment
            for order in created_orders:
                AdminTransaction.objects.create(
                    order=order,
                    user=request.user,
                    description=f'{request.user.email} paid via Razorpay for order {order.order_number}',
                    amount=Decimal(order.total_amount),
                    payment_method='razorpay',
                    payment_status='completed',
                    payment_type='credit'
                )
            
            # Send success email
            send_payment_success_email(request.user, created_orders, payment_id=razorpay_payment_id, payment_method='Razorpay')
        except Exception as e:
            # Handle verification error
            for order in created_orders:
                order.payment_status = 'failed'
                order.payment_attempts += 1
                order.last_payment_attempt = timezone.now()
                order.payment_failure_reason = f"Payment verification error: {str(e)}"
                order.save()
            
            send_payment_failed_email(request.user, created_orders, reason=str(e))
            
            if len(created_orders) >= 1:
                return redirect('orders:payment_failed', order_id=created_orders[0].order_id)
    
    # Handle wallet payment
    if payment_method == 'wallet' and wallet.balance >= final_total:
        try:
            product_names = ", ".join([item.variant.product.name for item in cart_items])
            transaction_obj = WalletService.make_payment(
                wallet,
                final_total,
                f"Order payment for {product_names}."
            )
            transaction = AdminTransaction.objects.create(
                order=order,
                user=request.user,
                description=f'{request.user.email} place an order on {order.order_number}',
                amount=Decimal(order.total_amount),
                payment_method='wallet',
                payment_status='completed',
                payment_type='credit'
                )
            # Update all orders
            for order in created_orders:
                order.payment_status = 'paid'
                order.paid_at = timezone.now()
                order.save()
            
            send_payment_success_email(request.user, created_orders, payment_method='Wallet')
                
        except ValueError as e:
            for order in created_orders:
                order.payment_status = 'failed'
                order.payment_attempts += 1
                order.last_payment_attempt = timezone.now()
                order.payment_failure_reason = f"Wallet payment failed: {str(e)}"
                order.save()
            
            send_payment_failed_email(request.user, created_orders, reason=str(e))
            
            if len(created_orders) >= 1:
                return redirect('orders:payment_failed', order_id=created_orders[0].order_id)
    
    
    # Redirect based on number of orders
    if len(created_orders) == 1:
        if created_orders[0].payment_status in ['paid', 'pending']:
            messages.success(request, 'Order placed successfully!')
            return redirect('orders:order_success', order_id=created_orders[0].order_id)
        else:
            return redirect('orders:payment_failed', order_id=created_orders[0].order_id)
    else:
        messages.success(request, f'Order placed successfully! {len(created_orders)} individual order(s) created.')
        return redirect('orders:order_success', order_id=created_orders[0].order_id)
        
    

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
    
    # Pagination
    paginator = Paginator(orders, 8) # 8 orders per page
    page = request.GET.get('page')
    
    try:
        orders_page = paginator.page(page)
    except PageNotAnInteger:
        orders_page = paginator.page(1)
    except EmptyPage:
        orders_page = paginator.page(paginator.num_pages)
    
    # Calculate counts for summary cards (use original queryset or paginated? Requirements usually mean total counts)
    # Counts should be based on ALL user orders, not just the page.
    delivered_count = orders.filter(order_status='delivered').count()
    in_progress_count = orders.filter(
        order_status__in=['processing', 'shipped', 'pending']
    ).count()
    
    # Pagination
    paginator = Paginator(orders, 8) # 8 orders per page
    page = request.GET.get('page')
    
    try:
        orders_page = paginator.page(page)
    except PageNotAnInteger:
        orders_page = paginator.page(1)
    except EmptyPage:
        orders_page = paginator.page(paginator.num_pages)
    
    context = {
        'orders': orders_page,
        'page_obj': orders_page,
        'delivered_count': delivered_count,
        'in_progress_count': in_progress_count,
        'active_tab': 'orders',
        'CANCELLATION_REASON_CHOICES': Order.CANCELLATION_REASON_CHOICES
    }
    return render(request, 'user/orders/order_list.html', context)



@login_required(login_url='user_auth:signin')
@never_cache
@transaction.atomic
def cancel_order(request, order_id):
    """Cancel an order"""
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    wallet = get_object_or_404(Wallet, user=request.user)
    transaction = Transaction.objects.filter(wallet=wallet)


    
    if not order.can_be_cancelled:
        print(request, 'This order cannot be cancelled.')
        return redirect('orders:order_list')
    
    if order.payment_status == 'paid' and order.payment_method in ['razorpay', 'wallet']:
        
        order.order_status = 'cancelled'
        # wallet.balance += order.total_amount
        # transaction.create(
        #     wallet=wallet,
        #     transaction_type='refund',
        #     description=f'Your Refund for order #{order.order_number} has been credited on your wallet',
        #     amount=order.total_amount,
        #     status='refunded'
        # )
        
        # wallet.save()

        try:
            refund_amount = order.total_amount
            transaction_obj = WalletService.make_refund(
                wallet=wallet,
                amount=refund_amount,
                description=f"Refund for cancelled order #{order.order_number}"
            )
            
            # Create Admin Transaction for refund
            AdminTransaction.objects.create(
                order=order,
                user=order.user,
                description=f'Refund for cancelled order #{order.order_number}',
                amount=Decimal(refund_amount),
                payment_method='wallet',
                payment_status='completed',
                payment_type='debit'
            )
            
            # Update order status and payment status
            order.payment_status = 'refunded'
            
            messages.success(request, f'Return approved for order #{order.order_number}. ₹{refund_amount} has been refunded to customer wallet.')
            
        except ValueError as e:
            # Handle refund errors
            messages.error(request, f'Refund failed: {str(e)}')
            return redirect('orders:admin_view_return', order_id=order_id)
        except Exception as e:
            # Handle other errors
            messages.error(request, f'Error processing refund: {str(e)}')
            return redirect('orders:admin_view_return', order_id=order_id)

    # Ensure order is marked cancelled
    order.order_status = 'cancelled'
    if not order.cancelled_at:
        order.cancelled_at = timezone.now()
        
    # Save cancellation reason
    cancellation_reason = request.POST.get('cancellation_reason')
    cancellation_description = request.POST.get('cancellation_description', '').strip()
    if cancellation_reason:
        order.cancellation_reason = cancellation_reason
    if cancellation_description:
        order.cancellation_description = cancellation_description

    # Update payment status logic
    if order.payment_status == 'refunded':
        pass  # Already handled and refunded
    elif order.payment_method == 'cash_on_delivery':
        order.payment_status = 'pending'
    else:
        order.payment_status = 'failed'

    order.save()
    
    # Increment stock quantity back
    if order.variant:
        order.variant.stock_quantity += order.quantity
        order.variant.save()
    
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
    
    # Track applied filters for display
    applied_filters = []
    if search_query: applied_filters.append(f'Search: {search_query}')
    if order_status_filter: applied_filters.append(f'Order: {dict(Order.ORDER_STATUS_CHOICES).get(order_status_filter)}')
    if payment_status_filter: applied_filters.append(f'Payment: {dict(Order.PAYMENT_STATUS_CHOICES).get(payment_status_filter)}')
    if payment_method_filter: applied_filters.append(f'Method: {dict(Order.PAYMENT_METHOD_CHOICES).get(payment_method_filter)}')
    if date_filter: applied_filters.append(f'Time: {date_filter.title()}')
    if start_date and end_date: applied_filters.append(f'Range: {start_date} to {end_date}')
    if min_amount: applied_filters.append(f'Min: ₹{min_amount}')
    if max_amount: applied_filters.append(f'Max: ₹{max_amount}')

    # Calculate statistics
    total_orders = orders.count()
    total_revenue = orders.aggregate(total=Sum('total_amount'))['total'] or 0
    average_order_value = total_revenue / total_orders if total_orders > 0 else 0
    
    # Count by status
    status_counts = orders.values('order_status').annotate(count=Count('order_id'))
    status_stats = {item['order_status']: item['count'] for item in status_counts}
    
    # Payment status counts
    payment_counts = orders.values('payment_status').annotate(count=Count('order_id'))
    payment_stats = {item['payment_status']: item['count'] for item in payment_counts}
    
    # Pagination
    paginator = Paginator(orders, 8)
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
        'start_date': str(start_date) if start_date else '',
        'end_date': str(end_date) if end_date else '',
        'min_amount': min_amount,
        'max_amount': max_amount,
        'sort_by': sort_by,
        'applied_filters': applied_filters,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'average_order_value': average_order_value,
        'status_stats': status_stats,
        'payment_stats': payment_stats,
        'ORDER_STATUS_CHOICES': Order.ORDER_STATUS_CHOICES,
        'PAYMENT_STATUS_CHOICES': Order.PAYMENT_STATUS_CHOICES,
        'PAYMENT_METHOD_CHOICES': Order.PAYMENT_METHOD_CHOICES,
        'CANCELLATION_REASON_CHOICES': Order.CANCELLATION_REASON_CHOICES,
    }
    
    return render(request, 'admin/orders/order_list.html', context)


@staff_member_required(login_url='auth_dashboard:signin')
def admin_order_detail(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)
    
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
        'CANCELLATION_REASON_CHOICES': Order.CANCELLATION_REASON_CHOICES,
        'title': f'Order #{order.order_number}',
    }
    
    return render(request, 'admin/orders/order_detail.html', context)

@login_required
@require_POST
def create_razorpay_order(request):
    """Create Razorpay order for frontend"""
    try:
        import json
        
        # Get cart total
        cart = Cart.objects.filter(user=request.user, is_active=True).first()
        if not cart or not cart.items.exists():
            return JsonResponse({
                'success': False,
                'error': 'Cart is empty'
            })
        
        cart_items = cart.items.select_related('variant__product').all()
        cart_total = sum(item.total_price for item in cart_items)
        
        # Get coupon discount from request body
        try:
            data = json.loads(request.body)
            coupon_discount = Decimal(str(data.get('coupon_discount', 0)))
        except:
            coupon_discount = Decimal('0')
        
        # Calculate tax on original cart total
        tax_amount = cart_total * Decimal('0.1')
        shipping_cost = Decimal(str(cart_items.count() * 20))
        
        # Calculate final total before coupon
        total_before_coupon = cart_total + tax_amount + shipping_cost
        
        # Apply coupon discount to final total
        final_total = total_before_coupon - coupon_discount
        if final_total < 0:
            final_total = Decimal('0')
        

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
    order = get_object_or_404(Order, order_id=order_id)
    
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
    
    # Update order status
    order.order_status = new_status
    
    # Update timestamps based on status
    if new_status == 'delivered':
        order.delivered_at = timezone.now()  # SET DELIVERED_AT HERE
        
        # Auto-update payment status to 'paid' if it's not already
        if order.payment_status != 'paid':
            old_payment_status = order.payment_status
            order.payment_status = 'paid'
            order.paid_at = timezone.now()
            
            # Create AdminTransaction for payment confirmation
            AdminTransaction.objects.create(
                order=order,
                user=order.user,
                description=f'Payment auto-confirmed on delivery',
                amount=Decimal(order.total_amount),
                payment_method=order.payment_method,
                payment_status='completed',
                payment_type='credit'
            )
            messages.success(request, f'Order #{order.order_number} marked as delivered and payment status updated to paid.')
        else:
            messages.success(request, f'Order #{order.order_number} marked as delivered.')
    elif new_status == 'cancelled':
        order.cancelled_at = timezone.now()
    elif new_status == 'returned':
        order.returned_at = timezone.now()
    
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
                description=f"Refund for cancelled order #{order.order_number}"
            )
            
            AdminTransaction.objects.create(
                order=order,
                user=order.user,
                description=f'Refund for cancelled order #{order.order_number}',
                amount=Decimal(refund_amount),
                payment_method='wallet',
                payment_status='completed',
                payment_type='debit'
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

            AdminTransaction.objects.create(
                order=order,
                user=order.user,
                description=f'Refund for cancelled order #{order.order_number}',
                amount=Decimal(order.total_amount),
                payment_method='wallet',
                payment_status='completed',
                payment_type='debit'
            )
            
        except Exception as e:
            messages.error(request, f'Order cancelled but refund failed: {str(e)}')
            order.payment_status = 'paid'
    
    order.save()
    
    # Increment stock quantity back if cancelled
    if new_status == 'cancelled' and order.variant:
        order.variant.stock_quantity += order.quantity
        order.variant.save()
    
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
    order = get_object_or_404(Order, order_id=order_id)
    
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
    
    # Create AdminTransaction if status changed to paid
    if new_payment_status == 'paid' and old_payment_status != 'paid':
        AdminTransaction.objects.create(
            order=order,
            user=order.user,
            description=f'Payment confirmed manually by {request.user.email} (Admin)',
            amount=Decimal(order.total_amount),
            payment_method=order.payment_method,
            payment_status='completed',
            payment_type='credit'
        )
        
    # Handle refund if status changed to refunded
    elif new_payment_status == 'refunded' and old_payment_status != 'refunded':
        try:
            with transaction.atomic():
                # Get or create wallet
                wallet, created = Wallet.objects.get_or_create(user=order.user)
                
                refund_amount = order.total_amount
                
                # Process refund
                WalletService.make_refund(
                    wallet=wallet,
                    amount=refund_amount,
                    description=f"Manual refund by admin for order #{order.order_number}"
                )
                
                # Create AdminTransaction
                AdminTransaction.objects.create(
                    order=order,
                    user=order.user,
                    description=f'Refund processed manually by {request.user.email} (Admin)',
                    amount=Decimal(refund_amount),
                    payment_method='wallet',
                    payment_status='completed',
                    payment_type='debit'
                )
                messages.success(request, f'Refund of ₹{refund_amount} processed to user wallet.')
                
        except Exception as e:
            # Revert status change if refund fails
            order.payment_status = old_payment_status
            order.save()
            messages.error(request, f'Failed to process refund: {str(e)}')
            return redirect('orders:admin_order_detail', order_id=order_id)
    
    messages.success(request, f'Payment status updated from {old_payment_status} to {new_payment_status}.')
    
    return redirect('orders:admin_order_detail', order_id=order_id)


@staff_member_required(login_url='auth_dashboard:signin')
@require_POST
def admin_order_cancel(request, order_id):
    """Cancel an order"""
    order = get_object_or_404(Order, order_id=order_id)
    
    if order.order_status == 'cancelled':
        messages.warning(request, 'Order is already cancelled.')
        return redirect('orders:admin_order_detail', order_id=order_id)
    
    if not order.can_be_cancelled:
        messages.error(request, 'This order cannot be cancelled at this stage.')
        return redirect('orders:admin_order_detail', order_id=order_id)
    
    reason = request.POST.get('cancellation_reason', '').strip()
    description = request.POST.get('cancellation_description', '').strip()
    
    # Update order status
    old_status = order.order_status
    order.order_status = 'cancelled'
    order.cancelled_at = timezone.now()
    if reason:
        order.cancellation_reason = reason
    if description:
        order.cancellation_description = description
    
    # Update payment status if paid
    if order.payment_status == 'paid':
        order.payment_status = 'refunded'
    
    order.save()
    
    # Increment stock quantity back
    if order.variant:
        order.variant.stock_quantity += order.quantity
        order.variant.save()
    
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
        order = get_object_or_404(Order, order_id=order_id, user=request.user)
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



@login_required
@never_cache
@require_http_methods(["GET", "POST"])
def request_return(request, order_id):
    """User requests a return for a delivered product"""
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    
    # Check if order can be returned
    if not order.can_be_returned:
        messages.error(request, 'This order cannot be returned. Return window may have expired or order is not delivered.')
        return redirect('orders:order_detail', order_id=order_id)
    
    if request.method == 'POST':
        form = ReturnRequestForm(request.POST, request.FILES, instance=order)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    order = form.save(commit=False)
                    
                    # Store uploaded images if any
                    images = []
                    if 'return_images' in request.FILES:
                        from django.core.files.storage import default_storage
                        for image in request.FILES.getlist('return_images'):
                            # Save image to storage
                            file_path = default_storage.save(
                                f'returns/{order.order_number}/{image.name}',
                                image
                            )
                            images.append(default_storage.url(file_path))
                    
                    if images:
                        order.return_images = images
                    
                    # Update order status
                    order.order_status = 'return_requested'
                    order.return_requested_at = timezone.now()
                    order.payment_status = 'refund_pending'
                    order.save()
                    
                    # Send notification to admin (you can implement this)
                    # send_return_notification_to_admin(order)
                    
                    messages.success(request, 'Return request submitted successfully! We will review your request and get back to you within 3-5 business days.')
                    
                    # Send email notification to user
                    # send_return_request_email(order.user.email, order)
                    
                    return redirect('orders:order_detail', order_id=order_id)
                    
            except Exception as e:
                messages.error(request, f'Error submitting return request: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ReturnRequestForm(instance=order)
    
    context = {
        'order': order,
        'form': form,
        'return_reasons': Order.RETURN_REASON_CHOICES,
    }
    
    return render(request, 'user/orders/request_return.html', context)

@staff_member_required
@require_http_methods(["GET", "POST"])
def admin_approve_return(request, order_id):
    """Admin approves a return request and processes refund to wallet"""
    order = get_object_or_404(Order, order_id=order_id)
    
    # Check if this is a valid return request
    if order.order_status != 'return_requested':
        messages.error(request, 'This order does not have a pending return request.')
        return redirect('orders:admin_order_detail', order_id=order_id)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Get or create user's wallet
                wallet, created = Wallet.objects.get_or_create(user=order.user)
                
                # Calculate refund amount
                refund_amount = order.total_amount
                
                # Check if already refunded to avoid double refund
                if order.payment_status != 'refunded':
                    # Process refund immediately
                    transaction_record = WalletService.make_refund(
                        wallet=wallet,
                        amount=refund_amount,
                        description=f"Refund for return order #{order.order_number}"
                    )
                    
                    # Log AdminTransaction
                    AdminTransaction.objects.create(
                        order=order,
                        user=order.user,
                        description=f'Refund processed upon return approval by {request.user.email} (Admin)',
                        amount=Decimal(refund_amount),
                        payment_method='wallet',
                        payment_status='completed',
                        payment_type='debit'
                    )
                    
                    # Update order payment status
                    order.payment_status = 'refunded'
                
                # Update order status
                order.order_status = 'return_approved'
                order.return_approved_at = timezone.now()
                
                # Save order
                order.save()
                
                messages.success(request, f'Return approved for order #{order.order_number}. Refunds of ₹{refund_amount} processed to wallet.')
                
                # Log the approval
                print(f"Return approved and refunded for order #{order.order_number}.")
                
                return redirect('orders:admin_view_return', order_id=order_id)
                
        except Exception as e:
            messages.error(request, f'Error approving return: {str(e)}')
            return redirect('orders:admin_view_return', order_id=order_id)
    
    # For GET request, show approval form
    context = {
        'order': order,
        'title': f'Approve Return - Order #{order.order_number}',
        'refund_amount': order.total_amount,
    }
    
    return render(request, 'admin/orders/approve_return.html', context)


@staff_member_required
@require_http_methods(["GET", "POST"])
def admin_reject_return(request, order_id):
    """Admin rejects a return request"""
    order = get_object_or_404(Order, order_id=order_id)
    
    if order.order_status != 'return_requested':
        messages.error(request, 'This order does not have a pending return request.')
        return redirect('orders:admin_order_detail', order_id=order_id)
    
    if request.method == 'POST':
        rejection_reason = request.POST.get('rejection_reason', '').strip()
        
        if not rejection_reason:
            messages.error(request, 'Please provide a reason for rejecting the return.')
            return redirect('orders:admin_order_detail', order_id=order_id)
        
        try:
            with transaction.atomic():
                # Update order status
                order.order_status = 'return_rejected'
                order.return_rejected_at = timezone.now()
                order.return_rejection_reason = rejection_reason
                order.payment_status = 'paid'  # Reset payment status
                order.save()
                
                # Send notification to user about rejected return
                # send_return_rejected_email(order.user.email, order, rejection_reason)
                
                messages.success(request, f'Return rejected for order #{order.order_number}. User has been notified.')
                
                return redirect('orders:admin_order_detail', order_id=order_id)
                
        except Exception as e:
            messages.error(request, f'Error rejecting return: {str(e)}')
    
    context = {
        'order': order,
        'title': f'Reject Return - Order #{order.order_number}',
    }
    
    return render(request, 'admin/orders/reject_return.html', context)

@staff_member_required
@require_POST
def admin_complete_return(request, order_id):
    """Admin marks return as completed and processes refund"""
    order = get_object_or_404(Order, order_id=order_id)
    
    if order.order_status != 'return_approved':
        messages.error(request, 'This order is not approved for return.')
        return redirect('orders:admin_order_detail', order_id=order_id)
    
    try:
        with transaction.atomic():
            # Fallback: Check if refund is pending (e.g. legacy orders or failed refunds)
            if order.payment_status != 'refunded':
                 # Get or create user's wallet
                wallet, created = Wallet.objects.get_or_create(user=order.user)
                
                # Process refund
                WalletService.make_refund(
                    wallet=wallet,
                    amount=order.total_amount,
                    description=f"Refund for return order #{order.order_number}"
                )
                
                # Log AdminTransaction
                AdminTransaction.objects.create(
                    order=order,
                    user=order.user,
                    description=f'Refund processed upon return completion by {request.user.email} (Admin)',
                    amount=Decimal(order.total_amount),
                    payment_method='wallet',
                    payment_status='completed',
                    payment_type='debit'
                )
                
                order.payment_status = 'refunded'
                messages.success(request, f'Refund of ₹{order.total_amount} processed to wallet.')

            # Update order status
            order.order_status = 'returned'
            order.returned_at = timezone.now()
            order.save()
            
            messages.success(request, f'Return marked as completed for order #{order.order_number}.')
            
            # Restock product variant
            if order.variant:
                order.variant.stock_quantity += order.quantity
                order.variant.save()
            
            # Send notification to user about completed return
            # send_return_completed_email(order.user.email, order)
            
            return redirect('orders:admin_order_detail', order_id=order_id)
            
    except Exception as e:
        messages.error(request, f'Error completing return: {str(e)}')
        return redirect('orders:admin_order_detail', order_id=order_id)
    
# Add these imports at the top
from django.core.paginator import Paginator

# Add these admin return management views
@staff_member_required(login_url='auth_dashboard:signin')
def admin_return_requests(request):
    """Admin view for pending return requests"""
    # FIXED: Get pending return requests (orders with return_requested_at but not approved/rejected)
    pending_returns = Order.objects.filter(
        return_requested_at__isnull=False,  # Has return request
        return_approved_at__isnull=True,    # Not approved yet
        return_rejected_at__isnull=True     # Not rejected yet
    ).select_related('user', 'product', 'shipping_address').order_by('-return_requested_at')
    
    # Get counts for stats
    pending_count = pending_returns.count()
    approved_count = Order.objects.filter(return_approved_at__isnull=False).count()
    rejected_count = Order.objects.filter(return_rejected_at__isnull=False).count()
    
    # Get total refunds (only refunded orders)
    total_refunds = Order.objects.filter(payment_status='refunded').aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    # FIXED: Get recently processed returns (last 5 approved OR rejected)
    recent_returns = Order.objects.filter(
        Q(return_approved_at__isnull=False) | Q(return_rejected_at__isnull=False)
    ).select_related('user', 'product').order_by('-updated_at')[:5]
    
    context = {
        'return_requests': pending_returns,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'total_refunds': total_refunds,
        'recent_returns': recent_returns,
    }
    
    return render(request, 'admin/orders/return_requests.html', context)

@staff_member_required(login_url='auth_dashboard:signin')
def admin_approved_returns(request):
    """Admin view for approved returns"""
    # Get approved returns
    approved_returns = Order.objects.filter(
        return_approved_at__isnull=False
    ).select_related('user', 'product').order_by('-return_approved_at')
    
    # Get counts for stats
    approved_count = approved_returns.count()
    pending_refund_count = approved_returns.filter(payment_status='refund_pending').count()
    
    # Get total refunded amount
    total_refunded = approved_returns.filter(payment_status='refunded').aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    # Pagination
    paginator = Paginator(approved_returns, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'approved_returns': page_obj,
        'approved_count': approved_count,
        'pending_refund_count': pending_refund_count,
        'total_refunded': total_refunded,
    }
    
    return render(request, 'admin/orders/approved_returns.html', context)

@staff_member_required(login_url='auth_dashboard:signin')
def admin_rejected_returns(request):
    """Admin view for rejected returns"""
    # Get rejected returns
    rejected_returns = Order.objects.filter(
        return_rejected_at__isnull=False
    ).select_related('user', 'product').order_by('-return_rejected_at')
    
    # Get counts for stats
    rejected_count = rejected_returns.count()
    
    # Get this month's rejected returns
    from django.utils import timezone
    from datetime import datetime, timedelta
    
    today = timezone.now()
    first_day_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    this_month_count = rejected_returns.filter(
        return_rejected_at__gte=first_day_of_month
    ).count()
    
    # Calculate saved amount (total amount of rejected returns)
    saved_amount = rejected_returns.aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    # Pagination
    paginator = Paginator(rejected_returns, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'rejected_returns': page_obj,
        'rejected_count': rejected_count,
        'this_month_count': this_month_count,
        'saved_amount': saved_amount,
    }
    
    return render(request, 'admin/orders/rejected_returns.html', context)

@staff_member_required(login_url='auth_dashboard:signin')
def admin_view_return(request, order_id):
    """Admin view for detailed return information"""
    order = get_object_or_404(Order, order_id=order_id)
    
    context = {
        'order': order,
        'title': f'Return Details - Order #{order.order_number}',
    }
    
    return render(request, 'admin/orders/view_return.html', context)

# Update the order_detail view to include return options
@login_required(login_url='user_auth:signin')
@never_cache
def order_detail(request, order_id):
    """Display order details"""
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    
    context = {
        'order': order,
        'can_return': order.can_be_returned,
        'is_return_requested': order.is_return_requested,
        'is_return_approved': order.is_return_approved,
        'is_return_rejected': order.is_return_rejected,
        'CANCELLATION_REASON_CHOICES': Order.CANCELLATION_REASON_CHOICES
    }
    return render(request, 'user/orders/order_details.html', context)

@login_required
def track_order(request, order_id):
    """Track order status with timeline"""
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    
    # Define order status flow
    status_flow = [
        {
            'status': 'pending',
            'label': 'Order Placed',
            'icon': 'fa-shopping-cart',
            'description': 'Your order has been placed successfully',
            'date': order.created_at if order.order_status in ['pending', 'confirmed', 'processing', 'shipped', 'delivered'] else None,
        },
        {
            'status': 'confirmed',
            'label': 'Order Confirmed',
            'icon': 'fa-check-circle',
            'description': 'Your order has been confirmed and is being prepared',
            'date': order.created_at if order.order_status in ['confirmed', 'processing', 'shipped', 'delivered'] else None,
        },
        {
            'status': 'processing',
            'label': 'Processing',
            'icon': 'fa-cog',
            'description': 'Your order is being processed and packed',
            'date': order.created_at if order.order_status in ['processing', 'shipped', 'delivered'] else None,
        },
        {
            'status': 'shipped',
            'label': 'Shipped',
            'icon': 'fa-shipping-fast',
            'description': 'Your order has been shipped and is on the way',
            'date': order.created_at if order.order_status in ['shipped', 'delivered'] else None,
        },
        {
            'status': 'delivered',
            'label': 'Delivered',
            'icon': 'fa-box-open',
            'description': 'Your order has been delivered successfully',
            'date': order.delivered_at if order.order_status == 'delivered' else None,
        },
    ]
    
    # Mark completed statuses
    status_order = ['pending', 'confirmed', 'processing', 'shipped', 'delivered']
    try:
        current_index = status_order.index(order.order_status)
        for i, status_item in enumerate(status_flow):
            status_item['completed'] = i <= current_index
            status_item['current'] = i == current_index
    except ValueError:
        # Handle cancelled or returned orders
        for status_item in status_flow:
            status_item['completed'] = False
            status_item['current'] = False
    
    # Calculate estimated delivery
    estimated_delivery = None
    if order.order_status in ['confirmed', 'processing', 'shipped']:
        from datetime import timedelta
        estimated_delivery = order.created_at + timedelta(days=7)
    
    context = {
        'order': order,
        'status_flow': status_flow,
        'estimated_delivery': estimated_delivery,
        'is_cancelled': order.order_status == 'cancelled',
        'is_returned': order.order_status == 'returned',
    }
    
    return render(request, 'user/orders/track_order.html', context)



@login_required
def download_invoice(request, order_id):
    """Generate and download PDF invoice using HTML template"""
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    
    # Prepare context data
    context = {
        'order': order,
        'invoice_date': timezone.now(),
        'user': request.user,
        'settings': settings,
    }
    
    # Render HTML template
    html_string = render_to_string('user/orders/invoice_pdf.html', context)
    
    # Create PDF
    font_config = FontConfiguration()
    
    # You can add custom CSS if needed
    css_string = """
    @page {
        size: A4;
        margin: 1.5cm;
        @bottom-center {
            content: "Page " counter(page) " of " counter(pages);
            font-size: 10px;
            color: #666;
        }
    }
    """
    
    html = HTML(string=html_string)
    
    # Generate PDF
    pdf_file = html.write_pdf(
        stylesheets=[CSS(string=css_string)],
        font_config=font_config
    )
    
    # Create HTTP response
    response = HttpResponse(pdf_file, content_type='application/pdf')
    filename = f'invoice_{order.order_number}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.pdf'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response

# orders/views.py



# Simple receipt version
@login_required
def download_receipt(request, order_id):
    """Generate and download simple receipt"""
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    
    context = {
        'order': order,
        'invoice_date': timezone.now(),
        'user': request.user,
    }
    
    html_string = render_to_string('orders/receipt_pdf.html', context)
    html = HTML(string=html_string)
    pdf_file = html.write_pdf()
    
    response = HttpResponse(pdf_file, content_type='application/pdf')
    filename = f'receipt_{order.order_number}_{timezone.now().strftime("%Y%m%d")}.pdf'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


# Admin version
from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def admin_download_invoice(request, order_id):
    """Generate invoice for admin (any order)"""
    order = get_object_or_404(Order, order_id=order_id)
    
    context = {
        'order': order,
        'invoice_date': timezone.now(),
        'is_admin': True,
        'generated_by': request.user.get_full_name(),
    }
    
    html_string = render_to_string('user/orders/invoice_pdf.html', context)
    html = HTML(string=html_string)
    pdf_file = html.write_pdf()
    
    response = HttpResponse(pdf_file, content_type='application/pdf')
    filename = f'admin_invoice_{order.order_number}_{timezone.now().strftime("%Y%m%d")}.pdf'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response

# orders/views.py
@login_required(login_url='user_auth:signin')
@never_cache
def payment_failed(request, order_id):
    """Display payment failed page with retry options"""
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    
    # Get related orders if this was part of a multi-order checkout
    related_orders = Order.objects.filter(
        user=request.user,
        created_at__gte=order.created_at - timedelta(minutes=5),
        payment_status='failed'
    ).exclude(order_id=order.order_id)
    
    context = {
        'order': order,
        'related_orders': related_orders,
    }
    
    return render(request, 'user/orders/payment_failed.html', context)


@login_required(login_url='user_auth:signin')
@require_POST
@transaction.atomic
def retry_payment(request, order_id):
    """Retry payment for a failed order - simplified version"""
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    
    # Check if payment can be retried (always allow if failed)
    if order.payment_status != 'failed':
        messages.error(request, 'Payment cannot be retried at this time.')
        return redirect('orders:order_detail', order_id=order.order_id)
    
    # Update payment attempts
    order.payment_attempts += 1
    order.last_payment_attempt = timezone.now()
    
    # Handle different payment methods
    if order.payment_method == 'razorpay':
        # Create a new Razorpay order for retry
        try:
            razorpay_service = RazorpayService()
            
            # Generate a unique receipt for retry
            receipt = f"retry_{order.order_number}_{int(timezone.now().timestamp())}"
            
            # Create new Razorpay order
            razorpay_order = razorpay_service.create_order(
                amount=float(order.total_amount),
                receipt=receipt
            )
            
            # Save the new Razorpay order ID
            order.razorpay_order_id = razorpay_order['id']
            order.save()
            
            return JsonResponse({
                'success': True,
                'order_id': razorpay_order['id'],
                'amount': razorpay_order['amount'],
                'currency': razorpay_order['currency'],
                'key_id': settings.RAZORPAY_KEY_ID,
                'receipt': razorpay_order['receipt'],
                'user_name': request.user.get_full_name() or request.user.username,
                'user_email': request.user.email,
                'user_contact': request.user.phone_number or '',
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    elif order.payment_method == 'wallet':
        # Check wallet balance
        wallet = Wallet.objects.get(user=request.user)
        if wallet.balance >= order.total_amount:
            try:
                transaction_obj = WalletService.make_payment(
                    wallet,
                    order.total_amount,
                    f"Retry payment for order #{order.order_number}"
                )
                order.payment_status = 'paid'
                order.paid_at = timezone.now()
                order.save()
                
                AdminTransaction.objects.create(
                    order=order,
                    user=order.user,
                    description=f'Retry payment via Wallet for order #{order.order_number}',
                    amount=Decimal(order.total_amount),
                    payment_method='wallet',
                    payment_status='completed',
                    payment_type='credit'
                )
                
                messages.success(request, f'Payment successful! Order #{order.order_number} has been confirmed.')
                return redirect('orders:order_success', order_id=order.order_id)
            except Exception as e:
                messages.error(request, f'Wallet payment failed: {str(e)}')
                # Update failure reason
                order.payment_failure_reason = f"Wallet payment failed: {str(e)}"
                order.save()
                return redirect('orders:order_detail', order_id=order.order_id)
        else:
            messages.error(request, 'Insufficient wallet balance. Please add funds to your wallet.')
            order.payment_failure_reason = "Insufficient wallet balance"
            order.save()
            return redirect('orders:order_detail', order_id=order.order_id)
    
    order.save()
    return redirect('orders:order_detail', order_id=order.order_id)

@login_required(login_url='user_auth:signin')
@require_POST
@transaction.atomic
def verify_retry_payment(request, order_id):
    """Verify Razorpay payment after successful retry"""
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    
    # Get Razorpay payment details from POST data
    razorpay_payment_id = request.POST.get('razorpay_payment_id')
    razorpay_order_id = request.POST.get('razorpay_order_id')
    razorpay_signature = request.POST.get('razorpay_signature')
    
    if not all([razorpay_payment_id, razorpay_order_id, razorpay_signature]):
        messages.error(request, 'Invalid payment details.')
        return redirect('orders:payment_failed', order_id=order.order_id)
    
    try:
        # Verify the payment
        razorpay_service = RazorpayService()
        is_valid = razorpay_service.verify_payment(
            razorpay_payment_id,
            razorpay_order_id,
            razorpay_signature
        )
        
        if is_valid:
            # Payment successful - update order
            order.payment_status = 'paid'
            order.paid_at = timezone.now()
            order.razorpay_payment_id = razorpay_payment_id
            order.razorpay_order_id = razorpay_order_id
            order.razorpay_signature = razorpay_signature
            order.payment_failure_reason = None  # Clear failure reason
            order.save()
            
            AdminTransaction.objects.create(
                order=order,
                user=order.user,
                description=f'Retry payment via Razorpay for order #{order.order_number}',
                amount=Decimal(order.total_amount),
                payment_method='razorpay',
                payment_status='completed',
                payment_type='credit'
            )
            
            messages.success(request, f'Payment successful! Order #{order.order_number} has been confirmed.')
            return redirect('orders:order_success', order_id=order.order_id)
        else:
            # Payment verification failed
            order.payment_failure_reason = "Payment verification failed"
            order.save()
            
            messages.error(request, 'Payment verification failed. Please try again.')
            return redirect('orders:payment_failed', order_id=order.order_id)
            
    except Exception as e:
        # Handle verification error
        order.payment_failure_reason = f"Payment verification error: {str(e)}"
        order.save()
        
        messages.error(request, f'Payment verification error: {str(e)}')
        return redirect('orders:payment_failed', order_id=order.order_id)


@login_required(login_url='user_auth:signin')
@require_POST
def retry_razorpay_payment(request, order_id):
    """Create Razorpay order for retry payment"""
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    
    try:
        razorpay_service = RazorpayService()
        
        # Generate a unique receipt for retry
        receipt = f"retry_{order.order_number}_{int(timezone.now().timestamp())}"
        
        # Create new Razorpay order
        razorpay_order = razorpay_service.create_order(
            amount=float(order.total_amount),
            receipt=receipt
        )
        
        return JsonResponse({
            'success': True,
            'order_id': razorpay_order['id'],
            'amount': razorpay_order['amount'],
            'currency': razorpay_order['currency'],
            'key_id': settings.RAZORPAY_KEY_ID,
            'receipt': razorpay_order['receipt'],
            'user_name': request.user.get_full_name() or request.user.username,
            'user_email': request.user.email,
            'user_contact': request.user.phone_number or '',
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


# ============================================
# COUPON MANAGEMENT VIEWS
# ============================================

@staff_member_required(login_url='auth_dashboard:signin')
@never_cache
def coupon_list(request):
    """List all coupons with search and filters"""
    from .models import Coupon
    
    coupons = Coupon.objects.all().order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        coupons = coupons.filter(
            Q(code__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        coupons = coupons.filter(is_active=True)
    elif status_filter == 'inactive':
        coupons = coupons.filter(is_active=False)
    elif status_filter == 'expired':
        coupons = coupons.filter(valid_until__lt=timezone.now())
    elif status_filter == 'upcoming':
        coupons = coupons.filter(valid_from__gt=timezone.now())
    
    # Pagination
    paginator = Paginator(coupons, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    total_coupons = Coupon.objects.count()
    active_coupons = Coupon.objects.filter(is_active=True).count()
    expired_coupons = Coupon.objects.filter(valid_until__lt=timezone.now()).count()
    
    context = {
        'page_obj': page_obj,
        'coupons': page_obj,
        'total_coupons': total_coupons,
        'active_coupons': active_coupons,
        'expired_coupons': expired_coupons,
        'search_query': search_query,
        'status_filter': status_filter,
    }
    
    return render(request, 'admin/coupons/coupon_list.html', context)


@staff_member_required(login_url='auth_dashboard:signin')
@never_cache
def coupon_create(request):
    """Create a new coupon"""
    from .models import Coupon
    
    if request.method == 'POST':
        try:
            from datetime import datetime, time
            
            # Parse and validate dates
            valid_from_str = request.POST.get('valid_from')
            valid_until_str = request.POST.get('valid_until')
            
            if not valid_from_str or not valid_until_str:
                messages.error(request, 'Both validity dates are required.')
                return redirect('orders:coupon_create')
            
            # Parse dates (they come as 'YYYY-MM-DD' from date input)
            valid_from_date = datetime.strptime(valid_from_str, '%Y-%m-%d').date()
            valid_until_date = datetime.strptime(valid_until_str, '%Y-%m-%d').date()
            
            # Validate date range
            if valid_until_date < valid_from_date:
                messages.error(request, 'End date cannot be before start date.')
                return redirect('orders:coupon_create')
            
            # Convert to datetime with start/end of day
            valid_from = datetime.combine(valid_from_date, time.min)  # 00:00:00
            valid_until = datetime.combine(valid_until_date, time.max)  # 23:59:59
            
            # Make timezone-aware if USE_TZ is True
            if timezone.is_naive(valid_from):
                valid_from = timezone.make_aware(valid_from)
            if timezone.is_naive(valid_until):
                valid_until = timezone.make_aware(valid_until)
            
            coupon = Coupon(
                code=request.POST.get('code').strip().upper(),
                description=request.POST.get('description', '').strip(),
                discount_percentage=request.POST.get('discount_percentage'),
                max_uses=request.POST.get('max_uses', 0),
                max_uses_per_user=request.POST.get('max_uses_per_user', 1),
                minimum_order_amount=request.POST.get('minimum_order_amount', 0),
                max_discount_amount=request.POST.get('max_discount_amount') or None,
                valid_from=valid_from,
                valid_until=valid_until,
                is_active=request.POST.get('is_active') == 'on',
                created_by=request.user
            )
            coupon.save()
            
            messages.success(request, f'Coupon "{coupon.code}" created successfully!')
            return redirect('orders:coupon_list')
            
        except ValueError as e:
            messages.error(request, f'Invalid date format: {str(e)}')
        except Exception as e:
            messages.error(request, f'Error creating coupon: {str(e)}')
    
    context = {
        'title': 'Create New Coupon',
        'now': timezone.now().strftime('%Y-%m-%dT%H:%M'),
    }
    
    return render(request, 'admin/coupons/coupon_form.html', context)


@staff_member_required(login_url='auth_dashboard:signin')
@never_cache
def coupon_edit(request, coupon_id):
    """Edit an existing coupon"""
    from .models import Coupon
    
    coupon = get_object_or_404(Coupon, id=coupon_id)
    
    if request.method == 'POST':
        try:
            from datetime import datetime, time
            
            # Parse and validate dates
            valid_from_str = request.POST.get('valid_from')
            valid_until_str = request.POST.get('valid_until')
            
            if not valid_from_str or not valid_until_str:
                messages.error(request, 'Both validity dates are required.')
                return redirect('orders:coupon_edit', coupon_id=coupon.id)
            
            # Parse dates (they come as 'YYYY-MM-DD' from date input)
            valid_from_date = datetime.strptime(valid_from_str, '%Y-%m-%d').date()
            valid_until_date = datetime.strptime(valid_until_str, '%Y-%m-%d').date()
            
            # Validate date range
            if valid_until_date < valid_from_date:
                messages.error(request, 'End date cannot be before start date.')
                return redirect('orders:coupon_edit', coupon_id=coupon.id)
            
            # Convert to datetime with start/end of day
            valid_from = datetime.combine(valid_from_date, time.min)  # 00:00:00
            valid_until = datetime.combine(valid_until_date, time.max)  # 23:59:59
            
            # Make timezone-aware if USE_TZ is True
            if timezone.is_naive(valid_from):
                valid_from = timezone.make_aware(valid_from)
            if timezone.is_naive(valid_until):
                valid_until = timezone.make_aware(valid_until)
            
            coupon.code = request.POST.get('code').strip().upper()
            coupon.description = request.POST.get('description', '').strip()
            coupon.discount_percentage = request.POST.get('discount_percentage')
            coupon.max_uses = request.POST.get('max_uses', 0)
            coupon.max_uses_per_user = request.POST.get('max_uses_per_user', 1)
            coupon.minimum_order_amount = request.POST.get('minimum_order_amount', 0)
            coupon.max_discount_amount = request.POST.get('max_discount_amount') or None
            coupon.valid_from = valid_from
            coupon.valid_until = valid_until
            coupon.is_active = request.POST.get('is_active') == 'on'
            coupon.save()
            
            messages.success(request, f'Coupon "{coupon.code}" updated successfully!')
            return redirect('orders:coupon_list')
            
        except ValueError as e:
            messages.error(request, f'Invalid date format: {str(e)}')
        except Exception as e:
            messages.error(request, f'Error updating coupon: {str(e)}')
    
    context = {
        'title': 'Edit Coupon',
        'coupon': coupon,
        'now': timezone.now().strftime('%Y-%m-%dT%H:%M'),
    }
    
    return render(request, 'admin/coupons/coupon_form.html', context)


@staff_member_required(login_url='auth_dashboard:signin')
@never_cache
def coupon_delete(request, coupon_id):
    """Delete a coupon"""
    from .models import Coupon
    
    coupon = get_object_or_404(Coupon, id=coupon_id)
    
    if request.method == 'POST':
        code = coupon.code
        coupon.delete()
        messages.success(request, f'Coupon "{code}" deleted successfully!')
        return redirect('orders:coupon_list')
    
    context = {
        'coupon': coupon,
    }
    
    return render(request, 'admin/coupons/coupon_confirm_delete.html', context)


@staff_member_required(login_url='auth_dashboard:signin')
@never_cache
def coupon_toggle_active(request, coupon_id):
    """Toggle coupon active status"""
    from .models import Coupon
    
    coupon = get_object_or_404(Coupon, id=coupon_id)
    
    if request.method == 'POST':
        coupon.is_active = not coupon.is_active
        coupon.save()
        
        status = "activated" if coupon.is_active else "deactivated"
        messages.success(request, f'Coupon "{coupon.code}" {status} successfully!')
    
    return redirect('orders:coupon_list')


@staff_member_required(login_url='auth_dashboard:signin')
@never_cache
def coupon_usage_list(request):
    """List all coupon usages"""
    from .models import CouponUsage
    
    usages = CouponUsage.objects.all().select_related('coupon', 'user', 'order').order_by('-used_at')
    
    # Filter by coupon
    coupon_filter = request.GET.get('coupon', '')
    if coupon_filter:
        usages = usages.filter(coupon__code__icontains=coupon_filter)
    
    # Pagination
    paginator = Paginator(usages, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics for dashboard
    from django.db.models import Sum
    total_usages = usages.count()
    total_savings = usages.aggregate(total=Sum('discount_amount'))['total'] or 0
    unique_users = usages.values('user').distinct().count()
    
    context = {
        'page_obj': page_obj,
        'usages': page_obj,
        'coupon_filter': coupon_filter,
        'total_usages': total_usages,
        'total_savings': total_savings,
        'unique_users': unique_users,
    }
    
    return render(request, 'admin/coupons/coupon_usage_list.html', context)


# ============================================
# COUPON VALIDATION API (For Checkout)
# ============================================

@login_required(login_url='user_auth:signin')
@require_POST
def validate_coupon(request):
    """
    Validate and apply coupon code for checkout
    """
    try:
        import json
        from .models import Coupon
        from decimal import Decimal
        
        data = json.loads(request.body)
        coupon_code = data.get('coupon_code', '').strip().upper()
        order_amount = Decimal(str(data.get('order_amount', 0)))
        
        if not coupon_code:
            return JsonResponse({
                'success': False,
                'message': 'Please enter a coupon code'
            })
        
        # Get coupon
        try:
            coupon = Coupon.objects.get(code=coupon_code)
        except Coupon.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Invalid coupon code'
            })
        
        # Check if coupon is valid
        is_valid, message = coupon.is_valid()
        if not is_valid:
            return JsonResponse({
                'success': False,
                'message': message
            })
        
        # Check if user can use this coupon
        can_use, message = coupon.can_be_used_by_user(request.user)
        if not can_use:
            return JsonResponse({
                'success': False,
                'message': message
            })
        
        # Check minimum order amount
        if order_amount < coupon.minimum_order_amount:
            return JsonResponse({
                'success': False,
                'message': f'Minimum order amount of ₹{coupon.minimum_order_amount} required'
            })
        
        # Calculate discount
        discount_amount = coupon.calculate_discount(order_amount)
        new_total = order_amount - discount_amount
        
        return JsonResponse({
            'success': True,
            'message': f'Coupon "{coupon.code}" applied successfully!',
            'coupon_code': coupon.code,
            'discount_percentage': float(coupon.discount_percentage),
            'discount_amount': float(discount_amount),
            'original_amount': float(order_amount),
            'new_total': float(new_total)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)