from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login

def admin_login(request):
	if request.user.is_authenticated and request.user.is_staff:
		return redirect('dashboard')

	error={}
	if request.method == 'POST':
		username = request.POST.get('username')
		password = request.POST.get('password')
		user = authenticate(request, username=username, password=password)

		if user is not None and user.is_staff:
			login(request, user)
			return redirect('dashboard')
		else:
			error['user'] = 'Invalid Credentials'

	return render(request, 'custom_admin/login.html', {'error': error})