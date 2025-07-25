from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from products.models import Product
from django.contrib.auth import logout

@never_cache
@login_required(login_url='login')
def home(request):
    if request.user.is_staff:
        logout(request)  
        return redirect('login') 
    products = Product.objects.filter(is_active=True)[:6]
    context = {
    'products': products
    }
    return render(request, 'registration/home.html', context)


@never_cache
@login_required(login_url='admin_login')
def admin_dashboard(request):
    if not request.user.is_staff:
        logout(request)  
        return redirect('admin_login')  
    
    return render(request, 'custom_admin/dashboard.html')
