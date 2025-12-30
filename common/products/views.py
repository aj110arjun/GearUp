import json
import logging

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.cache import never_cache
from django.db.models import Q, Count, Sum, Min, Max, Avg
from django.db import transaction
from django.utils.text import slugify
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.urls import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.core.exceptions import ValidationError
from django.conf import settings

from common.user.cart_wishlist.models import Cart, CartItem, Wishlist, WishlistItem
from .models import Product, ProductVariant, Category, ProductImage, ProductOffer, CategoryOffer, ProductReview, ReviewVote
from .forms import (
    ProductCreateForm,
    ProductEditForm,
    ProductImageForm,
    ProductImageFormSet,
    ProductVariantForm,
    ProductVariantFormSet,
    CategoryForm,
    ProductOfferForm,
    CategoryOfferForm,
    ProductReviewForm,
)

logger = logging.getLogger(__name__)

@staff_member_required(login_url='auth_dashboard:signin')
@never_cache
def product_listing(request):
    """
    Admin product listing with full filtering, sorting, and pagination
    """
    # Get parameters
    search_query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    stock_status = request.GET.get('in_stock', '')
    active_status = request.GET.get('is_active', '')
    sort_by = request.GET.get('sort', '')
    
    # Base QuerySet
    products = Product.objects.filter(is_deleted=False, category__is_deleted=False).prefetch_related('variants', 'category')
    
    # 1. Dashboard Stats (Calculated on full queryset before filtering)
    total_products = Product.objects.filter(is_deleted=False).count()
    active_products = Product.objects.filter(is_active=True, is_deleted=False).count()
    
    # Complex stats requiring variant aggregation
    # Products with at least one variant out of stock (stock_quantity = 0)
    out_of_stock_products = Product.objects.filter(is_deleted=False, variants__stock_quantity=0, variants__is_deleted=False).distinct().count()
    
    # Products with low stock (<= 10) but not out of stock
    low_stock_products = Product.objects.filter(
        is_deleted=False,
        variants__is_deleted=False,
        variants__stock_quantity__lte=10, 
        variants__stock_quantity__gt=0
    ).distinct().count()
    
    # 2. Filtering
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(sku__icontains=search_query) |
            Q(brand__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    if category_id:
        products = products.filter(category__id=category_id)

    if stock_status:
        if stock_status == 'true': # In Stock
            products = products.filter(variants__stock_quantity__gt=0, variants__is_deleted=False).distinct()
        elif stock_status == 'false': # Out of Stock
            # This is tricky in Django ORM with distinct. 
            # Usually, we want products where NO active/non-deleted variant has stock.
            # For simplicity, we'll keep the current logic but add is_deleted filter.
            products = products.filter(variants__stock_quantity=0, variants__is_deleted=False).distinct()
        elif stock_status == 'low': # Low Stock
            products = products.filter(variants__stock_quantity__lte=10, variants__stock_quantity__gt=0, variants__is_deleted=False).distinct()

    if active_status:
        if active_status == 'true':
            products = products.filter(is_active=True)
        elif active_status == 'false':
            products = products.filter(is_active=False)

    # 3. Sorting
    if sort_by == 'name':
        products = products.order_by('name')
    elif sort_by == 'price_asc':
        products = products.annotate(sorting_price=Min('variants__price', filter=Q(variants__is_deleted=False))).order_by('sorting_price')
    elif sort_by == 'price_desc':
        products = products.annotate(sorting_price=Min('variants__price', filter=Q(variants__is_deleted=False))).order_by('-sorting_price')
    elif sort_by == 'stock_asc':
        products = products.annotate(sorting_stock=Sum('variants__stock_quantity', filter=Q(variants__is_deleted=False))).order_by('sorting_stock')
    elif sort_by == 'stock_desc':
        products = products.annotate(sorting_stock=Sum('variants__stock_quantity', filter=Q(variants__is_deleted=False))).order_by('-sorting_stock')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    else:
        # Default sort
        products = products.order_by('-created_at')

    # 4. Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(products, 10) # 10 items per page as requested

    try:
        products_page = paginator.page(page)
    except PageNotAnInteger:
        products_page = paginator.page(1)
    except EmptyPage:
        products_page = paginator.page(paginator.num_pages)

    # 5. Enrich objects for template display (Total stock calculation)
    for product in products_page:
        product.total_stock = product.variants.filter(is_deleted=False).aggregate(total=Sum('stock_quantity'))['total'] or 0

    # 6. Context
    context = {
        'products': products_page,
        'categories': Category.objects.filter(is_active=True, is_deleted=False),
        'total_products': total_products,
        'active_products': active_products,
        'out_of_stock_products': out_of_stock_products,
        'low_stock_products': low_stock_products,
        # Preserve filters for template inputs
        'filters': {
            'search': search_query,
            'category': category_id,
            'in_stock': stock_status,
            'is_active': active_status,
            'sort': sort_by,
        },
        'applied_filters': [] # Optional: List of readable active filters for badges
    }
    
    # Helper to create list of applied filters
    if category_id:
        try:
            cat = Category.objects.get(id=category_id)
            context['applied_filters'].append(f"Category: {cat.name}")
        except: pass
    if stock_status:
        map_stock = {'true': 'In Stock', 'false': 'Out of Stock', 'low': 'Low Stock'}
        context['applied_filters'].append(map_stock.get(stock_status, 'Stock Filter'))
    if active_status:
        context['applied_filters'].append('Active' if active_status == 'true' else 'Inactive')
    if search_query:
        context['applied_filters'].append(f"Search: {search_query}")

    return render(request, 'admin/products/product_list.html', context)


@staff_member_required(login_url='auth_dashboard:signin')
@never_cache
def product_delete(request, slug):
    """Delete a product"""
    product = get_object_or_404(Product, slug=slug)
    
    if request.method == 'POST':
        try:
            product_name = product.name
            product.is_deleted = True
            product.is_active = False # Also deactivate it
            product.save()
            messages.success(request, f'Product "{product_name}" has been soft deleted successfully!')
            return redirect('products:product_list')
        except Exception as e:
            messages.error(request, f'An error occurred while deleting the product: {str(e)}')
            logger.error(f"Error deleting product: {str(e)}")
            return redirect('products:product_detail', product_slug=slug)
    
    # If not POST, show confirmation page
    context = {
        'product': product,
        'title': f'Delete Product - {product.name}',
    }
    return render(request, 'admin/products/product_delete_confirm.html', context)


@staff_member_required(login_url='auth_dashboard:signin')
@never_cache
def product_detail(request, product_slug):
    product = get_object_or_404(
        Product.objects.prefetch_related('images', 'variants', 'category'), 
        slug=product_slug
    )
    images = product.images.all()
    variants = product.variants.filter(is_deleted=False)
    
    # Stock summary
    total_stock = variants.aggregate(total=Sum('stock_quantity'))['total'] or 0
    active_variants = variants.filter(is_active=True, is_deleted=False).count()
    out_of_stock_variants = variants.filter(stock_quantity=0, is_deleted=False).count()
    low_stock_variants = variants.filter(stock_quantity__lte=10, stock_quantity__gt=0, is_deleted=False).count()
    
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

@staff_member_required(login_url='auth_dashboard:signin')
@never_cache
def product_create(request):
    """Create a new product with basic information and image upload"""
    
    if request.method == 'POST':
        form = ProductCreateForm(request.POST, request.FILES)
        
        if form.is_valid():
            try:
                product = form.save(commit=False)
                
                # Handle image upload
                if 'image' in request.FILES:
                    product.image = request.FILES['image']
                
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
                    product.sku = f"GRP-{str(product.id)[:8].upper()}"
                    product.save(update_fields=['sku'])
                
                # Create a primary ProductImage record from the main image
                if product.image:
                    ProductImage.objects.create(
                        product=product,
                        image=product.image,
                        alt_text=f"{product.name} - Main Image",
                        is_primary=True,
                        display_order=0
                    )
                
                # Success messages
                messages.success(
                    request, 
                    f'Product "{product.name}" has been created successfully!'
                )
                messages.info(
                    request, 
                    'You can now add variants and additional images by editing the product.'
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
    
    # Get active and non-deleted categories for the dropdown
    categories = Category.objects.filter(is_active=True, is_deleted=False).order_by('name')
    
    context = {
        'form': form,
        'categories': categories,
        'is_edit': False,
        'title': 'Add New Product',
    }
    
    return render(request, 'admin/products/product_create.html', context)

@staff_member_required(login_url='auth_dashboard:signin')
@never_cache
def product_edit(request, slug):
    """Full product editing with images. Variants are managed separately."""
    product = get_object_or_404(Product, slug=slug)
    
    if request.method == 'POST':
        form = ProductEditForm(request.POST, request.FILES, instance=product)
        image_formset = ProductImageFormSet(request.POST, request.FILES, instance=product)
        
        if form.is_valid() and image_formset.is_valid():
            try:
                with transaction.atomic():
                    # Save the main product form
                    product = form.save()
                    
                    # Handle images
                    images = image_formset.save(commit=False)
                    for i, image in enumerate(images):
                        image.product = product
                        image.save()
                    
                    # Delete marked images
                    for image in image_formset.deleted_objects:
                        # If deleting a primary image, make another one primary
                        if image.is_primary:
                            remaining_images = ProductImage.objects.filter(product=product).exclude(pk=image.pk)
                            if remaining_images.exists():
                                remaining_images.first().is_primary = True
                                remaining_images.first().save()
                        image.delete()
                    
                    # Ensure only one primary image
                    primary_images = ProductImage.objects.filter(product=product, is_primary=True)
                    if primary_images.count() > 1:
                        # Keep the first one as primary, set others to False
                        first_primary = primary_images.first()
                        primary_images.exclude(pk=first_primary.pk).update(is_primary=False)
                    elif primary_images.count() == 0:
                        # If no primary image, set the first one as primary
                        first_image = ProductImage.objects.filter(product=product).first()
                        if first_image:
                            first_image.is_primary = True
                            first_image.save()
                    
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
                logger.error(f"Error updating product: {str(e)}")
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProductEditForm(instance=product)
        image_formset = ProductImageFormSet(instance=product)
    
    categories = Category.objects.filter(is_active=True, is_deleted=False).order_by('name')
    
    context = {
        'form': form,
        'image_formset': image_formset,
        'product': product,
        'variants': product.variants.filter(is_deleted=False),
        'categories': Category.objects.filter(is_active=True, is_deleted=False).order_by('name'),
        'is_edit': True,
        'title': f'Edit Product - {product.name}',
    }
    
    return render(request, 'admin/products/product_edit.html', context)
    
@user_passes_test(lambda u: u.is_superuser)
@never_cache
def add_variant_admin(request, slug):
    """
    Separate view to add a variant to a product.
    """
    product = get_object_or_404(Product, slug=slug)
    
    if request.method == 'POST':
        form = ProductVariantForm(request.POST, product=product)
        if form.is_valid():
            variant = form.save(commit=False)
            variant.product = product
            variant.save()
            messages.success(request, f'Variant {variant} added successfully.')
            return redirect('products:product_edit', slug=product.slug)
    else:
        form = ProductVariantForm(product=product)
    
    context = {
        'product': product,
        'form': form,
    }
    return render(request, 'admin/products/variant_add.html', context)

@user_passes_test(lambda u: u.is_superuser)
@never_cache
def edit_variant_admin(request, variant_id):
    """
    Separate view to edit an existing variant.
    """
    variant = get_object_or_404(ProductVariant, id=variant_id)
    product = variant.product
    
    if request.method == 'POST':
        form = ProductVariantForm(request.POST, instance=variant)
        if form.is_valid():
            form.save()
            messages.success(request, 'Variant updated successfully!')
            return redirect('products:product_edit', slug=product.slug)
    else:
        form = ProductVariantForm(instance=variant)
    
    context = {
        'product': product,
        'variant': variant,
        'form': form,
    }
    return render(request, 'admin/products/variant_edit.html', context)

@user_passes_test(lambda u: u.is_superuser)
@never_cache
def delete_variant_admin(request, variant_id):
    """
    Soft delete a variant.
    """
    variant = get_object_or_404(ProductVariant, id=variant_id)
    product = variant.product
    
    variant.is_deleted = True
    variant.is_active = False
    variant.save()
    
    messages.success(request, 'Variant removed successfully!')
    return redirect('products:product_edit', slug=product.slug)

@staff_member_required(login_url='auth_dashboard:signin')
@never_cache
def category_list(request):
    # Get all non-deleted categories with related data and annotate with counts
    categories = Category.objects.filter(is_deleted=False).prefetch_related('products').annotate(
        total_products_count=Count('products', filter=Q(products__is_deleted=False)),
        active_products_count=Count('products', filter=Q(products__is_active=True, products__is_deleted=False))
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

@staff_member_required(login_url='auth_dashboard:signin')
@never_cache
def category_create(request):
    return handle_category_form(request)

@staff_member_required(login_url='auth_dashboard:signin')
@never_cache
def category_edit(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)
    return handle_category_form(request, category)

def handle_category_form(request, category_instance=None):
    """Handle both create and edit operations in one function"""
    is_edit = category_instance is not None
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category_instance)
        
        if form.is_valid():
            try:
                # Save with validation
                category = form.save()
                
                # Success message
                action = "updated" if is_edit else "created"
                messages.success(request, f'Category "{category.name}" has been {action} successfully!')
                
                return redirect('products:category_list')
                
            except ValidationError as e:
                # Handle model-level validation errors
                messages.error(request, str(e))
            except Exception as e:
                # Handle other errors
                logger.error(f"Error saving category: {str(e)}")
                messages.error(request, f'Error saving category: {str(e)}')
                
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
    
    # Add statistics for edit mode
    if is_edit and category_instance:
        context['total_products'] = category_instance.products.count()
        context['active_products'] = category_instance.products.filter(is_active=True).count()
    
    return render(request, 'admin/categories/category_form.html', context)

@staff_member_required(login_url='auth_dashboard:signin')
@never_cache
def offer_list(request):
    """List all product and category offers"""
    product_offers = ProductOffer.objects.select_related('product').all()
    category_offers = CategoryOffer.objects.select_related('category').all()
    
    context = {
        'product_offers': product_offers,
        'category_offers': category_offers,
    }
    return render(request, 'admin/offers/offer_list.html', context)

@staff_member_required(login_url='auth_dashboard:signin')
@never_cache
def product_offer_create(request):
    if request.method == 'POST':
        form = ProductOfferForm(request.POST)
        if form.is_valid():
            offer = form.save()
            messages.success(request, f'Offer "{offer.name}" applied to {offer.product.name} successfully!')
            return redirect('products:offer_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProductOfferForm()
    
    context = {
        'form': form,
        'title': 'Add Product Offer'
    }
    return render(request, 'admin/offers/offer_form.html', context)

@staff_member_required(login_url='auth_dashboard:signin')
@never_cache
def product_offer_edit(request, offer_id):
    offer = get_object_or_404(ProductOffer, id=offer_id)
    if request.method == 'POST':
        form = ProductOfferForm(request.POST, instance=offer)
        if form.is_valid():
            offer = form.save()
            messages.success(request, f'Offer "{offer.name}" updated successfully!')
            return redirect('products:offer_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProductOfferForm(instance=offer)
    
    context = {
        'form': form,
        'title': f'Edit Offer - {offer.name}',
        'is_edit': True
    }
    return render(request, 'admin/offers/offer_form.html', context)

@staff_member_required(login_url='auth_dashboard:signin')
@never_cache
def product_offer_delete(request, offer_id):
    offer = get_object_or_404(ProductOffer, id=offer_id)
    offer.delete()
    messages.success(request, 'Product offer deleted successfully!')
    return redirect('products:offer_list')

@staff_member_required(login_url='auth_dashboard:signin')
@never_cache
def category_offer_create(request):
    if request.method == 'POST':
        form = CategoryOfferForm(request.POST)
        if form.is_valid():
            offer = form.save()
            messages.success(request, f'Offer "{offer.name}" applied to {offer.category.name} successfully!')
            return redirect('products:offer_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CategoryOfferForm()
    
    context = {
        'form': form,
        'title': 'Add Category Offer'
    }
    return render(request, 'admin/offers/offer_form.html', context)

@staff_member_required(login_url='auth_dashboard:signin')
@never_cache
def category_offer_edit(request, offer_id):
    offer = get_object_or_404(CategoryOffer, id=offer_id)
    if request.method == 'POST':
        form = CategoryOfferForm(request.POST, instance=offer)
        if form.is_valid():
            offer = form.save()
            messages.success(request, f'Offer "{offer.name}" updated successfully!')
            return redirect('products:offer_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CategoryOfferForm(instance=offer)
    
    context = {
        'form': form,
        'title': f'Edit Offer - {offer.name}',
        'is_edit': True
    }
    return render(request, 'admin/offers/offer_form.html', context)

@staff_member_required(login_url='auth_dashboard:signin')
@never_cache
def category_offer_delete(request, offer_id):
    offer = get_object_or_404(CategoryOffer, id=offer_id)
    offer.delete()
    messages.success(request, 'Category offer deleted successfully!')
    return redirect('products:offer_list')

@login_required(login_url='user_auth:signin')
@never_cache
def product_list_user(request):
    """User-side product listing with filtering and sorting"""
    # Get all active and non-deleted products with variants, annotated with review stats
    products = Product.objects.filter(is_active=True, is_deleted=False, category__is_deleted=False).annotate(
        avg_rating_sort=Avg('reviews__rating', filter=Q(reviews__is_approved=True)),
        review_count_sort=Count('reviews', filter=Q(reviews__is_approved=True))
    ).prefetch_related('variants', 'category', 'images')
    
    # Get filter parameters
    category_id = request.GET.get('category')
    search_query = request.GET.get('q')
    sort_by = request.GET.get('sort', '')
    
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
    
    # Apply sorting
    if sort_by == 'price_asc':
        products = products.annotate(
            product_min_price=Min('variants__price', filter=Q(variants__is_active=True, variants__is_deleted=False))
        ).order_by('product_min_price')
    elif sort_by == 'price_desc':
        products = products.annotate(
            product_min_price=Min('variants__price', filter=Q(variants__is_active=True, variants__is_deleted=False))
        ).order_by('-product_min_price')
    elif sort_by == 'name':
        products = products.order_by('name')
    elif sort_by == 'name2':  # Z-A
        products = products.order_by('-name')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    elif sort_by == 'rating_desc':
        products = products.order_by('-avg_rating_sort', '-created_at')
    elif sort_by == 'rating_asc':
        products = products.order_by('avg_rating_sort', '-created_at')
    elif sort_by == 'reviews_desc':
        products = products.order_by('-review_count_sort', '-created_at')
    else:
        # Default ordering
        products = products.order_by('-created_at')
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(products, 8)  # 8 products per page
    
    try:
        products_page = paginator.page(page)
    except PageNotAnInteger:
        products_page = paginator.page(1)
    except EmptyPage:
        products_page = paginator.page(paginator.num_pages)
    
    # Get categories for filter
    categories = Category.objects.filter(is_active=True, is_deleted=False)
    
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
            wishlist_product_ids = WishlistItem.objects.filter(
                wishlist__user=request.user
            ).values_list('product_id', flat=True)
        except Exception as e:
            logger.error(f"Error getting wishlist: {e}")
    
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
    # Prefetch the known relations
    product = get_object_or_404(
        Product.objects.prefetch_related('variants', 'images', 'category', 'reviews', 'reviews__user'),
        slug=product_slug,
        is_active=True,
        is_deleted=False
    )

    # Get images
    images_qs = product.images.all()

    # Get active and non-deleted variants
    variants = product.variants.filter(is_active=True, is_deleted=False)

    # Get cart variant IDs for current user
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

    # Get approved reviews unioned with current user's reviews (even if unapproved)
    reviews_base = product.reviews.select_related('user')
    if request.user.is_authenticated:
        reviews = reviews_base.filter(Q(is_approved=True) | Q(user=request.user)).distinct()
    else:
        reviews = reviews_base.filter(is_approved=True)
    
    # Get review statistics
    review_stats = {
        'average_rating': product.get_average_rating(),
        'total_reviews': product.get_total_reviews(),
        'rating_distribution': product.get_rating_distribution(),
        'review_percentages': product.get_review_percentage(),
    }
    
    # Check if user has already reviewed this product
    user_review = None
    if request.user.is_authenticated:
        user_review = product.reviews.filter(user=request.user).first()
    
    # Review form for authenticated users who haven't reviewed
    review_form = None
    if request.user.is_authenticated and not user_review:
        review_form = ProductReviewForm()
    
    # Get user's review votes
    user_votes = {}
    if request.user.is_authenticated:
        user_votes = ReviewVote.objects.filter(
            user=request.user,
            review__in=reviews
        ).values('review_id', 'helpful')
        user_votes = {vote['review_id']: vote['helpful'] for vote in user_votes}

    # Get related products (same category)
    related_products = Product.objects.filter(
        category=product.category,
        is_active=True,
        is_deleted=False
    ).exclude(id=product.id).prefetch_related('variants', 'images')[:4]

    # Get wishlist status
    if request.user.is_authenticated:
        wishlist_product_ids = list(WishlistItem.objects.filter(
            wishlist__user=request.user
        ).values_list('product_id', flat=True))
    else:
        wishlist_product_ids = []

    context = {
        'product': product,
        'images': images_qs,
        'variants': variants,
        'reviews': reviews,
        'review_stats': review_stats,
        'user_review': user_review,
        'review_form': review_form,
        'user_votes': user_votes,
        'related_products': related_products,
        'wishlist_product_ids': wishlist_product_ids,
    }

    return render(request, 'user/products/product_details.html', context)

@require_POST
@login_required
def submit_review(request, product_slug):
    """Handle review submission without images"""
    product = get_object_or_404(Product, slug=product_slug, is_active=True)
    
    # Check if user already reviewed
    if ProductReview.objects.filter(product=product, user=request.user).exists():
        warn_msg = 'You have already reviewed this product.'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': warn_msg})
        messages.warning(request, warn_msg)
        return redirect('products:product_detail_user', product_slug=product_slug)
    
    form = ProductReviewForm(request.POST)
    
    if form.is_valid():
        try:
            with transaction.atomic():
                # Create review
                review = form.save(commit=False)
                review.product = product
                review.user = request.user
                review.save()
                
                success_msg = 'Thank you for your review! It will be visible after approval.'
                redirect_url = reverse('products:product_detail_user', args=[product.slug])
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True, 
                        'message': success_msg,
                        'redirect_url': redirect_url
                    })
                
                messages.success(request, success_msg)
                return redirect('products:product_detail_user', product_slug=product.slug)
                
        except Exception as e:
            logger.error(f"Error saving review: {e}")
            error_msg = 'An error occurred while saving your review.'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': error_msg})
            messages.error(request, error_msg)
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'errors': form.errors})
        messages.error(request, 'Please correct the errors in your review.')
    
    return redirect('products:product_detail_user', product_slug=product_slug)

@require_POST
@login_required
def vote_review(request, review_id):
    """AJAX view for voting on reviews"""
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)
    
    try:
        review = get_object_or_404(ProductReview, id=review_id)
        
        # Handle both JSON and POST data
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                vote_type = data.get('vote_type')
            except json.JSONDecodeError:
                vote_type = request.POST.get('vote_type')
        else:
            vote_type = request.POST.get('vote_type')
        
        if vote_type not in ['helpful', 'not_helpful']:
            return JsonResponse({'success': False, 'error': 'Invalid vote type'}, status=400)
        
        # Check if user already voted
        existing_vote = ReviewVote.objects.filter(review=review, user=request.user).first()
        
        with transaction.atomic():
            if existing_vote:
                # Remove vote if clicking same type again
                if (existing_vote.helpful and vote_type == 'helpful') or \
                   (not existing_vote.helpful and vote_type == 'not_helpful'):
                    existing_vote.delete()
                    # Decrement count
                    if vote_type == 'helpful':
                        review.helpful_votes -= 1
                    else:
                        review.not_helpful_votes -= 1
                    action = 'removed'
                else:
                    # Change vote
                    existing_vote.helpful = vote_type == 'helpful'
                    existing_vote.save()
                    # Update counts
                    if vote_type == 'helpful':
                        review.helpful_votes += 1
                        review.not_helpful_votes = max(0, review.not_helpful_votes - 1)
                    else:
                        review.not_helpful_votes += 1
                        review.helpful_votes = max(0, review.helpful_votes - 1)
                    action = 'changed'
            else:
                # Add new vote
                ReviewVote.objects.create(
                    review=review,
                    user=request.user,
                    helpful=vote_type == 'helpful'
                )
                if vote_type == 'helpful':
                    review.helpful_votes += 1
                else:
                    review.not_helpful_votes += 1
                action = 'added'
            
            review.save()
        
        return JsonResponse({
            'success': True,
            'action': action,
            'helpful_votes': review.helpful_votes,
            'not_helpful_votes': review.not_helpful_votes,
            'user_helpful_vote': vote_type == 'helpful' if action != 'removed' else None
        })
        
    except Exception as e:
        logger.error(f"Error voting on review: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@require_GET
def get_review(request, review_id):
    """Get review data for editing"""
    from .models import ProductReview
    review = get_object_or_404(ProductReview, id=review_id, user=request.user)
    
    # Check if review belongs to user
    if review.user != request.user:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    
    data = {
        'success': True,
        'review': {
            'id': review.id,
            'rating': review.rating,
            'title': review.title,
            'comment': review.comment,
        }
    }
    return JsonResponse(data)

@login_required
@require_POST
def update_review(request, review_id):
    """Update an existing review with robust redirection support"""
    from .models import ProductReview
    from .forms import ProductReviewForm
    
    logger.info(f"Updating review {review_id} for user {request.user}")
    review = get_object_or_404(ProductReview, id=review_id)
    
    if review.user != request.user:
        logger.warning(f"Unauthorized update attempt on review {review_id} by {request.user}")
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)
    
    product = review.product
    form = ProductReviewForm(request.POST, instance=review)
    
    if form.is_valid():
        try:
            review = form.save()
            success_msg = 'Review updated successfully'
            redirect_url = reverse('products:product_detail_user', kwargs={'product_slug': product.slug})
            
            logger.info(f"Review {review_id} updated. Redirecting to {redirect_url}")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': success_msg,
                    'redirect_url': redirect_url
                })
            
            messages.success(request, success_msg)
            return redirect(redirect_url)
        except Exception as e:
            logger.error(f"Error saving updated review {review_id}: {e}")
            return JsonResponse({'success': False, 'message': 'Database error occurred'}, status=500)
    
    logger.debug(f"Form validation failed for review {review_id}: {form.errors}")
    return JsonResponse({
        'success': False,
        'errors': form.errors,
        'message': 'Please correct the highlighted errors.'
    })

