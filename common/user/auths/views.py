from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.utils import timezone
from django.contrib.auth.decorators import login_required

from .forms import UserCreationForm, SigninForm, OTPVerificationForm, ProfileUpdateForm, CustomPasswordChangeForm
from .models import UserModel, OTP
from core.services import send_otp_email


@never_cache
def signup(request):
    if request.user.is_authenticated:
        return redirect('user_home:home')

    # Check if user is already in OTP verification stage
    if 'signup_data' in request.session and 'otp_sent' in request.session:
        return redirect('user_auth:verify_otp')

    # Get referral code from URL parameters
    referral_code = request.GET.get('ref', '').strip().upper()

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        
        if form.is_valid():
            # Store form data in session including referral code
            signup_data = {
                'email': form.cleaned_data['email'],
                'first_name': form.cleaned_data['first_name'],
                'last_name': form.cleaned_data['last_name'],
                'password': form.cleaned_data['password1'],
            }
            
            # Store referral code if provided
            referral_code_input = form.cleaned_data.get('referral_code_input', '').strip().upper()
            if referral_code_input:
                signup_data['referral_code'] = referral_code_input
            elif referral_code:
                signup_data['referral_code'] = referral_code
            
            request.session['signup_data'] = signup_data

            # Generate and send OTP
            otp = OTP.create_otp(form.cleaned_data['email'])
            send_otp_email(otp.email, otp.otp_code)

            request.session['otp_sent'] = True
            request.session['otp_email'] = otp.email
            request.session['otp_created'] = otp.created_at.isoformat()

            return redirect('user_auth:verify_otp')
    else:
        form = UserCreationForm()

    context = {
        'form': form,
        'referral_code': referral_code if referral_code else None
    }
    return render(request, 'user/auth/signup.html', context)


