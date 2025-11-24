from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.db.models import Q, Count, Sum
from django.db import transaction
from django.utils.text import slugify
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.urls import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Min, Max

from .models import Product, ProductVariant, Category
from .forms import (
    ProductCreateForm,
    ProductEditForm,
    ProductImageForm,
    ProductImageFormSet,
    ProductVariantFormSet,
    CategoryForm,
)


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

@staff_member_required
@never_cache
def product_detail(request, product_slug):
    # Try different prefetch options based on your model structure
    try:
        # Option 1: If you have a separate ProductImage model
        product = get_object_or_404(
            Product.objects.prefetch_related('productimage_set', 'variants', 'category'), 
            slug=product_slug
        )
        # Get images based on the relationship name
        images = product.productimage_set.all()
    except:
        try:
            # Option 2: If the related name is 'images'
            product = get_object_or_404(
                Product.objects.prefetch_related('images', 'variants', 'category'), 
                slug=product_slug
            )
            images = product.images.all()
        except:
            # Option 3: If it's a single image field or different relationship
            product = get_object_or_404(
                Product.objects.prefetch_related('variants', 'category'), 
                slug=product_slug
            )
            images = []
    
    variants = product.variants.all()
    
    # Stock summary
    total_stock = variants.aggregate(total=Sum('stock_quantity'))['total'] or 0
    active_variants = variants.filter(is_active=True).count()
    out_of_stock_variants = variants.filter(stock_quantity=0).count()
    low_stock_variants = variants.filter(stock_quantity__lte=10, stock_quantity__gt=0).count()
    
    context = {
        'product': product,
        'images': images,
        'variants': variants,
        'total_stock': total_stock,
        'active_variants': active_variants,
        'out_of_stock_variants': out_of_stock_variants,
        'low_stock_variants': low_stock_variants,
    }
    
    return render(request, 'admin/products/product_detail.html', context)


# forms already imported above

@staff_member_required
@never_cache
def product_create(request):
    """Create a new product with basic information"""
    
    if request.method == 'POST':
        form = ProductCreateForm(request.POST)
        
        if form.is_valid():
            try:
                product = form.save(commit=False)
                
                # Auto-generate slug if empty
                if not product.slug:
                    product.slug = slugify(product.name)
                    # Ensure slug is unique
                    base_slug = product.slug
                    counter = 1
                    while Product.objects.filter(slug=product.slug).exists():
                        product.slug = f"{base_slug}-{counter}"
                        counter += 1
                
                # Save the product first to get an ID
                product.save()
                
                # Auto-generate SKU if empty (after saving to get ID)
                if not product.sku:
                    # Use UUID for unique SKU
                    product.sku = f"GRP-{str(product.id)[:8].upper()}"
                    product.save(update_fields=['sku'])
                
                # Success messages
                messages.success(
                    request, 
                    f'Product "{product.name}" has been created successfully!'
                )
                messages.info(
                    request, 
                    'You can now add variants and images by editing the product.'
                )
                
                # Redirect to product detail or edit page
                return redirect('products:product_detail', product_slug=product.slug)
                
            except Exception as e:
                messages.error(
                    request, 
                    f'An error occurred while creating the product: {str(e)}'
                )
        else:
            # Form has validation errors
            messages.error(
                request, 
                'Please correct the errors below.'
            )
    else:
        # GET request - show empty form
        form = ProductCreateForm()
    
    # Get active categories for the dropdown
    categories = Category.objects.filter(is_active=True).order_by('name')
    
    context = {
        'form': form,
        'categories': categories,
        'is_edit': False,
        'title': 'Add New Product',
    }
    
    return render(request, 'admin/products/product_create.html', context)

