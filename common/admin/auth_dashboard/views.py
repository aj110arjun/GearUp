from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.contrib.auth import logout
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count, F, FloatField, ExpressionWrapper
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models.functions import TruncDate, TruncMonth, TruncYear

from datetime import timedelta, datetime

from common.user.auths.models import UserModel
from common.orders.models import Order
from common.products.models import Product, Category
from common.admin.auth_dashboard.sales_report import generate_report_response

from .forms import AdminSigninForm
from core.services import get_login_redirect_url

@never_cache
def admin_signin(request):
    # Only redirect if already authenticated AS ADMIN
    if request.user.is_authenticated and request.session.get('auth_portal') == 'admin':
        return redirect(get_login_redirect_url(request.user))
    
    # Redirect regular users to user dashboard
    if request.user.is_authenticated and not request.user.is_staff:
        messages.warning(request, "You don't have admin privileges.")
        return redirect('user_home:home')

    if request.method == 'POST':
        form = AdminSigninForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            login(request, user)
            
            # Handle "Remember me" functionality
            if not form.cleaned_data.get('remember_me'):
                request.session.set_expiry(0)
                
            # Tag the session for isolation
            request.session['auth_portal'] = 'admin'
            
            messages.success(request, f"Welcome back, {user.username}!")
            
            # Redirect to next page
            next_page = request.GET.get('next')
            return redirect(get_login_redirect_url(user, next_page))
    else:
        form = AdminSigninForm()

    context = {
        'form': form,
        'title': 'Admin Sign In'
    }
    return render(request, 'admin/auths/signin.html', context)

@staff_member_required(login_url='auth_dashboard:signin')
@never_cache
def admin_signout(request):
    logout(request)
    messages.success(request, "Successfully signed out.")
    return redirect('auth_dashboard:signin')




