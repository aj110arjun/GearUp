from django.shortcuts import render


def signup(request):
    return render(request, 'user/auth/signup.html')


def signin(request):
    return render(request, 'user/auth/signin.html')
