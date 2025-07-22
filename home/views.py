from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required


@login_required(login_url='login')
def home(request):
    if not request.user.is_authenticated:
        return redirect('home')
    return render(request, 'registration/home.html')
