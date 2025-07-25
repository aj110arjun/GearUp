from .models import Product, Category
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import ProductForm  
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt



def product_list(request):
	products = Product.objects.filter(is_active=True)
	context = {
	'products': products
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
    return render(request, 'custom_admin/single_product.html', {'product': product})


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


def edit_product(request, slug):
    product = get_object_or_404(Product, slug=slug)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect('admin_product_view', slug=product.slug)
    else:
        form = ProductForm(instance=product)
    return render(request, 'custom_admin/product_edit.html', {'form': form, 'product': product})

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



