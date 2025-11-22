from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from django.views.decorators.cache import never_cache
from .forms import AdminSigninForm
from django.contrib.auth import logout
from django.contrib.admin.views.decorators import staff_member_required


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


@never_cache
def admin_signout(request):
    logout(request)
    messages.success(request, "Successfully signed out.")
    return redirect('admin_auth:signin')

@staff_member_required(login_url='auth_dashboard:signin')
def dashboard(request):
    return render(request, 'admin/dashboard.html')

