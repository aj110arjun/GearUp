from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from products.models import Product

@never_cache
@login_required(login_url='login')
def home(request):
    products = Product.objects.all()
    context = {
    'products': products
    }
    return render(request, 'registration/home.html', context)