@staff_member_required(login_url='auth_dashboard:signin')
@never_cache
def dashboard(request):
    # Get filter parameter
    selected_filter = request.GET.get('filter', 'daily')
    
    # Calculate date range based on filter
    end_date = timezone.now()
    if selected_filter == 'daily':
        start_date = end_date - timedelta(days=30)
        trunc_func = TruncDate('created_at')
    elif selected_filter == 'monthly':
        start_date = end_date - timedelta(days=365)
        trunc_func = TruncMonth('created_at')
    else:  # yearly
        start_date = end_date - timedelta(days=365*5)
        trunc_func = TruncYear('created_at')
    
    # 1. Order Statistics
    total_orders = Order.objects.count()
    total_sales = Order.objects.filter(order_status='delivered').aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    # Calculate completed and pending orders
    completed_orders = Order.objects.filter(order_status='delivered').count()
    pending_orders = Order.objects.filter(order_status__in=['pending', 'confirmed', 'processing', 'shipped']).count()
    
    # 2. Sales Chart Data
    orders = Order.objects.filter(
        created_at__range=[start_date, end_date],
        order_status='delivered'
    ).annotate(
        date_truncated=trunc_func
    ).values('date_truncated').annotate(
        sales=Sum('total_amount'),
        orders_count=Count('order_id')
    ).order_by('date_truncated')
    
    # Format chart data
    daily_sales = []
    sales_data = []
    date_labels = []
    
    for order in orders:
        if selected_filter == 'daily':
            date_str = order['date_truncated'].strftime('%b %d')
        elif selected_filter == 'monthly':
            date_str = order['date_truncated'].strftime('%b %Y')
        else:  # yearly
            date_str = order['date_truncated'].strftime('%Y')
        
        date_labels.append(date_str)
        sales_amount = float(order['sales'] or 0)
        sales_data.append(sales_amount)
        daily_sales.append({
            'date': date_str,
            'sales': sales_amount,
            'orders': order['orders_count']
        })
    
    # 3. Top Products (last 30 days)
    last_30_days = timezone.now() - timedelta(days=30)
    
    # Since you have product directly in Order model
    top_products = Order.objects.filter(
        created_at__gte=last_30_days,
        order_status='delivered'
    ).values(
        'product__name',  # Changed from variant__product__name
        'product__brand'  # Changed from variant__product__brand
    ).annotate(
        quantity_sold=Sum('quantity'),
        total_revenue=Sum(F('unit_price') * F('quantity'))
    ).order_by('-quantity_sold')[:10]
    
    # 4. Top Categories (using product__category)
    top_categories = Order.objects.filter(
        created_at__gte=last_30_days,
        order_status='delivered'
    ).values(
        'product__category__name'  # Changed from variant__product__category__name
    ).annotate(
        quantity_sold=Sum('quantity'),
        total_revenue=Sum(F('unit_price') * F('quantity'))
    ).order_by('-quantity_sold')[:10]
    
    # 5. Top Brands
    top_brands = Order.objects.filter(
        created_at__gte=last_30_days,
        order_status='delivered'
    ).values(
        'product__brand'  # Changed from variant__product__brand
    ).annotate(
        quantity_sold=Sum('quantity'),
        total_revenue=Sum(F('unit_price') * F('quantity'))
    ).order_by('-quantity_sold')[:10]
    
    # 6. Recent Orders with product information
    recent_orders = Order.objects.select_related(
        'user', 
        'product',
        'product__category',
        'variant'
    ).order_by('-created_at')[:10]
    
    # 7. Order Status Distribution
    status_distribution = Order.objects.values('order_status').annotate(
        count=Count('order_id')
    ).order_by('order_status')
    
    # Calculate percentages
    total_count = sum(item['count'] for item in status_distribution)
    for item in status_distribution:
        item['percentage'] = round((item['count'] / total_count * 100), 1) if total_count > 0 else 0
    
    # 8. Payment Method Distribution
    payment_method_distribution = Order.objects.values('payment_method').annotate(
        count=Count('order_id')
    ).order_by('payment_method')
    
    # 9. Additional metrics
    # Average Order Value
    avg_order_value = Order.objects.filter(
        order_status='delivered',
        created_at__gte=last_30_days
    ).aggregate(
        avg_value=ExpressionWrapper(
            Sum('total_amount') / Count('order_id'),
            output_field=FloatField()
        )
    )['avg_value'] or 0
    
    # New customers (last 30 days) - users who made their first order
    from django.db.models import Min
    first_time_customers = Order.objects.filter(
        created_at__gte=last_30_days
    ).values('user').annotate(
        first_order_date=Min('created_at')
    ).filter(
        created_at__date=F('first_order_date')
    ).count()
    
    # 10. Return Statistics
    return_statistics = {
        'total_return_requests': Order.objects.filter(
            return_requested_at__isnull=False
        ).count(),
        'approved_returns': Order.objects.filter(
            return_approved_at__isnull=False
        ).count(),
        'rejected_returns': Order.objects.filter(
            return_rejected_at__isnull=False
        ).count(),
        'completed_returns': Order.objects.filter(
            returned_at__isnull=False
        ).count(),
    }
    
    # 11. Top Selling Variants (if you have variant information)
    top_variants = Order.objects.filter(
        created_at__gte=last_30_days,
        order_status='delivered',
        variant__isnull=False  # Only include orders with variants
    ).values(
        'product__name',
        'variant__size',
        'variant__color'
    ).annotate(
        quantity_sold=Sum('quantity'),
        total_revenue=Sum(F('unit_price') * F('quantity'))
    ).order_by('-quantity_sold')[:10]
    
    # Calculate period total
    period_total = sum(item['sales'] for item in daily_sales) if daily_sales else 0
    
    # Calculate average daily sales
    avg_daily_sales = period_total / len(daily_sales) if daily_sales else 0
    
    # Find peak day sales
    peak_day_sales = max((item['sales'] for item in daily_sales), default=0) if daily_sales else 0
    
    # 12. Revenue by Payment Status
    revenue_by_payment_status = Order.objects.values('payment_status').annotate(
        total_revenue=Sum('total_amount'),
        order_count=Count('order_id')
    ).order_by('payment_status')

    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)
    
    context = {
        'total_orders': total_orders,
        'total_sales': total_sales,
        'completed_orders': completed_orders,
        'pending_orders': pending_orders,
        'daily_sales': daily_sales,
        'sales_data': sales_data,
        'date_labels': date_labels,
        'top_products': top_products,
        'top_categories': top_categories,
        'top_brands': top_brands,
        'recent_orders': recent_orders,
        'selected_filter': selected_filter,
        'avg_order_value': round(avg_order_value, 2),
        'new_customers': first_time_customers,
        'period_total': period_total,
        'avg_daily_sales': round(avg_daily_sales, 2),
        'peak_day_sales': peak_day_sales,
        'days_active': len(daily_sales) if daily_sales else 0,
        'status_distribution': status_distribution,
        'payment_method_distribution': payment_method_distribution,
        'return_statistics': return_statistics,
        'top_variants': top_variants,
        'revenue_by_payment_status': revenue_by_payment_status,
        'today': today,
        'thirty_days_ago': thirty_days_ago,
    }
    
    return render(request, 'admin/dashboard.html', context)

