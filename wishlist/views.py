from django.shortcuts import render


def view_wishlist(request):
	return render(request, 'registration/wishlist.html')
