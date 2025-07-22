from django.shortcuts import render, redirect
from Users.models import User
from Users.forms import CustomUserLoginForm
from django.contrib import messages


def user_login(request):
    error = []

    if request.session.get('user_id'):
        return redirect('home')

    form = CustomUserLoginForm()

    if request.method == 'POST':
        form = CustomUserLoginForm(request.POST)
        if form.is_valid():
            email = request.POST.get('email')
            password = request.POST.get('password')

            if not email or not password:
                error.append('Both Fields are required')
            elif '@' not in email:
                error.append('Invalid Email')
            else:
                try:
                    user = User.objects.get(email=email, password=password)
                    if user.is_active:
                        request.session['user_id'] = user.id
                        return redirect('home')
                    else:
                        error.append('Account is inactive')
                except User.DoesNotExist:
                    error.append('Invalid Credentials')
        else:
            error.append('Invalid form submission')

    return render(request, 'user/login.html', {'form': form, 'error': error})

def user_signup(request):
    error=[]
    if request.method == 'POST':
        fullname = request.POST.get('fullname')
        email = request.POST.get('email')
        password = request.POST.get('password')
        cpassword = request.POST.get('cpassword')

        if not fullname or not email or not password or not cpassword:
            error.append("All fields are required")
        elif '@' not in email:
            error.append('Invalid email')
        elif cpassword != cpassword:
            error.append("Password Don't Match" )
        elif User.objects.filter(email=email).exists():
            error.append('Email already in use')
        else:
            user = User(fullname=fullname, email=email, password=password)
            user.is_active = True
            user.save()
            messages.success(request,'Account created please login')
            return redirect('user_login')

    return render(request, 'user/signup.html', {'error': error})
