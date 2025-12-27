import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.utils import timezone
from django.contrib.auth.decorators import login_required

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import (
    PasswordResetView, PasswordResetDoneView, 
    PasswordResetConfirmView, PasswordResetCompleteView
)
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.core.mail import send_mail, BadHeaderError
from django.http import HttpResponse
from django.conf import settings
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView
from django.db.models import Q

from .forms import UserCreationForm, SigninForm, OTPVerificationForm, ProfileUpdateForm, CustomPasswordChangeForm, CustomPasswordResetForm, CustomSetPasswordForm, ForgotPasswordForm, ResetPasswordForm, EmailChangeForm, EmailChangeOTPForm
from .models import UserModel, OTP, PasswordResetToken
from core.services import (
    send_otp_email, send_password_reset_otp_email, 
    send_email_change_otp_email, get_login_redirect_url
)


@never_cache
def signup(request):
    if request.user.is_authenticated:
        return redirect(get_login_redirect_url(request.user))

    # Check if user is already in OTP verification stage
    if 'signup_data' in request.session and 'otp_sent' in request.session:
        return redirect('user_auth:verify_otp')

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

            return redirect('user_auth:verify_otp')
    else:
        form = UserCreationForm()

    context = {
        'form': form
    }
    return render(request, 'user/auth/signup.html', context)


@never_cache
def signin(request):
    if request.user.is_authenticated:
        return redirect(get_login_redirect_url(request.user))

    if request.method == 'POST':
        form = SigninForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            login(request, user)
            
            # Handle "Remember me" functionality
            if not form.cleaned_data.get('remember_me'):
                # Set session to expire when browser closes
                request.session.set_expiry(0)
            
            
            # Redirect to next page or home/dashboard
            messages.success(request, f'Successfully signed in as {user.get_full_name() or user.username}')
            next_page = request.GET.get('next')
            return redirect(get_login_redirect_url(user, next_page))
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
        return redirect(get_login_redirect_url(request.user))
    
    if 'signup_data' not in request.session or 'otp_sent' not in request.session:
        return redirect('signup')
    
    signup_data = request.session['signup_data']
    otp_email = request.session.get('otp_email')
    
    # Get the latest OTP for this email
    try:
        otp = OTP.objects.filter(email=otp_email, is_verified=False).latest('created_at')
    except OTP.DoesNotExist:
        messages.error(request, "OTP expired or invalid. Please sign up again.")
        return redirect('user_auth:signup')
    
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
                
                return redirect('user_auth:signin')
            
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




User = get_user_model()

