from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache

@never_cache
@login_required(login_url='login')
def home(request):
    if not request.user.is_authenticated:
        return redirect('home')
    return render(request, 'registration/home.html')
