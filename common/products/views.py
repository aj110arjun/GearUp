import json

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.db.models import Q, Count, Sum,  Min, Max
from django.db import transaction
from django.utils.text import slugify
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.urls import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from common.user.cart_wishlist.models import Cart, CartItem, Wishlist
from .models import Product, ProductVariant, Category
from .forms import (
    ProductCreateForm,
    ProductEditForm,
    ProductImageForm,
    ProductImageFormSet,
    ProductVariantFormSet,
    CategoryForm,
    ProductVariantForm,    
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
def add_variant(request, product_slug):
    """Add a new variant for a product"""
    product = get_object_or_404(Product, slug=product_slug)
    
    if request.method == 'POST':
        form = ProductVariantForm(request.POST)
        if form.is_valid():
            variant = form.save(commit=False)
            variant.product = product
            variant.save()
            
            messages.success(request, f'Variant added successfully for {product.name}')
            return redirect('products:product_edit', product_slug=product.slug)
    else:
        form = ProductVariantForm()
    
    context = {
        'product': product,
        'form': form,
        'title': f'Add Variant - {product.name}'
    }
    return render(request, 'admin/products/add_variant.html', context)

@staff_member_required
@never_cache
def edit_variant(request, product_slug, variant_id):
    """Edit an existing variant"""
    product = get_object_or_404(Product, slug=product_slug)
    variant = get_object_or_404(ProductVariant, id=variant_id, product=product)
    
    if request.method == 'POST':
        form = ProductVariantForm(request.POST, instance=variant)
        if form.is_valid():
            form.save()
            messages.success(request, 'Variant updated successfully')
            return redirect('products:product_edit', product_slug=product.slug)
    else:
        form = ProductVariantForm(instance=variant)
    
    context = {
        'product': product,
        'variant': variant,
        'form': form,
        'title': f'Edit Variant - {product.name}'
    }
    return render(request, 'admin/products/edit_variant.html', context)

@staff_member_required
@require_POST
def delete_variant(request, variant_id):
    """Delete a variant"""
    variant = get_object_or_404(ProductVariant, id=variant_id)
    product_slug = variant.product.slug
    
    variant.delete()
    messages.success(request, 'Variant deleted successfully')
    return redirect('products:product_edit', product_slug=product_slug)

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
    
    # Get filter parameters (match template parameter names)
    category_id = request.GET.get('category')
    search_query = request.GET.get('q')
    sort_by = request.GET.get('sort', '')
    
    # Debug prints
    print(f"Category ID: {category_id}")
    print(f"Search Query: {search_query}")
    print(f"Sort By: {sort_by}")
    
    # Apply filters
    if category_id and category_id != '':
        try:
            products = products.filter(category__id=category_id)
        except ValueError:
            pass  # Invalid category ID
    
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(brand__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )
    
    # Remove duplicates
    products = products.distinct()
    
    # Apply sorting (use different annotation names to avoid property conflict)
    if sort_by == 'price_asc':
        products = products.annotate(
            product_min_price=Min('variants__price')
        ).order_by('product_min_price')
    elif sort_by == 'price_desc':
        products = products.annotate(
            product_min_price=Min('variants__price')
        ).order_by('-product_min_price')
    elif sort_by == 'name':
        products = products.order_by('name')
    elif sort_by == 'name2':  # Z-A
        products = products.order_by('-name')
    else:
        # Default ordering
        products = products.order_by('-created_at')
    
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
    
    # Get cart items
    cart_items = []
    wishlist_product_ids = []
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            cart_items = cart.items.all()
        except Cart.DoesNotExist:
            pass
        
        # Get wishlist product IDs
        try:
            from wishlist.models import Wishlist  # Adjust import based on your app structure
            wishlist_product_ids = Wishlist.objects.filter(
                user=request.user
            ).values_list('product_id', flat=True)
        except:
            pass
    
    # Prepare filters for template display
    filters = {
        'search': search_query or '',
        'category': category_id or '',
        'sort': sort_by or '',
    }
    
    context = {
        'products': products_page,
        'categories': categories,
        'filters': filters,
        'cart_items': cart_items,
        'cart_variant_ids': [item.variant.id for item in cart_items],
        'wishlist_product_ids': list(wishlist_product_ids),
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

    # Get cart variant IDs for current user to check which variants are in cart
    cart_variant_ids = []
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            cart_variant_ids = list(cart.items.values_list('variant_id', flat=True))
        except Cart.DoesNotExist:
            pass
    
    # Add in_cart status to each variant
    for variant in variants:
        variant.in_cart = variant.id in cart_variant_ids

    # Get related products
    related_products = Product.objects.filter(
        category=product.category,
        is_active=True
    ).exclude(id=product.id).prefetch_related('variants', 'images')[:4]

    if request.user.is_authenticated:
        wishlist = Wishlist.objects.filter(user=request.user).first()
        if wishlist:
            wishlist_product_ids = list(wishlist.items.values_list('product_id', flat=True))
        else:
            wishlist_product_ids = []
    else:
        wishlist_product_ids = []

    context = {
        'product': product,
        'images': images_qs,
        'variants': variants,
        'related_products': related_products,
        'wishlist_product_ids': wishlist_product_ids,
    }

    return render(request, 'user/products/product_details.html', context)


@require_POST
@login_required
def toggle_wishlist(request):
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        
        if not product_id:
            return JsonResponse({'error': 'Product ID is required'}, status=400)
        
        product = Product.objects.get(id=product_id)
        wishlist, created = Wishlist.objects.get_or_create(user=request.user)
        
        if wishlist.has_product(product):
            wishlist.remove_product(product)
            return JsonResponse({'status': 'removed'})
        else:
            wishlist.add_product(product)
            return JsonResponse({'status': 'added'})
            
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_POST
@login_required
def add_to_cart(request):
    try:
        # Parse JSON data from request body
        data = json.loads(request.body)
        variant_id = data.get('variant_id')
        quantity = int(data.get('quantity', 1))
        
        if not variant_id:
            return JsonResponse({'success': False, 'error': 'Variant ID is required'}, status=400)
        
        variant = ProductVariant.objects.get(id=variant_id)
        
        # Check stock availability
        if variant.stock_quantity < quantity:
            return JsonResponse({
                'success': False, 
                'error': f'Only {variant.stock_quantity} items available in stock'
            })
        
        cart, created = Cart.objects.get_or_create(user=request.user)
        
        # Check if item already in cart
        cart_item_exists = CartItem.objects.filter(cart=cart, variant=variant).exists()
        
        if cart_item_exists:
            # Remove from cart
            CartItem.objects.filter(cart=cart, variant=variant).delete()
            cart_count = cart.items.count()
            return JsonResponse({
                'success': True, 
                'added': False, 
                'removed': True,
                'cart_count': cart_count,
                'message': 'Item removed from cart'
            })
        else:
            # Add to cart
            CartItem.objects.create(cart=cart, variant=variant, quantity=quantity)
            cart_count = cart.items.count()
            return JsonResponse({
                'success': True, 
                'added': True, 
                'removed': False,
                'cart_count': cart_count,
                'message': 'Item added to cart'
            })
            
    except ProductVariant.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Product variant not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def ajax_cart_count(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            cart = Cart.objects.get(user=request.user)
            cart_count = cart.items.count()
        except Cart.DoesNotExist:
            cart_count = 0
        
        return JsonResponse({
            'count': cart_count
        })
    return JsonResponse({'error': 'Invalid request'})