@staff_member_required
@never_cache
def product_edit(request, product_slug):
    """Full product editing with variants and images"""
    product = get_object_or_404(Product, slug=product_slug)
    
    if request.method == 'POST':
        form = ProductEditForm(request.POST, instance=product)
        variant_formset = ProductVariantFormSet(request.POST, instance=product)
        image_formset = ProductImageFormSet(request.POST, request.FILES, instance=product)
        
        if form.is_valid() and variant_formset.is_valid() and image_formset.is_valid():
            try:
                with transaction.atomic():
                    # Save the main product form
                    product = form.save()
                    
                    # Save variants
                    variants = variant_formset.save(commit=False)
                    for variant in variants:
                        variant.product = product
                        variant.save()
                    
                    # Delete marked variants
                    for variant in variant_formset.deleted_objects:
                        variant.delete()
                    
                    # Save images
                    images = image_formset.save(commit=False)
                    for image in images:
                        image.product = product
                        image.save()
                    
                    # Delete marked images
                    for image in image_formset.deleted_objects:
                        image.delete()
                    
                    # Note: AdditionalImage model doesn't track 'is_primary'; skip primary-image enforcement
                    
                    messages.success(
                        request, 
                        f'Product "{product.name}" has been updated successfully!'
                    )
                    return redirect('products:product_detail', product_slug=product.slug)
                    
            except Exception as e:
                messages.error(
                    request, 
                    f'An error occurred while updating the product: {str(e)}'
                )
        else:
            messages.error(request, 'Please correct the errors below.')
            # Add form errors to messages
            if form.errors:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
    else:
        form = ProductEditForm(instance=product)
        variant_formset = ProductVariantFormSet(instance=product)
        image_formset = ProductImageFormSet(instance=product)
    
    categories = Category.objects.filter(is_active=True).order_by('name')
    
    context = {
        'form': form,
        'variant_formset': variant_formset,
        'image_formset': image_formset,
        'product': product,
        'categories': categories,
        'is_edit': True,
        'title': f'Edit Product - {product.name}',
    }
    
    return render(request, 'admin/products/product_edit.html', context)


@staff_member_required
@never_cache
def category_list(request):
    # Get all categories with related data and annotate with counts
    categories = Category.objects.prefetch_related('products').annotate(
        total_products_count=Count('products'),
        active_products_count=Count('products', filter=Q(products__is_active=True))
    ).all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        categories = categories.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(slug__icontains=search_query)
        )
    
    # Filter functionality
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        categories = categories.filter(is_active=True)
    elif status_filter == 'inactive':
        categories = categories.filter(is_active=False)
    
    # Sorting
    sort_by = request.GET.get('sort', 'name')
    if sort_by in ['name', '-name', 'created_at', '-created_at', 'product_count', '-product_count']:
        if sort_by == 'product_count':
            categories = categories.order_by('total_products_count')
        elif sort_by == '-product_count':
            categories = categories.order_by('-total_products_count')
        else:
            categories = categories.order_by(sort_by)
    else:
        categories = categories.order_by('name')
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(categories, 20)  # 20 categories per page
    
    try:
        categories_page = paginator.page(page)
    except PageNotAnInteger:
        categories_page = paginator.page(1)
    except EmptyPage:
        categories_page = paginator.page(paginator.num_pages)
    
    # Get summary statistics
    total_categories = categories.count()
    active_categories = categories.filter(is_active=True).count()
    categories_with_products = categories.filter(total_products_count__gt=0).count()
    
    context = {
        'categories': categories_page,
        'search_query': search_query,
        'status_filter': status_filter,
        'sort_by': sort_by,
        'total_categories': total_categories,
        'active_categories': active_categories,
        'categories_with_products': categories_with_products,
    }
    
    return render(request, 'admin/categories/category_list.html', context)


@staff_member_required
@never_cache
def category_create(request):
    return handle_category_form(request)

@staff_member_required
@never_cache
def category_edit(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)
    return handle_category_form(request, category)

