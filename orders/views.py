from django.shortcuts import render


def view_orders(request):
	return render(request, 'registration/orders/order_history.html')

def track_orders(request):
	return render(request, 'registration/orders/track_orders.html')
