from django.shortcuts import render, redirect
from .models import Address 
from django.contrib.auth.decorators import login_required
from .forms import AddressForm


def view_address(request):
	addresses = Address.objects.filter(user=request.user)
	context={
	'addresses': addresses,
	}
	return render(request, 'registration/address/address.html', context)

@login_required
def add_address(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            if not Address.objects.filter(user=request.user).exists():
                address.is_default = True
            address.save()
            return redirect('view_address')
    else:
        form = AddressForm()
    return render(request, 'registration/address/add_address.html', {'form': form, 'form_title': 'Add Address'})

