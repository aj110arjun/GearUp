from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from django.views.decorators.cache import never_cache

from .forms import UserCreationForm, SigninForm

@never_cache
def signup(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = UserCreationForm()
    
    context = {
        'form': form
    }
    return render(request, 'user/auth/signup.html', context)


@never_cache
def signin(request):
    if request.user.is_authenticated:
        return redirect('home')  # or 'dashboard'

    if request.method == 'POST':
        form = SigninForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            login(request, user)
            
            # Handle "Remember me" functionality
            if not form.cleaned_data.get('remember_me'):
                # Set session to expire when browser closes
                request.session.set_expiry(0)
            
            messages.success(request, f"Welcome back, {user.first_name}!")
            
            # Redirect to next page or home
            next_page = request.GET.get('next', 'home')
            return redirect(next_page)
    else:
        form = SigninForm()

    context = {
        'form': form,
        'title': 'Sign In'
    }
    return render(request, 'user/auth/signin.html', context)
