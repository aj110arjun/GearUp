from django import forms
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate

from .models import UserModel


class UserCreationForm(BaseUserCreationForm):
    email = forms.EmailField(
        required=True,
        label="Email Address"
    )
    password = forms.CharField(
        widget=forms.PasswordInput,
        validators=[validate_password],
        help_text="Your password must contain at least 8 characters."
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput,
        label="Confirm Password"
    )
    
    class Meta:
        model = UserModel
        fields = ['email', 'first_name', 'last_name']
        # Note: 'password' is not in fields because it's an extra field
    
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
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        # Set username as email automatically
        user.username = self.cleaned_data['email']
        user.set_password(self.cleaned_data['password'])
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