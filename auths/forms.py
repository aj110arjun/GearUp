from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from .models import UserModel

class UserCreationForm(forms.ModelForm):
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
        fields = ['email', 'first_name', 'last_name', 'password']
        # Remove username from fields since we're using email
    
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