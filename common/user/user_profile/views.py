# common/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib.auth.views import PasswordChangeView, PasswordChangeDoneView
from django.urls import reverse_lazy

from .forms import UserProfileForm
from common.user.auths.models import UserModel


@never_cache
@login_required(login_url='user_auth:signin')
def profile(request):
    if request.method == 'POST':
        form = UserProfileForm(
            request.POST, 
            request.FILES, 
            instance=request.user
        )
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('profile:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserProfileForm(instance=request.user)
    
    context = {
        'form': form
    }
    return render(request, 'user/profile/profile.html', context)


@never_cache
@login_required(login_url='auth_user:signin')
def order_history(request):
    # You can integrate this with your order app later
    orders = []  # Placeholder for orders
    context = {
        'orders': orders
    }
    return render(request, 'user/order_history.html', context)

class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'user/auth/password_change.html'
    success_url = reverse_lazy('user_auth:password_change_done')

class CustomPasswordChangeDoneView(PasswordChangeDoneView):
    template_name = 'user/auth/password_change_done.html'