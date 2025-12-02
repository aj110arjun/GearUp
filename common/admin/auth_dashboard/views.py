from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.contrib.auth import logout
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q
from django.conf import settings
from common.user.auths.models import UserModel
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from .forms import AdminSigninForm

@never_cache
def admin_signin(request):
    # Redirect if already authenticated and is staff
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('auth_dashboard:dashboard')
    
    # Redirect regular users to user dashboard
    if request.user.is_authenticated and not request.user.is_staff:
        messages.warning(request, "You don't have admin privileges.")
        return redirect('home')

    if request.method == 'POST':
        form = AdminSigninForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            login(request, user)
            
            # Handle "Remember me" functionality
            if not form.cleaned_data.get('remember_me'):
                request.session.set_expiry(0)  # Session expires when browser closes
            
            messages.success(request, f"Welcome back, {user.username}!")
            
            # Redirect to next page or admin dashboard
            next_page = request.GET.get('next', 'auth_dashboard:dashboard')
            return redirect(next_page)
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
    return redirect('admin_auth:signin')

@staff_member_required(login_url='auth_dashboard:signin')
def dashboard(request):
    return render(request, 'admin/dashboard.html')

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
    
    return redirect('auth_dashboard:admin_user_list')

