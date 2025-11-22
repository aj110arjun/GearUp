from django import forms
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError


class AdminSigninForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        required=True,
        label="Username",
        widget=forms.TextInput(attrs={
            'autocomplete': 'username',
            'placeholder': 'Enter your username',
            'class': 'w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'current-password',
            'placeholder': 'Enter your password',
            'class': 'w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
        }),
        label="Password"
    )
    remember_me = forms.BooleanField(
        required=False,
        label="Remember me"
    )

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')

        if username and password:
            # Authenticate using username and password
            user = authenticate(username=username, password=password)
            
            if user is None:
                raise ValidationError("Invalid username or password. Please try again.")
            elif not user.is_active:
                raise ValidationError("This account is inactive.")
            elif not user.is_staff and not user.is_superuser:
                raise ValidationError("Access denied. Admin privileges required.")
            
            cleaned_data['user'] = user

        return cleaned_data