@require_POST
@login_required
def delete_review(request, review_id):
    """Delete user's own review"""
    review = get_object_or_404(ProductReview, id=review_id, user=request.user)
    
    try:
        product_slug = review.product.slug
        review.delete()
        messages.success(request, 'Your review has been deleted.')
    except Exception as e:
        logger.error(f"Error deleting review: {e}")
        messages.error(request, 'Error deleting review.')
    
    # If this was an AJAX request, return JSON so frontend can update without redirect
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': 'Review deleted.', 'review_id': review_id})

    return redirect('products:product_detail_user', product_slug=product_slug)

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
        
        if wishlist.items.filter(product=product).exists():
            wishlist.items.filter(product=product).delete()
            return JsonResponse({'success': True, 'status': 'removed'})
        else:
            wishlist.items.create(product=product)
            return JsonResponse({'success': True, 'status': 'added'})
            
    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Product not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Error toggling wishlist: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

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
        logger.error(f"Error adding to cart: {e}")
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

@require_GET
def ajax_reviews(request, product_slug):
    """AJAX endpoint to load more reviews"""
    product = get_object_or_404(Product, slug=product_slug, is_active=True)
    
    # Get filter parameters
    sort_by = request.GET.get('sort', 'recent')
    verified_only = request.GET.get('verified', 'false') == 'true'
    rating_filter = request.GET.get('rating', '')
    page = int(request.GET.get('page', 1))
    per_page = 5
    
    # Get reviews
    reviews = product.reviews.filter(is_approved=True).select_related('user')
    
    # Apply filters
    if verified_only:
        reviews = reviews.filter(verified_purchase=True)
    
    if rating_filter and rating_filter.isdigit():
        rating = int(rating_filter)
        reviews = reviews.filter(rating=rating)
    
    # Apply sorting
    if sort_by == 'helpful':
        reviews = reviews.order_by('-helpful_votes', '-created_at')
    elif sort_by == 'highest':
        reviews = reviews.order_by('-rating', '-created_at')
    elif sort_by == 'lowest':
        reviews = reviews.order_by('rating', '-created_at')
    else:  # recent
        reviews = reviews.order_by('-created_at')
    
    # Paginate
    paginator = Paginator(reviews, per_page)
    
    try:
        reviews_page = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        reviews_page = paginator.page(1)
    
    # Get user votes if authenticated
    user_votes = {}
    if request.user.is_authenticated:
        user_votes = ReviewVote.objects.filter(
            user=request.user,
            review__in=reviews_page.object_list
        ).values('review_id', 'helpful')
        user_votes = {vote['review_id']: vote['helpful'] for vote in user_votes}
    
    # Prepare review data for JSON response
    review_data = []
    for review in reviews_page:
        review_data.append({
            'id': review.id,
            'user_name': review.user.username,
            'user_initial': review.user.username[0].upper() if review.user.username else 'U',
            'rating': review.rating,
            'title': review.title,
            'comment': review.comment,
            'created_at': review.created_at.strftime('%b %d, %Y'),
            'verified_purchase': review.verified_purchase,
            'helpful_votes': review.helpful_votes,
            'not_helpful_votes': review.not_helpful_votes,
            'user_vote': user_votes.get(review.id),
            'is_owner': review.user == request.user,
        })
    
    return JsonResponse({
        'success': True,
        'reviews': review_data,
        'has_next': reviews_page.has_next(),
        'current_page': page,
        'total_pages': paginator.num_pages,
    })