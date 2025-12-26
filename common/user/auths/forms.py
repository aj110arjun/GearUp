import re

from django import forms
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserChangeForm, PasswordChangeForm
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from .models import UserModel



class UserCreationForm(BaseUserCreationForm):
    email = forms.EmailField(required=True, label="Email Address")
    first_name = forms.CharField(required=True, max_length=30)
    last_name = forms.CharField(required=True, max_length=30)
    
    class Meta:
        model = UserModel
        fields = ['email', 'first_name', 'last_name']
    
    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        
        if password1:
            # Minimum length check
            if len(password1) < 8:
                raise ValidationError("Password must contain at least 8 characters.")
            
            # Numeric check
            if password1.isdigit():
                raise ValidationError("Your password can't be entirely numeric.")
            
            # Common passwords check
            common_passwords = [
                'password', '12345678', 'qwerty', 'admin', 'welcome',
                'password1', '123456789', 'abc123', 'letmein', 'monkey'
            ]
            if password1.lower() in common_passwords:
                raise ValidationError("Your password can't be a commonly used password.")
            
            # Similarity check (simplified)
            email = self.cleaned_data.get('email', '')
            first_name = self.cleaned_data.get('first_name', '')
            last_name = self.cleaned_data.get('last_name', '')
            
            user_info = [email.split('@')[0], first_name, last_name]
            for info in user_info:
                if info and info.lower() in password1.lower():
                    raise ValidationError("Your password can't be too similar to your other personal information.")
        
        return password1
    
    def clean_email(self):
        email = self.cleaned_data['email']
        if UserModel.objects.filter(email=email).exists():
            raise ValidationError("This email is already registered. Please use a different email.")
        return email
    
    def clean_first_name(self):
        first_name = self.cleaned_data['first_name']
        if not first_name.replace(' ', '').isalpha():
            raise ValidationError("First name should contain only letters.")
        return first_name.strip()
    
    def clean_last_name(self):
        last_name = self.cleaned_data['last_name']
        if not last_name.replace(' ', '').isalpha():
            raise ValidationError("Last name should contain only letters.")
        return last_name.strip()
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class SigninForm(forms.Form):
    email = forms.EmailField(
        required=True,
        label="Email Address",
        widget=forms.EmailInput(attrs={
            'autocomplete': 'email',
            'placeholder': 'Enter your email address'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'current-password',
            'placeholder': 'Enter your password'
        }),
        label="Password"
    )
    remember_me = forms.BooleanField(
        required=False,
        label="Remember me"
    )

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        if email and password:
            # Authenticate using email as username
            user = authenticate(username=email, password=password)
            if user is None:
                raise forms.ValidationError("Invalid email or password. Please try again.")
            elif not user.is_active:
                raise forms.ValidationError("This account is inactive.")

            cleaned_data['user'] = user

        return cleaned_data


class OTPVerificationForm(forms.Form):
    otp_code = forms.CharField(
        max_length=4,
        min_length=4,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter 4-digit OTP',
            'class': 'text-center text-xl tracking-widest'
        }),
        label="Verification Code"
    )

    def clean_otp_code(self):
        otp_code = self.cleaned_data['otp_code']
        if not re.match(r'^\d{4}$', otp_code):
            raise ValidationError("OTP must be exactly 4 digits.")
        return otp_code


class ProfileUpdateForm(UserChangeForm):
    password = None  # Remove password field from the form
    
    class Meta:
        model = UserModel
        fields = [
            'first_name', 'last_name', 'profile_image',
            'bio', 'phone_number', 'location', 'website', 
            'date_of_birth', 'twitter', 'facebook', 'instagram', 'linkedin'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'bio': forms.Textarea(attrs={'rows': 4}),
        }
    
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     # Make email read-only or handle carefully
    #     self.fields['email'].widget.attrs['readonly'] = True

class CustomPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        label="Current Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your current password'
        })
    )
    new_password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new password'
        })
    )
    new_password2 = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password'
        })
    )

    def clean_old_password(self):
        old_password = self.cleaned_data.get("old_password")
        if not self.user.check_password(old_password):
            raise forms.ValidationError("Your current password was entered incorrectly.")
        return old_password
    


