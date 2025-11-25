from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.utils import timezone
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required

from .forms import UserCreationForm, SigninForm, OTPVerificationForm, CustomPasswordChangeForm
from .models import UserModel, OTP
from core.services import send_otp_email


@never_cache
def signup(request):
    if request.user.is_authenticated:
        return redirect('home')

    # Check if user is already in OTP verification stage
    if 'signup_data' in request.session and 'otp_sent' in request.session:
        return redirect('verify_otp')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)

        if form.is_valid():
            # Store form data in session
            request.session['signup_data'] = {
                'email': form.cleaned_data['email'],
                'first_name': form.cleaned_data['first_name'],
                'last_name': form.cleaned_data['last_name'],
                'password': form.cleaned_data['password1'],
            }

            # Generate and send OTP
            otp = OTP.create_otp(form.cleaned_data['email'])  # Fixed method name
            send_otp_email(otp.email, otp.otp_code)

            request.session['otp_sent'] = True
            request.session['otp_email'] = otp.email
            request.session['otp_created'] = otp.created_at.isoformat()

            messages.success(request, f"Verification code sent to {form.cleaned_data['email']}")  # Fixed
            return redirect('verify_otp')
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


@never_cache
def verify_otp(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if 'signup_data' not in request.session or 'otp_sent' not in request.session:
        return redirect('signup')
    
    signup_data = request.session['signup_data']
    otp_email = request.session.get('otp_email')
    
    # Get the latest OTP for this email
    try:
        otp = OTP.objects.filter(email=otp_email, is_verified=False).latest('created_at')
    except OTP.DoesNotExist:
        messages.error(request, "OTP expired or invalid. Please sign up again.")
        return redirect('signup')
    
    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        
        if form.is_valid():
            otp_code = form.cleaned_data['otp_code']
            
            # Verify OTP
            if otp.otp_code == otp_code and not otp.is_expired():
                # Mark OTP as verified
                otp.is_verified = True
                otp.save()
                
                # Create user account
                user = UserModel(
                    email=signup_data['email'],
                    username=signup_data['email'],
                    first_name=signup_data['first_name'],
                    last_name=signup_data['last_name'],
                )
                user.set_password(signup_data['password'])
                user.save()
                
                # Clean up session
                del request.session['signup_data']
                del request.session['otp_sent']
                del request.session['otp_email']
                del request.session['otp_created']
                
                messages.success(request, "Account created successfully! You can now sign in.")
                return redirect('signin')
            
            else:
                if otp.is_expired():
                    form.add_error('otp_code', "OTP has expired. Please request a new one.")
                else:
                    form.add_error('otp_code', "Invalid OTP code. Please try again.")
    
    else:
        form = OTPVerificationForm()
    
    # Calculate remaining time
    remaining_time = max(0, (otp.expires_at - timezone.now()).total_seconds())
    minutes = int(remaining_time // 60)
    seconds = int(remaining_time % 60)
    
    context = {
        'form': form,
        'email': otp_email,
        'remaining_time': int(remaining_time),
        'timer_display': f"{minutes:02d}:{seconds:02d}",
        'is_expired': otp.is_expired(),
    }
    return render(request, 'user/auth/verify_otp.html', context)


@never_cache
def resend_otp(request):
    if 'signup_data' not in request.session:
        return redirect('signup')

    signup_data = request.session['signup_data']
    email = signup_data['email']

    # Generate new OTP
    otp = OTP.create_otp(email)
    send_otp_email(otp.email, otp.otp_code)

    # Update session
    request.session['otp_email'] = otp.email
    request.session['otp_created'] = otp.created_at.isoformat()

    messages.success(request, "New verification code sent!")
    return redirect('verify_otp')

@never_cache
@login_required(login_url='auth_user:signin')
def change_password(request):
    if not request.user.has_usable_password():
        messages.error(request, "Password change is not available for social accounts.")
        return redirect('profile:profile')
    
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your password has been changed successfully!')
            return redirect('profile:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomPasswordChangeForm(request.user)
    
    context = {
        'form': form
    }
    return render(request, 'user/auth/change_password.html', context)


@login_required
def custom_logout(request):
    logout(request)
    return redirect('/')