@staff_member_required(login_url='auth_dashboard:signin')
@never_cache
def download_sales_report(request):
    """Handle sales report download"""
    
    # Get parameters
    report_format = request.GET.get('format', 'pdf')  # Default to PDF
    report_type = request.GET.get('type', 'detailed')
    
    # Date range
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            start_date = timezone.make_aware(start_date)
        except:
            start_date = timezone.now() - timedelta(days=30)
    else:
        start_date = timezone.now() - timedelta(days=30)
    
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            end_date = timezone.make_aware(end_date)
        except:
            end_date = timezone.now()
    else:
        end_date = timezone.now()
    
    # Ensure end_date is at end of day
    end_date = end_date.replace(hour=23, minute=59, second=59)
    
    # Generate and return report
    return generate_report_response(report_format, start_date, end_date, report_type)


@staff_member_required(login_url='auth_dashboard:signin')
@never_cache
def admin_user_list(request):
    """Admin user listing with search and filters"""
    # Get all users
    users = UserModel.objects.filter(is_superuser=False).order_by('-date_joined')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(username__icontains=search_query) |
            Q(phone_number__icontains=search_query) |
            Q(referral_code__icontains=search_query)
        )
    
    # Filter functionality
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    
    
    # Date filter
    date_filter = request.GET.get('date_filter', '')
    today = timezone.now().date()
    if date_filter == 'today':
        users = users.filter(date_joined__date=today)
    elif date_filter == 'week':
        week_ago = today - timedelta(days=7)
        users = users.filter(date_joined__date__gte=week_ago)
    elif date_filter == 'month':
        month_ago = today - timedelta(days=30)
        users = users.filter(date_joined__date__gte=month_ago)
    
    # Sorting
    sort_by = request.GET.get('sort', '-date_joined')
    if sort_by in ['date_joined', '-date_joined', 'email', '-email', 'username', '-username']:
        users = users.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(users, 25)  # Show 25 users per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    total_users = UserModel.objects.filter(is_superuser=False).count()
    active_users = UserModel.objects.filter(is_active=True, is_superuser=False).count()
    new_today = UserModel.objects.filter(date_joined__date=today).count()
    new_week = UserModel.objects.filter(
        date_joined__date__gte=today - timedelta(days=7)
    ).count()
    
    context = {
        'page_obj': page_obj,
        'users': page_obj,
        'total_users': total_users,
        'active_users': active_users,
        'new_today': new_today,
        'new_week': new_week,
        'search_query': search_query,
        'status_filter': status_filter,
        'date_filter': date_filter,
        'sort_by': sort_by,
    }
    
    return render(request, 'admin/users/user_list.html', context)

