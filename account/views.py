from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from .models import AccountInfo


@never_cache
@login_required(login_url='login')
def account_info(request):
    account, created = AccountInfo.objects.get_or_create(
        user=request.user,
        defaults={
            'address': 'Not set',
            'city': 'Not set',
            'landmark': 'Not set',
            'street': 'Not set',
            'pincode': '000000',
        }
    )
    return render(request, 'registration/account.html', {'account': account})

@login_required(login_url='login')
def edit_info(request):
	user = request.user
	account, created = AccountInfo.objects.get_or_create(user=request.user)
	if request.method == 'POST':
		error={}
		account.address = request.POST.get('address')
		account.city = request.POST.get('city')
		account.street = request.POST.get('street')
		account.landmark = request.POST.get('landmark')
		account.pincode = request.POST.get('pincode')

		user.first_name = request.POST.get('first_name')
		if "1234567890" in user.first_name:
			error['first_name'] = 'Fullname only contain characters'

		if not account.address or not account.city or not account.street or not account.landmark or not account.pincode:
			error['address'] = 'Address cannot be empty'
			error['city'] = 'City cannot be empty'
			error['street'] = 'Street cannot be empty'
			error['landmark'] = 'Landmark cannot be empty'
		try:
			int(account.pincode)
		except ValueError:
			error['pincode'] = 'Not a valid pincode'
		if error:
			return render(request, 'registration/edit_account.html', {"error": error})

		account.save()
		user.save()
		return redirect('account')
	return render(request, 'registration/edit_account.html', {'account': account, 'user': user})

