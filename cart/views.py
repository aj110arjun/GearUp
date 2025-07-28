from django.shortcuts import render

def view_cart(request):
	return render(request, 'registration/cart.html')
