from .models import Product
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test


def product_list(request):
	products = Product.objects.all()
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
    return render(request, 'custom_admin/product.html', {'products': products})



