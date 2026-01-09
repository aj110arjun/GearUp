import random

from django.shortcuts import redirect, render
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.views.decorators.cache import never_cache

from common.products.models import Product



@never_cache
@login_required(login_url='user_auth:signin')
def home(request):
    """
    Home page view with Featured, Bestseller, and New Arrival sections
    """
    # 1. Bestsellers (Take 4)
    bestseller_qs = Product.objects.filter(
        is_active=True, 
        is_deleted=False,
        is_bestseller=True
    ).prefetch_related('variants', 'category')[:4]
    
    # 2. Featured (Take 8)
    featured_qs = Product.objects.filter(
        is_active=True, 
        is_deleted=False,
        is_featured=True
    ).prefetch_related('variants', 'category')[:8]
    
    # 3. New Arrivals (Take 8 recent)
    new_arrivals_qs = Product.objects.filter(
        is_active=True,
        is_deleted=False
    ).order_by('-created_at').prefetch_related('variants', 'category')[:8]

    # Helper to process products
    def _prepare_products(qs):
        data = []
        for product in qs:
            variants = product.variants.filter(is_active=True, is_deleted=False)
            if variants.exists():
                first_variant = variants.first()
                # Calculate prices
                original_price = first_variant.price
                discounted_price = first_variant.get_discounted_price()
                discount_percentage = first_variant.discount_percentage
                
                # Check if there is a discount
                has_discount = discounted_price < original_price

                data.append({
                    'product': product,
                    'price': discounted_price, 
                    'original_price': original_price if has_discount else None,
                    'discount_percentage': discount_percentage if has_discount else 0,
                    'in_stock': first_variant.stock_quantity > 0,
                })
        return data

    context = {
        'bestsellers': _prepare_products(bestseller_qs),
        'featured_products': _prepare_products(featured_qs),
        'new_arrivals': _prepare_products(new_arrivals_qs),
        'today': timezone.now().date(),
        'random': random.randint(1, 99),
    }
    return render(request, 'user/index.html', context)


def custom_404_view(request, exception):
    """
    Custom 404 error handler
    """
    # Check if the request is for the admin portal
    if request.path.startswith('/admin/') or request.path.startswith('/django-admin/'):
        return render(request, 'admin/404_admin.html', status=404)
    
    # Default to customer 404 page
    return render(request, '404.html', status=404)