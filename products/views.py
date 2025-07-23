from django.shortcuts import render
from .models import Product


def product_list(request):
	products = Product.objects.all()
	context = {
	'products': products
	}
	return render(request, 'registration/products.html', context)