@never_cache
def signin(request):
    if request.user.is_authenticated:
        return redirect('user_home:home')  # or 'dashboard'

    if request.method == 'POST':
        form = SigninForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            login(request, user)
            
            # Handle "Remember me" functionality
            if not form.cleaned_data.get('remember_me'):
                # Set session to expire when browser closes
                request.session.set_expiry(0)
            
            
            # Redirect to next page or home
            next_page = request.GET.get('next', 'user_home:home')
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
        return redirect('user_home:home')
    
    if 'signup_data' not in request.session or 'otp_sent' not in request.session:
        messages.error(request, "Session expired. Please sign up again.")
        return redirect('user_auth:signup')
    
    signup_data = request.session['signup_data']
    otp_email = request.session.get('otp_email')
    
    # Get the latest OTP for this email
    try:
        otp = OTP.objects.filter(email=otp_email, is_verified=False).latest('created_at')
    except OTP.DoesNotExist:
        messages.error(request, "OTP expired or invalid. Please sign up again.")
        return redirect('user_auth:signup')
    
    # Get or create referral settings
    try:
        # Try to get existing settings
        settings = ReferralSettings.objects.first()
        if not settings:
            # Create default settings if none exist
            settings = ReferralSettings.objects.create()
    except Exception as e:
        # Fallback if there's any error with the model
        settings = None
    
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
                
                # --- REFERRAL HANDLING ---
                referral_code = signup_data.get('referral_code')
                if referral_code:
                    # Create referral relationship
                    referral = create_referral_relationship(user, referral_code)
                    
                    if referral:
                        # Get signup bonus points from settings or use default
                        if settings:
                            bonus_points = settings.signup_bonus_points
                        else:
                            bonus_points = 100  # Default value
                        
                        # Award signup bonus to referred user
                        user.add_referral_points(
                            bonus_points,
                            f"Signup bonus via referral from {referral.referrer.email}"
                        )
                        
                        # Increment referrer's referral count (this also awards points to referrer)
                        referral.referrer.increment_referral_count()
                        
                        # Mark referral as successful
                        referral.mark_successful()
                        
                        messages.success(request, 
                            f"🎉 Welcome {user.first_name}! You received {bonus_points} bonus points "
                            f"for using a referral code!"
                        )
                    else:
                        messages.warning(request, 
                            "Referral code was invalid or expired, but your account was created successfully."
                        )
                else:
                    # No referral code - award standard signup bonus if settings exist
                    if settings and settings.signup_bonus_points > 0:
                        user.add_referral_points(
                            settings.signup_bonus_points,
                            "Welcome signup bonus"
                        )
                        messages.success(request, 
                            f"Welcome {user.first_name}! You received {settings.signup_bonus_points} points as a welcome bonus!"
                        )
                    elif not settings or settings.signup_bonus_points <= 0:
                        # Award default bonus if no settings or no bonus configured
                        user.add_referral_points(50, "Welcome signup bonus")
                        messages.success(request, 
                            f"Welcome {user.first_name}! You received 50 points as a welcome bonus!"
                        )
                
                # Log the user in
                login(request, user)
                
                # Clean up session
                keys_to_delete = ['signup_data', 'otp_sent', 'otp_email', 'otp_created']
                for key in keys_to_delete:
                    if key in request.session:
                        del request.session[key]
                
                # Redirect to dashboard or home
                return redirect('user_home:home')
            
            else:
                if otp.is_expired():
                    form.add_error('otp_code', "OTP has expired. Please request a new one.")
                    messages.error(request, "OTP has expired. Please request a new one.")
                else:
                    form.add_error('otp_code', "Invalid OTP code. Please try again.")
                    messages.error(request, "Invalid OTP code. Please try again.")
    
    else:
        form = OTPVerificationForm()
    
    # Calculate remaining time for display
    remaining_time = max(0, (otp.expires_at - timezone.now()).total_seconds())
    minutes = int(remaining_time // 60)
    seconds = int(remaining_time % 60)
    
    # Check if user signed up with referral code
    has_referral = 'referral_code' in signup_data and signup_data['referral_code']
    
    # Get referral bonus amount for display
    if settings:
        referral_bonus = settings.signup_bonus_points
    else:
        referral_bonus = 100  # Default value
    
    context = {
        'form': form,
        'email': otp_email,
        'remaining_time': int(remaining_time),
        'timer_display': f"{minutes:02d}:{seconds:02d}",
        'is_expired': otp.is_expired(),
        'has_referral': has_referral,
        'referral_bonus': referral_bonus,
    }
    return render(request, 'user/auth/verify_otp.html', context)


@never_cache
def resend_otp(request):
    if 'signup_data' not in request.session:
        return redirect('user_auth:signup')

    signup_data = request.session['signup_data']
    email = signup_data['email']

    # Generate new OTP
    otp = OTP.create_otp(email)
    send_otp_email(otp.email, otp.otp_code)

    # Update session
    request.session['otp_email'] = otp.email
    request.session['otp_created'] = otp.created_at.isoformat()

    messages.success(request, "New verification code sent!")
    return redirect('user_auth:verify_otp')

# views.py


# auths/views.py - Update the profile views

@login_required
def profile_view(request):
    """Display user profile"""
    # Create form instance with current user data
    form = ProfileUpdateForm(instance=request.user)
    
    return render(request, 'user/profile/profile.html', {
        'user_profile': request.user,
        'form': form  # Pass the form to template
    })

@login_required
def profile_edit(request):
    """Edit user profile"""
    if request.method == 'POST':
        form = ProfileUpdateForm(
            request.POST, 
            request.FILES, 
            instance=request.user
        )
        print(f"Form is valid: {form.is_valid()}")  # Debug
        print(f"Form errors: {form.errors}")  # Debug
        print(f"Form data: {request.POST}")  # Debug
        
        if form.is_valid():
            user = form.save()
            print(f"User saved: {user}")  # Debug
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('user_auth:profile')
        else:
            # Show what specific errors are occurring
            messages.error(request, f'Please correct the errors: {form.errors}')
    else:
        form = ProfileUpdateForm(instance=request.user)
    
    return render(request, 'user/profile/profile.html', {
        'form': form,
        'user_profile': request.user
    })

@login_required
def profile_image_upload(request):
    """Handle profile image upload separately"""
    if request.method == 'POST' and request.FILES.get('profile_image'):
        user = request.user
        user.profile_image = request.FILES['profile_image']
        user.save()
        messages.success(request, 'Profile image updated successfully!')
    
    return redirect('user_auth:profile_edit')  # Fixed redirect

@login_required
def user_logout(request):
    logout(request)
    return redirect('user_home:home')

@login_required
def change_password(request):
    """Change password when user knows current password"""
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Update session to prevent logout
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password has been changed successfully!')
            return redirect('user_auth:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomPasswordChangeForm(request.user)
    
    return render(request, 'user/auth/change_password.html', {
        'form': form,
        'title': 'Change Password'
    })