def handle_category_form(request, category_instance=None):
    """
    Handle both create and edit operations in one function
    """
    is_edit = category_instance is not None
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category_instance)
        
        if form.is_valid():
            category = form.save(commit=False)
            
            # Auto-generate slug if empty
            if not category.slug and category.name:
                from django.utils.text import slugify
                category.slug = slugify(category.name)
            
            category.save()
            
            # Success message
            action = "updated" if is_edit else "created"
            messages.success(request, f'Category "{category.name}" has been {action} successfully!')
            
            return redirect('products:category_list')  # You'll need to create this view
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        # GET request - initialize form
        if is_edit:
            form = CategoryForm(instance=category_instance)
        else:
            form = CategoryForm()
    
    context = {
        'form': form,
        'is_edit': is_edit,
        'category': category_instance if is_edit else None,
        'title': f'Edit Category - {category_instance.name}' if is_edit else 'Add New Category',
    }
    
    return render(request, 'admin/categories/category_form.html', context)

@login_required(login_url='user_auth:signin')
@never_cache
def product_list_user(request):
    """User-side product listing with filtering and sorting"""
    # Get all active products with variants
    products = Product.objects.filter(is_active=True).prefetch_related('variants', 'category')
    
    # Get filter parameters
    category_slug = request.GET.get('category')
    search_query = request.GET.get('q')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    sort_by = request.GET.get('sort', 'name')
    in_stock = request.GET.get('in_stock')
    
    # Apply filters
    if category_slug and category_slug != 'all':
        products = products.filter(category__slug=category_slug)
    
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(brand__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )
    
    if min_price:
        products = products.filter(variants__price__gte=min_price)
    
    if max_price:
        products = products.filter(variants__price__lte=max_price)
    
    if in_stock:
        products = products.filter(variants__stock_quantity__gt=0)
    
    # Remove duplicates
    products = products.distinct()
    
    # Apply sorting
    if sort_by == 'price_low':
        products = products.annotate(min_price=Min('variants__price')).order_by('min_price')
    elif sort_by == 'price_high':
        products = products.annotate(min_price=Min('variants__price')).order_by('-min_price')
    elif sort_by == 'name':
        products = products.order_by('name')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    elif sort_by == 'bestseller':
        products = products.filter(is_bestseller=True).order_by('-created_at')
    elif sort_by == 'featured':
        products = products.filter(is_featured=True).order_by('-created_at')
    else:
        products = products.order_by('name')
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(products, 12)  # 12 products per page
    
    try:
        products_page = paginator.page(page)
    except PageNotAnInteger:
        products_page = paginator.page(1)
    except EmptyPage:
        products_page = paginator.page(paginator.num_pages)
    
    # Get categories for filter
    categories = Category.objects.filter(is_active=True)
    
    # Get price range for filter
    price_range = products.aggregate(
        min_price=Min('variants__price'),
        max_price=Max('variants__price')
    )
    
    context = {
        'products': products_page,
        'categories': categories,
        'search_query': search_query,
        'category_slug': category_slug,
        'min_price': min_price,
        'max_price': max_price,
        'sort_by': sort_by,
        'in_stock': in_stock,
        'price_range': price_range,
    }
    
    return render(request, 'user/products/product_list.html', context)

@login_required(login_url='user_auth:signin')
@never_cache
def product_detail_user(request, product_slug):
    """User-side product detail page"""
    # Prefetch the known relations; ProductImage uses related_name 'images'
    product = get_object_or_404(
        Product.objects.prefetch_related('variants', 'images', 'category'),
        slug=product_slug,
        is_active=True
    )

    # Use the related `images` queryset directly and pass it in context
    images_qs = product.images.all()

    # Get active variants
    variants = product.variants.filter(is_active=True)

    # Get related products
    related_products = Product.objects.filter(
        category=product.category,
        is_active=True
    ).exclude(id=product.id).prefetch_related('variants', 'images')[:4]

    context = {
        'product': product,
        'images': images_qs,
        'variants': variants,
        'related_products': related_products,
    }

    return render(request, 'user/products/product_details.html', context)