class CustomPasswordResetView(FormView):
    """
    Custom password reset view with email/username input
    """
    template_name = 'user/auth/password_reset.html'
    form_class = CustomPasswordResetForm
    success_url = reverse_lazy('password_reset_done')
    email_template_name = 'auth/password_reset_email.html'
    subject_template_name = 'auth/password_reset_subject.txt'
    
    def form_valid(self, form):
        # Get the email from cleaned data
        email = form.cleaned_data['email_or_username']
        
        # Get user
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # This shouldn't happen due to form validation, but just in case
            messages.error(self.request, "User not found.")
            return redirect('password_reset')
        
        # Generate reset token
        token = PasswordResetToken.objects.create(
            user=user,
            expires_at=timezone.now() + timezone.timedelta(hours=24),
            ip_address=self.get_client_ip(),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Send reset email
        context = {
            'user': user,
            'token': token.token,
            'protocol': 'https' if self.request.is_secure() else 'http',
            'domain': self.request.get_host(),
            'site_name': getattr(settings, 'SITE_NAME', 'Your Site'),
        }
        
        subject = render_to_string(self.subject_template_name, context)
        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())
        
        message = render_to_string(self.email_template_name, context)
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
                html_message=message
            )
            
            # Log the reset request
            self.log_reset_request(user)
            
            messages.success(self.request, 
                "Password reset instructions have been sent to your email."
            )
            
        except BadHeaderError:
            return HttpResponse('Invalid header found.')
        except Exception as e:
            messages.error(self.request, 
                f"Failed to send reset email. Please try again later. Error: {str(e)}"
            )
            return redirect('password_reset')
        
        return super().form_valid(form)
    
    def get_client_ip(self):
        """Get client IP address"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip
    
    def log_reset_request(self, user):
        """Log password reset request (optional)"""
        # You can implement logging here
        pass


class CustomPasswordResetDoneView(TemplateView):
    """Password reset done view"""
    template_name = 'user/auth/password_reset_done.html'


class CustomPasswordResetConfirmView(FormView):
    """
    Custom password reset confirm view with token validation
    """
    template_name = 'user/auth/password_reset_confirm.html'
    form_class = CustomSetPasswordForm
    success_url = reverse_lazy('password_reset_complete')
    
    def dispatch(self, request, *args, **kwargs):
        # Get token from URL
        self.token = kwargs.get('token')
        
        # Validate token
        try:
            self.reset_token = PasswordResetToken.objects.get(token=self.token)
            
            if not self.reset_token.is_valid():
                messages.error(request, "This reset link has expired or has already been used.")
                return redirect('password_reset')
                
        except PasswordResetToken.DoesNotExist:
            messages.error(request, "Invalid reset link. Please request a new one.")
            return redirect('password_reset')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.reset_token.user
        return kwargs
    
    def form_valid(self, form):
        # Save new password
        user = self.reset_token.user
        form.save()
        
        # Mark token as used
        self.reset_token.mark_as_used()
        
        # Log the password change
        self.log_password_change(user)
        
        messages.success(self.request, 
            "Your password has been reset successfully. You can now log in with your new password."
        )
        
        return super().form_valid(form)
    
    def log_password_change(self, user):
        """Log password change (optional)"""
        # You can implement logging here
        pass
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['validlink'] = True
        context['user'] = self.reset_token.user
        return context


class CustomPasswordResetCompleteView(TemplateView):
    """Password reset complete view"""
    template_name = 'user/auth/password_reset_complete.html'


def check_reset_token(request, token):
    """
    API endpoint to check if reset token is valid
    """
    try:
        reset_token = PasswordResetToken.objects.get(token=token)
        
        if reset_token.is_valid():
            return JsonResponse({
                'valid': True,
                'email': reset_token.user.email,
                'username': reset_token.user.username
            })
        else:
            return JsonResponse({
                'valid': False,
                'message': 'Token expired or already used'
            })
            
    except PasswordResetToken.DoesNotExist:
        return JsonResponse({
            'valid': False,
            'message': 'Invalid token'
        })


def resend_reset_email(request):
    """
    View to resend reset email
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        
        try:
            user = User.objects.get(email=email)
            
            # Invalidate old tokens
            PasswordResetToken.objects.filter(
                user=user,
                is_used=False
            ).update(is_used=True)
            
            # Create new token
            token = PasswordResetToken.objects.create(
                user=user,
                expires_at=timezone.now() + timezone.timedelta(hours=24),
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # Send email
            context = {
                'user': user,
                'token': token.token,
                'protocol': 'https' if request.is_secure() else 'http',
                'domain': request.get_host(),
                'site_name': getattr(settings, 'SITE_NAME', 'Your Site'),
            }
            
            message = render_to_string('auth/password_reset_email.html', context)
            subject = f"Password Reset for {context['site_name']}"
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
                html_message=message
            )
            
            messages.success(request, 
                "Password reset instructions have been resent to your email."
            )
            
        except User.DoesNotExist:
            messages.error(request, "No user found with this email.")
        
        return redirect('password_reset')
    
    return redirect('password_reset')




# ============================================
# OTP-Based Password Reset Flow
# ============================================

@never_cache
def forgot_password(request):
    """Step 1: Request password reset OTP"""
    if request.user.is_authenticated:
        return redirect(get_login_redirect_url(request.user))
    
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            
            # Generate and send OTP
            otp = OTP.create_otp(email)
            send_password_reset_otp_email(email, otp.otp_code)
            
            # Store email in session
            request.session['reset_email'] = email
            request.session['reset_otp_sent'] = True
            
            messages.success(request, "Verification code sent to your email!")
            return redirect('user_auth:verify_reset_otp')
    else:
        form = ForgotPasswordForm()
    
    return render(request, 'user/auth/forgot_password.html', {'form': form})


