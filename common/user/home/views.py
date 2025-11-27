import random

from django.shortcuts import redirect, render
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.views.decorators.cache import never_cache

from common.products.views import Product



@never_cache
@login_required(login_url='user_auth:signin')
def home(request):
    # Get all active products
    active_products = Product.objects.filter(
        is_active=True
    ).prefetch_related('variants')
    
    # Convert to list and shuffle for random selection
    product_list = list(active_products)
    random.shuffle(product_list)
    
    # Take first 12 products
    random_products = product_list[:12]
    
    # Prepare product data with pricing information
    products_data = []
    for product in random_products:
        variants = product.variants.filter(is_active=True)
        if variants.exists():
            # Get the first variant for display
            first_variant = variants.first()
            products_data.append({
                'product': product,
                'price': first_variant.price,
                'original_price': first_variant.compare_price if first_variant.compare_price else None,
                'discount': True if first_variant.compare_price and first_variant.compare_price > first_variant.price else False,
                'in_stock': first_variant.stock_quantity > 0
            })
    
    # Calculate discount percentage for template
    for product_data in products_data:
        if product_data['original_price'] and product_data['price']:
            discount_amount = product_data['original_price'] - product_data['price']
            product_data['discount_percentage'] = int((discount_amount / product_data['original_price']) * 100)
        else:
            product_data['discount_percentage'] = 0
    
    context = {
        'products': products_data,
        'today': timezone.now().date(),  # Add current date for birthday detection
        'random': random.randint(1, 99),  # Add random number for ratings
    }
    return render(request, 'user/index.html', context)