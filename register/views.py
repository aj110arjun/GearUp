import random

from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from .forms import EmailUserCreationForm
from django.contrib.auth import login, logout
from .forms import EmailLoginForm
from django.contrib.auth.models import User


def login_view(request):
    if request.user.is_authenticated:
        if not request.user.is_staff:
            return redirect('home')
        else:
            messages.error(request, "Unauthorized access.")
            return redirect('admin_login')

    if request.method == 'POST':
        form = EmailLoginForm(request.POST)
        if form.is_valid():
            if form.user.is_staff:
                messages.error(request, 'Admin user cannot login here.')
            else:
                login(request, form.user)
                request.session['user_logged_in'] = True
                return redirect('home')
    else:
        form = EmailLoginForm()

    return render(request, 'registration/login.html', {'form': form})


def signup_view(request):
    if request.method == 'POST':
        form = EmailUserCreationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password1 = form.cleaned_data['password1']
            password2 = form.cleaned_data['password2']
            fullname = form.cleaned_data['fullname']

            otp = str(random.randint(1000, 9999))

            request.session['signup_data'] = {
                'email': email,
                'password1': password1,
                'password2': password2,
                'fullname': fullname,   
                'otp': otp,
            }

            # Send OTP to email
            send_mail(
                subject="Your GearUp OTP Code",
                message=f"Your OTP code is: {otp}",
                from_email='aj110arjun@gmail.com',
                recipient_list=[email],
                fail_silently=False,
            )

            return redirect('verify_otp')
    else:
        form = EmailUserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})

def verify_otp_view(request):
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        data = request.session.get('signup_data')

        if data and data['otp'] == entered_otp:
            email = data['email']
            password = data['password1']
            fullname = data['fullname']

            user = User.objects.create_user(username=email, email=email, password=password, first_name=fullname)
            del request.session['signup_data']  # cleanup
            messages.success(request, "Your account has been verified. Please log in.")
            return redirect('login')
        else:
            messages.error(request, "Invalid OTP. Please try again.")

    return render(request, 'registration/otp/verify_otp.html')

def logout_view(request):
    request.session.flush()
    return redirect('login')

def admin_logout(request):
    request.session.flush()
    return redirect('admin_login')

def admin_login(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin_dashboard')
        else:
            messages.error(request, "Unauthorized access.")
            return redirect('login')

    if request.method == 'POST':
        form = EmailLoginForm(request.POST)
        if form.is_valid():
            if not form.user.is_staff:
                messages.error(request, 'User cannot login here.')
            else:
                login(request, form.user)
                request.session['admin_logged_in'] = True
                return redirect('admin_dashboard')
    else:
        form = EmailLoginForm()

    return render(request, 'custom_admin/login.html', {'form': form})