@staff_member_required(login_url='auth_dashboard:signin')
@never_cache
def admin_user_detail(request, user_id):
    """Admin user detail view - shows basic user information"""
    User = get_user_model()
    user = get_object_or_404(User, id=user_id)
    
    # Get basic user stats
    today = timezone.now().date()
    days_since_joined = (today - user.date_joined.date()).days
    
    # Count user activities if you have any activity models
    # For example, if you have an Order model:
    # total_orders = Order.objects.filter(user=user).count()
    # total_spent = Order.objects.filter(user=user).aggregate(total=models.Sum('total_amount'))['total'] or 0
    
    # Get login history if you have it
    # recent_logins = LoginHistory.objects.filter(user=user).order_by('-login_time')[:10]
    
    context = {
        'user': user,
        'days_since_joined': days_since_joined,
        'today': today,
    }
    
    return render(request, 'admin/users/user_details.html', context)


@staff_member_required(login_url='auth_dashboard:signin')
@never_cache
def admin_user_toggle_active(request, user_id):
    User = get_user_model()
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        user.is_active = not user.is_active
        user.save()
        
        action = "granted User access to" if user.is_active else "revoked user access from"
        messages.success(request, f"Successfully {action} {user.email}.")
        
    return redirect('auth_dashboard:admin_user_detail', user_id=user_id)


@staff_member_required(login_url='auth_dashboard:signin')
@never_cache
def admin_user_activate(request, user_id):
    """Activate a user account"""
    User = get_user_model()
    user = get_object_or_404(User, id=user_id)
    
    # Prevent self-deactivation
    if user == request.user:
        messages.error(request, "You cannot modify your own account status.")
        return redirect('auth_dashboard:admin_user_list')
    
    if not user.is_active:
        user.is_active = True
        user.save()
        messages.success(request, f"User {user.get_full_name() or user.username} has been activated successfully.")
    else:
        messages.info(request, f"User {user.get_full_name() or user.username} is already active.")
    
    # Try to redirect to referring page
    referer = request.META.get('HTTP_REFERER')
    if referer and 'users' in referer:
        return redirect(referer)
    return redirect('auth_dashboard:admin_user_list')


@staff_member_required(login_url='auth_dashboard:signin')
@never_cache
def admin_user_deactivate(request, user_id):
    """Deactivate a user account"""
    User = get_user_model()
    user = get_object_or_404(User, id=user_id)
    
    # Prevent self-deactivation
    if user == request.user:
        messages.error(request, "You cannot deactivate your own account.")
        return redirect('auth_dashboard:admin_user_list')
    
    # Prevent deactivating superusers (optional security measure)
    if user.is_superuser and not request.user.is_superuser:
        messages.error(request, "You don't have permission to deactivate a superuser.")
        return redirect('auth_dashboard:admin_user_list')
    
    if user.is_active:
        user.is_active = False
        user.save()
        messages.success(request, f"User {user.get_full_name() or user.username} has been deactivated successfully.")
    else:
        messages.info(request, f"User {user.get_full_name() or user.username} is already inactive.")
    
    # Try to redirect to referring page
    referer = request.META.get('HTTP_REFERER')
    if referer and 'users' in referer:
        return redirect(referer)
    return redirect('auth_dashboard:admin_user_list')


# ============================================
# COUPON MANAGEMENT VIEWS
# ============================================

