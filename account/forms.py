# accounts/forms.py
from django import forms
from django.contrib.auth.models import User
from .models import AccountInfo

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'email']

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = AccountInfo
        fields = ['profile']
