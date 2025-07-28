from django.shortcuts import render, redirect, redirect, get_object_or_404
from .models import Address 
from django.contrib.auth.decorators import login_required
from .forms import AddressForm
from django.contrib import messages


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

def toggle_default_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)

    # Unset all user's addresses
    Address.objects.filter(user=request.user, is_default=True).update(is_default=False)

    # Set the selected address as default
    address.is_default = True
    address.save()

    return redirect('view_address')  

def edit_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)

    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            return redirect('view_address')  # Redirect to address list
    else:
        form = AddressForm(instance=address)

    return render(request, 'registration/address/edit_address.html', {'form': form, 'address': address})

def delete_address(request, address_id):

    address = get_object_or_404(Address, id=address_id, user=request.user)

    if address.is_default:
        messages.warning(request, "You cannot delete your default address. Please set another address as default first.")
        return redirect('view_address')

    address.delete()
    return redirect('view_address')

