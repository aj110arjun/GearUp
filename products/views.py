import os

from .models import Product, Category, ProductImage, ProductImage
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import ProductForm, AdditionalImageForm
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.conf import settings




def product_list(request):
    products = Product.objects.filter(is_active=True)

    # Get filters
    search_query = request.GET.get('search', '')
    sort_by = request.GET.get('sort', '')
    price_min = request.GET.get('min_price', '')
    price_max = request.GET.get('max_price', '')

    # Search by name
    if search_query:
        products = products.filter(name__icontains=search_query)

    # Filter by price range
    if price_min:
        products = products.filter(price__gte=price_min)
    if price_max:
        products = products.filter(price__lte=price_max)

    # Sorting
    if sort_by == 'price_asc':
        products = products.order_by('price')
    elif sort_by == 'price_desc':
        products = products.order_by('-price')
    elif sort_by == 'name_asc':
        products = products.order_by('name')
    elif sort_by == 'name_desc':
        products = products.order_by('-name')

    context = {
        'products': products,
        'search_query': search_query,
        'sort_by': sort_by,
        'min_price': price_min,
        'max_price': price_max,
    }
    return render(request, 'registration/products.html', context)



def product_detail(request, slug):
	product = get_object_or_404(Product, slug=slug)
	return render(request, 'registration/single_product.html', {'product': product})


def staff_required(user):
    return user.is_authenticated and user.is_staff


@login_required(login_url='admin_login')
@user_passes_test(staff_required, login_url='admin_login')
def admin_product_view(request, slug):
    product = get_object_or_404(Product, slug=slug)
    additional_images = product.additional_images.all()
    context = {
    'product': product,
    'additional_images': additional_images,
    }
    return render(request, 'custom_admin/single_product.html', context)


@login_required(login_url='admin_login')
@user_passes_test(staff_required, login_url='admin_login')
def admin_product_list(request):
    products = Product.objects.all()

    # Filters
    category   = request.GET.get('category')
    min_price  = request.GET.get('min_price')
    max_price  = request.GET.get('max_price')
    in_stock   = request.GET.get('in_stock')
    search     = request.GET.get('search')
    sort       = request.GET.get('sort')        # ← New

    if category:
        products = products.filter(category__id=category)
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)
    if in_stock == 'true':
        products = products.filter(stock__gt=0)
    elif in_stock == 'false':
        products = products.filter(stock__lte=0)
    if search:
        products = products.filter(name__icontains=search)

    # Sorting
    if sort == 'name_asc':
        products = products.order_by('name')
    elif sort == 'name_desc':
        products = products.order_by('-name')
    elif sort == 'price_asc':
        products = products.order_by('price')
    elif sort == 'price_desc':
        products = products.order_by('-price')
    else:
        # default sort (e.g. newest first)
        products = products.order_by('-product_id')

    categories = Category.objects.all()

    context = {
        'products':   products,
        'categories': categories,
        'filters': {
            'category':  category,
            'min_price': min_price,
            'max_price': max_price,
            'in_stock':  in_stock,
            'search':    search,
            'sort':      sort,     # ← Pass back to template
        }
    }
    return render(request, 'custom_admin/product.html', context)


@login_required
def edit_product(request, slug):
    product = get_object_or_404(Product, slug=slug)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)

        # handle additional images
        files = request.FILES.getlist('additional_images')
        if form.is_valid():
            form.save()
            for file in files:
                ProductImage.objects.create(product=product, image=file)
            return redirect('admin_product_view', slug=product.slug)
    else:
        form = ProductForm(instance=product)
    
    context = {
        'form': form,
        'product': product,
        'additional_images': product.additional_images.all(),
    }
    return render(request, 'custom_admin/product_edit.html', context)


def delete_product(request, slug):
    product = get_object_or_404(Product, slug=slug)
    
    if request.method == "POST":
        product.delete()
        return redirect('admin_product_list')  
    
    return render(request, 'custom_admin/confirm_delete.html', {'product': product})


def toggle_product_status(request, slug):
    product = get_object_or_404(Product, slug=slug)
    product.is_active = not product.is_active
    product.save()

    if product.is_active:
        messages.success(request, f"Product '{product.name}' is now active.")
    else:
        messages.warning(request, f"Product '{product.name}' is now blocked.")

    return redirect('admin_product_view', slug=slug)

def add_product_view(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        new_cat_name = request.POST.get('new_category')

        if new_cat_name:
            # Capitalize and check for duplicates
            category, created = Category.objects.get_or_create(name=new_cat_name.strip().title())
            post_data = request.POST.copy()
            post_data['category'] = category.id
            form = ProductForm(post_data, request.FILES)

        if form.is_valid():
            form.save()
            messages.success(request, "Product added successfully.")
            return redirect('admin_product_list')
    else:
        form = ProductForm()

    return render(request, 'custom_admin/add_product.html', {'form': form})

    
@csrf_exempt
def ajax_add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            return JsonResponse({
                'success': True,
                'id': category.id,
                'name': category.name
            })
        return JsonResponse({'success': False, 'errors': form.errors})


def delete_main_image(request, slug):
    product = get_object_or_404(Product, slug=slug)
    if product.image:
        image_path = product.image.path
        product.image.delete()
        product.save()
        if os.path.exists(image_path):
            os.remove(image_path)
        messages.success(request, "Main image deleted.")
    return redirect('admin_product_view', slug=slug)

def delete_additional_image(request, image_id):
    image = get_object_or_404(ProductImage, id=image_id)
    product_slug = image.product.slug
    image.delete()
    return redirect('edit_product', slug=product_slug)