# forms.py


User = get_user_model()

class CustomPasswordResetForm(PasswordResetForm):
    """
    Custom password reset form with email/username field
    """
    email_or_username = forms.CharField(
        label=_("Email or Username"),
        max_length=254,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter your email address or username'),
            'autocomplete': 'email'
        })
    )
    
    def clean_email_or_username(self):
        data = self.cleaned_data['email_or_username']
        
        # Check if input is email
        if '@' in data:
            # Try to find by email
            try:
                user = User.objects.get(email=data)
                return user.email
            except User.DoesNotExist:
                raise ValidationError(_("No account found with this email address."))
        else:
            # Try to find by username
            try:
                user = User.objects.get(username=data)
                return user.email
            except User.DoesNotExist:
                raise ValidationError(_("No account found with this username."))
    
    def save(self, **kwargs):
        # Override to use the cleaned email
        self.cleaned_data['email'] = self.cleaned_data['email_or_username']
        return super().save(**kwargs)


class CustomSetPasswordForm(SetPasswordForm):
    """
    Custom set password form with better styling
    """
    new_password1 = forms.CharField(
        label=_("New password"),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter new password'),
            'autocomplete': 'new-password'
        }),
        strip=False,
        help_text=_("Your password must contain at least 8 characters."),
    )
    
    new_password2 = forms.CharField(
        label=_("Confirm new password"),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Confirm new password'),
            'autocomplete': 'new-password'
        }),
    )


class PasswordChangeForm(CustomSetPasswordForm):
    """
    Form for changing password while logged in
    """
    old_password = forms.CharField(
        label=_("Old password"),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter old password'),
            'autocomplete': 'current-password'
        }),
    )
    
    def clean_old_password(self):
        old_password = self.cleaned_data["old_password"]
        if not self.user.check_password(old_password):
            raise ValidationError(
                _("Your old password was entered incorrectly. Please enter it again.")
            )
        return old_password


class ForgotPasswordForm(forms.Form):
    """Form for requesting password reset OTP"""
    email = forms.EmailField(
        required=True,
        label="Email Address",
        widget=forms.EmailInput(attrs={
            'autocomplete': 'email',
            'placeholder': 'Enter your registered email'
        })
    )
    
    def clean_email(self):
        email = self.cleaned_data['email']
        if not UserModel.objects.filter(email=email).exists():
            raise ValidationError("No account found with this email address.")
        return email


class ResetPasswordForm(forms.Form):
    """Form for setting new password after OTP verification"""
    password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Enter new password'
        })
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Confirm new password'
        })
    )
    
    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        
        if password1:
            # Minimum length check
            if len(password1) < 8:
                raise ValidationError("Password must contain at least 8 characters.")
            
            # Numeric check
            if password1.isdigit():
                raise ValidationError("Your password can't be entirely numeric.")
            
            # Common passwords check
            common_passwords = [
                'password', '12345678', 'qwerty', 'admin', 'welcome',
                'password1', '123456789', 'abc123', 'letmein', 'monkey'
            ]
            if password1.lower() in common_passwords:
                raise ValidationError("Your password can't be a commonly used password.")
        
        return password1
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise ValidationError("The two password fields didn't match.")
        
        return cleaned_data


class EmailChangeForm(forms.Form):
    """Form to initiate email change"""
    new_email = forms.EmailField(
        required=True,
        label="New Email Address",
        widget=forms.EmailInput(attrs={
            'placeholder': 'Enter your new email address',
            'class': 'form-control'
        })
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_new_email(self):
        new_email = self.cleaned_data['new_email']
        if self.user and self.user.email == new_email:
            raise ValidationError("New email must be different from your current email.")
        if UserModel.objects.filter(email=new_email).exists():
            raise ValidationError("This email is already registered with another account.")
        return new_email


class EmailChangeOTPForm(OTPVerificationForm):
    """Form to verify OTP for email change"""
    pass
