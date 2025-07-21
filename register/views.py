from django.shortcuts import render, redirect
from Users.models import User
from Users.forms import CustomUserLoginForm
from django.contrib import messages


def user_login(request):
    if request.session.get('user_id'):
        return redirect('home')
    if request.method == 'POST':
        form = CustomUserLoginForm(request.POST)
        if form.is_valid():
            email = request.POST.get('email')
            password = request.POST.get('password')

            if not email or not password:
                error.append('Both Fields are required')
            else:
                try:
                    user = User.objects.get(email=email)
                    if user.is_active:
                        request.session['user_id'] = user.id
                        return redirect('home')
                    else:
                        error.append('Account is inactive')
                except User.DoesNotExist:
                    error.append('Invalid Credentials')
                if error:
                    return render(request, 'user/login.html', {'error': error})
        else:
            form = CustomUserLoginForm()




    return render(request, 'user/login.html')