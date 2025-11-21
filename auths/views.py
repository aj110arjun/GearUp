from django.shortcuts import render, redirect
from .forms import UserCreationForm


def signup(request):
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


def signin(request):
    return render(request, 'user/auth/signin.html')
