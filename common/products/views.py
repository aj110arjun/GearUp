from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.db.models import Q, Count, Sum
from .models import Product, ProductVariant, Category
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.urls import reverse
from .forms import ProductForm, ProductImageFormSet, ProductVariantFormSet


@staff_member_required(login_url='auth_dashboard:signin')
@never_cache
def product_listing(request):
    # Filters
    category_filter = request.GET.get('category', '')
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')
    
    # Get products
    products = Product.objects.all().prefetch_related('variants')
    
    # Apply filters
    if category_filter:
        products = products.filter(category__slug=category_filter)
    
    if status_filter:
        if status_filter == 'active':
            products = products.filter(is_active=True)
        elif status_filter == 'inactive':
            products = products.filter(is_active=False)
        elif status_filter == 'featured':
            products = products.filter(is_featured=True)
        elif status_filter == 'bestseller':
            products = products.filter(is_bestseller=True)
        elif status_filter == 'out_of_stock':
            products = products.filter(variants__stock_quantity=0).distinct()
        elif status_filter == 'low_stock':
            products = products.filter(variants__stock_quantity__lte=10, variants__stock_quantity__gt=0).distinct()
    
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(sku__icontains=search_query) |
            Q(brand__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Get categories for filter dropdown
    categories = Category.objects.filter(is_active=True)
    
    # Add variant counts and total stock to each product
    for product in products:
        product.variant_count = product.variants.count()
        product.total_stock = product.variants.aggregate(total=Sum('stock_quantity'))['total'] or 0
        product.active_variants = product.variants.filter(is_active=True).count()
    
    context = {
        'products': products,
        'categories': categories,
        'category_filter': category_filter,
        'status_filter': status_filter,
        'search_query': search_query,
        'total_products': products.count(),
    }
    
    return render(request, 'admin/products/product_list.html', context)

@staff_member_required(login_url='auth_dashboard:signin')
@never_cache
def product_detail(request, product_slug):
    product = get_object_or_404(
        Product.objects.prefetch_related('variants', 'images'), 
        slug=product_slug
    )
    variants = product.variants.all()
    
    # Stock summary
    total_stock = variants.aggregate(total=Sum('stock_quantity'))['total'] or 0
    active_variants = variants.filter(is_active=True).count()
    out_of_stock_variants = variants.filter(stock_quantity=0).count()
    low_stock_variants = variants.filter(stock_quantity__lte=10, stock_quantity__gt=0).count()
    
    context = {
        'product': product,
        'variants': variants,
        'total_stock': total_stock,
        'active_variants': active_variants,
        'out_of_stock_variants': out_of_stock_variants,
        'low_stock_variants': low_stock_variants,
    }
    
    return render(request, 'admin/products/product_detail.html', context)


@staff_member_required
@never_cache
def product_create(request):
    return handle_product_form(request)

@staff_member_required
@never_cache
def product_edit(request, product_slug):
    product = get_object_or_404(Product, slug=product_slug)
    return handle_product_form(request, product)

def handle_product_form(request, product_instance=None):
    """
    Handle both create and edit operations in one function
    """
    is_edit = product_instance is not None
    
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product_instance)
        image_formset = ProductImageFormSet(
            request.POST, request.FILES, 
            instance=product_instance if is_edit else None
        )
        variant_formset = ProductVariantFormSet(
            request.POST, 
            instance=product_instance if is_edit else None
        )
        
        if form.is_valid() and image_formset.is_valid() and variant_formset.is_valid():
            product = form.save(commit=False)
            
            # Auto-generate slug if empty
            if not product.slug and product.name:
                from django.utils.text import slugify
                product.slug = slugify(product.name)
            
            product.save()
            
            # Save formsets
            image_formset.instance = product
            image_formset.save()
            
            variant_formset.instance = product
            variant_formset.save()
            
            # Success message
            action = "updated" if is_edit else "created"
            messages.success(request, f'Product "{product.name}" has been {action} successfully!')
            
            return redirect('products:product_detail', product_slug=product.slug)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        # GET request - initialize forms
        if is_edit:
            form = ProductForm(instance=product_instance)
            image_formset = ProductImageFormSet(instance=product_instance)
            variant_formset = ProductVariantFormSet(instance=product_instance)
        else:
            form = ProductForm()
            image_formset = ProductImageFormSet()
            variant_formset = ProductVariantFormSet()
    
    context = {
        'form': form,
        'image_formset': image_formset,
        'variant_formset': variant_formset,
        'is_edit': is_edit,
        'product': product_instance if is_edit else None,
        'title': f'Edit Product - {product_instance.name}' if is_edit else 'Add New Product',
    }
    
    return render(request, 'admin/products/product_form.html', context)