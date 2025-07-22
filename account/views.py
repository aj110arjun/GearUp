from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required(login_url='login')
def account_info(request):
	return render(request, 'registration/account.html')