@staff_member_required(login_url='auth_dashboard:signin')
@never_cache
def coupon_list(request):
    """List all coupons with search and filters"""
    from common.orders.models import Coupon
    
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
    from common.orders.models import Coupon
    
    if request.method == 'POST':
        try:
            coupon = Coupon(
                code=request.POST.get('code').strip().upper(),
                description=request.POST.get('description', '').strip(),
                discount_percentage=request.POST.get('discount_percentage'),
                max_uses=request.POST.get('max_uses', 0),
                max_uses_per_user=request.POST.get('max_uses_per_user', 1),
                minimum_order_amount=request.POST.get('minimum_order_amount', 0),
                max_discount_amount=request.POST.get('max_discount_amount') or None,
                valid_from=request.POST.get('valid_from'),
                valid_until=request.POST.get('valid_until'),
                is_active=request.POST.get('is_active') == 'on',
                created_by=request.user
            )
            coupon.save()
            
            messages.success(request, f'Coupon "{coupon.code}" created successfully!')
            return redirect('auth_dashboard:coupon_list')
            
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
    from common.orders.models import Coupon
    
    coupon = get_object_or_404(Coupon, id=coupon_id)
    
    if request.method == 'POST':
        try:
            coupon.code = request.POST.get('code').strip().upper()
            coupon.description = request.POST.get('description', '').strip()
            coupon.discount_percentage = request.POST.get('discount_percentage')
            coupon.max_uses = request.POST.get('max_uses', 0)
            coupon.max_uses_per_user = request.POST.get('max_uses_per_user', 1)
            coupon.minimum_order_amount = request.POST.get('minimum_order_amount', 0)
            coupon.max_discount_amount = request.POST.get('max_discount_amount') or None
            coupon.valid_from = request.POST.get('valid_from')
            coupon.valid_until = request.POST.get('valid_until')
            coupon.is_active = request.POST.get('is_active') == 'on'
            coupon.save()
            
            messages.success(request, f'Coupon "{coupon.code}" updated successfully!')
            return redirect('auth_dashboard:coupon_list')
            
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
    from common.orders.models import Coupon
    
    coupon = get_object_or_404(Coupon, id=coupon_id)
    
    if request.method == 'POST':
        code = coupon.code
        coupon.delete()
        messages.success(request, f'Coupon "{code}" deleted successfully!')
        return redirect('auth_dashboard:coupon_list')
    
    context = {
        'coupon': coupon,
    }
    
    return render(request, 'admin/coupons/coupon_confirm_delete.html', context)


@staff_member_required(login_url='auth_dashboard:signin')
@never_cache
def coupon_toggle_active(request, coupon_id):
    """Toggle coupon active status"""
    from common.orders.models import Coupon
    
    coupon = get_object_or_404(Coupon, id=coupon_id)
    
    if request.method == 'POST':
        coupon.is_active = not coupon.is_active
        coupon.save()
        
        status = "activated" if coupon.is_active else "deactivated"
        messages.success(request, f'Coupon "{coupon.code}" {status} successfully!')
    
    return redirect('auth_dashboard:coupon_list')


@staff_member_required(login_url='auth_dashboard:signin')
@never_cache
def coupon_usage_list(request):
    """List all coupon usages"""
    from common.orders.models import CouponUsage
    
    usages = CouponUsage.objects.all().select_related('coupon', 'user', 'order').order_by('-used_at')
    
    # Filter by coupon
    coupon_filter = request.GET.get('coupon', '')
    if coupon_filter:
        usages = usages.filter(coupon__code__icontains=coupon_filter)
    
    # Pagination
    paginator = Paginator(usages, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'usages': page_obj,
        'coupon_filter': coupon_filter,
    }
    
    return render(request, 'admin/coupons/coupon_usage_list.html', context)

@staff_member_required(login_url='auth_dashboard:signin')
@never_cache
def admin_cancellations(request):
    """View to see cancelled orders and deleted products"""
    # 1. Cancelled Orders
    cancelled_orders_qs = Order.objects.filter(order_status='cancelled').select_related(
        'user', 'product', 'variant', 'shipping_address'
    ).order_by('-cancelled_at')
    
    # 2. Deleted Products
    deleted_products_qs = Product.objects.filter(is_deleted=True).select_related('category').order_by('-updated_at')
    
    # Pagination for orders
    order_page = request.GET.get('order_page', 1)
    order_paginator = Paginator(cancelled_orders_qs, 10)
    cancelled_orders = order_paginator.get_page(order_page)
    
    # Pagination for products
    product_page = request.GET.get('product_page', 1)
    product_paginator = Paginator(deleted_products_qs, 10)
    deleted_products = product_paginator.get_page(product_page)
    
    context = {
        'cancelled_orders': cancelled_orders,
        'deleted_products': deleted_products,
        'title': 'Cancellations & Archives'
    }
    return render(request, 'admin/archives/cancellations.html', context)
