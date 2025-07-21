from django.shortcuts import render, redirect
from Users.models import User
from Users.forms import CustomUserLoginForm
from django.contrib import messages


def user_login(request):
    if request.session:
        return redirect('home')
    error = []
    if request.method == 'POST':
        form = CustomUserLoginForm(request.POST)
        if form.is_valid():
            email = request.POST.get('email')
            password = request.POST.get('password')
            try:
                user = User.objects.get(email=email, password=password)
                if user.is_active:
                    request.session['user_id'] = user.id
                    return redirect('home')
                else:
                    error.append("Account is inactive")
            except User.DoesNotExist:
                error.append('Invalid Credentials')
           
        else:
            error.append('Both fields are required')
        if error:
            return render(request, 'user/login.html', {'error':error})

    else:
        form = CustomUserLoginForm()


    return render(request, 'user/login.html')