@never_cache
def verify_reset_otp(request):
    """Step 2: Verify OTP for password reset"""
    if request.user.is_authenticated:
        return redirect(get_login_redirect_url(request.user))
    
    if 'reset_email' not in request.session or 'reset_otp_sent' not in request.session:
        messages.error(request, "Please request a password reset first.")
        return redirect('user_auth:forgot_password')
    
    email = request.session['reset_email']
    
    # Get the latest OTP for this email
    try:
        otp = OTP.objects.filter(email=email, is_verified=False).latest('created_at')
    except OTP.DoesNotExist:
        messages.error(request, "OTP expired. Please request a new one.")
        return redirect('user_auth:forgot_password')
    
    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        
        if form.is_valid():
            otp_code = form.cleaned_data['otp_code']
            
            # Verify OTP
            verified_otp, message = OTP.verify_otp(email, otp_code)
            
            if verified_otp:
                # Store verification status in session
                request.session['reset_otp_verified'] = True
                messages.success(request, "OTP verified! Now set your new password.")
                return redirect('user_auth:reset_password')
            else:
                form.add_error('otp_code', message)
    else:
        form = OTPVerificationForm()
    
    # Calculate remaining time
    remaining_time = max(0, (otp.expires_at - timezone.now()).total_seconds())
    minutes = int(remaining_time // 60)
    seconds = int(remaining_time % 60)
    
    context = {
        'form': form,
        'email': email,
        'remaining_time': int(remaining_time),
        'timer_display': f"{minutes:02d}:{seconds:02d}",
        'is_expired': otp.is_expired(),
    }
    return render(request, 'user/auth/verify_reset_otp.html', context)


@never_cache
def resend_reset_otp(request):
    """Resend OTP for password reset"""
    if 'reset_email' not in request.session:
        return redirect('user_auth:forgot_password')
    
    email = request.session['reset_email']
    
    # Generate new OTP
    otp = OTP.create_otp(email)
    send_password_reset_otp_email(email, otp.otp_code)
    
    messages.success(request, "New verification code sent!")
    return redirect('user_auth:verify_reset_otp')


@never_cache
def reset_password(request):
    """Step 3: Set new password after OTP verification"""
    if request.user.is_authenticated:
        return redirect(get_login_redirect_url(request.user))
    
    if 'reset_email' not in request.session or 'reset_otp_verified' not in request.session:
        messages.error(request, "Please verify OTP first.")
        return redirect('user_auth:forgot_password')
    
    email = request.session['reset_email']
    
    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        
        if form.is_valid():
            password = form.cleaned_data['password1']
            
            # Get user and update password
            try:
                user = UserModel.objects.get(email=email)
                user.set_password(password)
                user.save()
                
                # Clean up session
                del request.session['reset_email']
                del request.session['reset_otp_sent']
                del request.session['reset_otp_verified']
                
                messages.success(request, "Password reset successful! You can now sign in with your new password.")
                return redirect('user_auth:signin')
            except UserModel.DoesNotExist:
                messages.error(request, "User not found.")
                return redirect('user_auth:forgot_password')
    else:
        form = ResetPasswordForm()
    
    return render(request, 'user/auth/reset_password.html', {'form': form})


# ============================================
# Email Change Flow
# ============================================

@login_required
@never_cache
def initiate_email_change(request):
    """Step 1: User enters new email address"""
    # Block social (Google) users from changing email
    if request.user.socialaccount_set.exists():
        messages.error(request, "Google accounts cannot change their email address here.")
        return redirect('user_auth:profile')

    if request.method == 'POST':
        form = EmailChangeForm(request.POST, user=request.user)
        if form.is_valid():
            new_email = form.cleaned_data['new_email']
            
            # Generate and send OTP to NEW email
            otp = OTP.create_otp(new_email)
            send_email_change_otp_email(new_email, otp.otp_code)
            
            # Store new email in session
            request.session['new_email_request'] = new_email
            request.session['email_change_otp_sent'] = True
            
            messages.success(request, f"A verification code has been sent to {new_email}")
            return redirect('user_auth:verify_email_change')
    else:
        form = EmailChangeForm(user=request.user)
    
    return render(request, 'user/auth/initiate_email_change.html', {'form': form})


@login_required
@never_cache
def verify_email_change(request):
    """Step 2: Verify OTP sent to new email"""
    if 'new_email_request' not in request.session or 'email_change_otp_sent' not in request.session:
        messages.error(request, "Please initiate an email change request first.")
        return redirect('user_auth:initiate_email_change')
    
    new_email = request.session['new_email_request']
    
    # Get the latest OTP for this email
    try:
        otp = OTP.objects.filter(email=new_email, is_verified=False).latest('created_at')
    except OTP.DoesNotExist:
        messages.error(request, "OTP expired. Please request a new one.")
        return redirect('user_auth:initiate_email_change')
    
    if request.method == 'POST':
        form = EmailChangeOTPForm(request.POST)
        if form.is_valid():
            otp_code = form.cleaned_data['otp_code']
            
            # Verify OTP
            verified_otp, message = OTP.verify_otp(new_email, otp_code)
            
            if verified_otp:
                # Update user email and username
                user = request.user
                user.email = new_email
                user.username = new_email  # Project uses email as username
                user.save()
                
                # Success notification
                messages.success(request, f"Your email has been successfully updated to {new_email}")
                
                # Cleanup session
                del request.session['new_email_request']
                del request.session['email_change_otp_sent']
                
                return redirect('user_auth:profile')
            else:
                form.add_error('otp_code', message)
    else:
        form = EmailChangeOTPForm()
        
    # Calculate remaining time
    remaining_time = max(0, (otp.expires_at - timezone.now()).total_seconds())
    minutes = int(remaining_time // 60)
    seconds = int(remaining_time % 60)
    
    context = {
        'form': form,
        'email': new_email,
        'remaining_time': int(remaining_time),
        'timer_display': f"{minutes:02d}:{seconds:02d}",
        'is_expired': otp.is_expired(),
    }
    return render(request, 'user/auth/verify_email_change_otp.html', context)


@login_required
@never_cache
def resend_email_change_otp(request):
    """Resend OTP for email change"""
    if 'new_email_request' not in request.session:
        return redirect('user_auth:initiate_email_change')
    
    new_email = request.session['new_email_request']
    
    # Generate new OTP
    otp = OTP.create_otp(new_email)
    send_email_change_otp_email(new_email, otp.otp_code)
    
    messages.success(request, "New verification code sent!")
    return redirect('user_auth:verify_email_change')
