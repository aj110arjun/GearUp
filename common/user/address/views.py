# views.py (create address views)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.http import JsonResponse
from .models import Address
from .forms import AddressForm

@login_required
@never_cache
def address_list(request):
    """Display user's addresses"""
    addresses = Address.objects.filter(user=request.user, is_active=True)
    
    # Check if redirecting from checkout
    from_checkout = request.GET.get('from_checkout') == 'true'
    
    context = {
        'addresses': addresses,
        'active_tab': 'addresses',
        'from_checkout': from_checkout
    }
    return render(request, 'user/address/address_list.html', context)

@login_required
@never_cache
def address_create(request):
    """Create new address"""
    # Get next URL from request (checkout page)
    next_url = request.GET.get('next', None)
    
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(request, 'Address added successfully!')
            
            # Redirect back to checkout if that's where we came from
            if next_url:
                return redirect(next_url)
            return redirect('address:address_list')
    else:
        # Check if user has any active addresses to set initial default checkbox
        has_addresses = Address.objects.filter(user=request.user, is_active=True).exists()
        form = AddressForm(initial={'is_default': not has_addresses})
    
    context = {
        'form': form,
        'title': 'Add New Address',
        'active_tab': 'addresses',
        'next_url': next_url
    }
    return render(request, 'user/address/address_form.html', context)

@login_required
@never_cache
def address_edit(request, pk):
    """Edit existing address"""
    address = get_object_or_404(Address, pk=pk, user=request.user)
    
    # Get next URL from request (checkout page)
    next_url = request.GET.get('next', None)
    
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, 'Address updated successfully!')
            
            # Redirect back to checkout if that's where we came from
            if next_url:
                return redirect(next_url)
            return redirect('address:address_list')
    else:
        form = AddressForm(instance=address)
    
    context = {
        'form': form,
        'title': 'Edit Address',
        'address': address,
        'active_tab': 'addresses',
        'next_url': next_url
    }
    return render(request, 'user/address/address_form.html', context)

@login_required
@never_cache
def address_delete(request, pk):
    """Delete address (soft delete)"""
    address = get_object_or_404(Address, pk=pk, user=request.user)
    
    # Get next URL from request (checkout page)
    next_url = request.GET.get('next', None)
    
    if request.method == 'POST':
        # Soft delete by setting is_active to False
        address.is_active = False
        address.save()
        
        # If we deleted the default address, set a new default
        if address.is_default:
            new_default = Address.objects.filter(
                user=request.user, 
                is_active=True
            ).first()
            if new_default:
                new_default.is_default = True
                new_default.save()
        
        messages.success(request, 'Address deleted successfully!')
        
        # Redirect back to checkout if that's where we came from
        if next_url:
            return redirect(next_url)
        return redirect('address:address_list')
    
    context = {
        'address': address,
        'active_tab': 'addresses',
        'next_url': next_url
    }
    return render(request, 'user/address/address_confirm_delete.html', context)

@login_required
@never_cache
def set_default_address(request, pk):
    """Set address as default"""
    address = get_object_or_404(Address, pk=pk, user=request.user)
    
    # Get next URL from request (checkout page)
    next_url = request.GET.get('next', None)
    
    if request.method == 'POST':
        address.is_default = True
        address.save()
        messages.success(request, 'Default address updated successfully!')
    
    # Redirect back to checkout if that's where we came from
    if next_url:
        return redirect(next_url)
    return redirect('address:address_list')


@login_required
@never_cache
def get_address_json(request, pk):
    """Get address data as JSON (for AJAX requests)"""
    address = get_object_or_404(Address, pk=pk, user=request.user)
    
    data = {
        'id': address.id,
        'full_name': address.full_name,
        'phone_number': address.phone_number,
        'address_line1': address.address_line1,
        'address_line2': address.address_line2,
        'city': address.city,
        'state': address.state,
        'zip_code': address.zip_code,
        'country': address.country,
        'instructions': address.instructions,
        'formatted_address': address.get_formatted_address(),
    }
    
    return JsonResponse(data)