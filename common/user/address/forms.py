# common/user/address/forms.py
import re
from django import forms
from django.core.exceptions import ValidationError
from .models import Address

class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = [
            'full_name',
            'phone_number', 
            'address_line1',
            'address_line2',
            'city',
            'state',
            'zip_code',
            'country',
            'address_type',
            'instructions',
            'is_default'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Full Name'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Phone Number'
            }),
            'address_line1': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Address Line 1'
            }),
            'address_line2': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Address Line 2 (Optional)'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'City'
            }),
            'state': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'State'
            }),
            'zip_code': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'ZIP Code'
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Country'
            }),
            'address_type': forms.Select(attrs={
                'class': 'form-input'
            }),
            'instructions': forms.Textarea(attrs={
                'class': 'form-input',
                'placeholder': 'Delivery instructions (optional) - Minimum 5 words required',
                'rows': 3
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make instructions field required for validation
        self.fields['instructions'].required = False

    def clean_full_name(self):
        full_name = self.cleaned_data.get('full_name', '').strip()
        if not full_name:
            raise ValidationError("Full name is required.")
        
        # Check for special characters (only allow letters, spaces, hyphens, and apostrophes)
        if re.search(r'[!@#$%^&*()_+=<>?/\\|\[\]{}~`]', full_name):
            raise ValidationError("Full name should not contain special characters. Only letters, spaces, hyphens (-), and apostrophes (') are allowed.")
        
        # Check for numbers
        if re.search(r'\d', full_name):
            raise ValidationError("Full name should not contain numbers.")
        
        # Minimum 2 words check
        if len(full_name.split()) < 2:
            raise ValidationError("Please enter your full name (first and last name).")
        
        return full_name

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number', '').strip()
        if phone_number:
            # Remove spaces, hyphens, and parentheses for validation
            clean_phone = re.sub(r'[\s\-\(\)]', '', phone_number)
            
            # Check if it contains only numbers and optional + at start
            if not re.match(r'^\+?\d+$', clean_phone):
                raise ValidationError("Phone number should contain only numbers and optional country code with +.")
            
            # Check length (minimum 10 digits excluding +)
            digits_only = clean_phone.lstrip('+')
            if len(digits_only) < 10:
                raise ValidationError("Phone number should be at least 10 digits long.")
            
            if len(digits_only) > 15:
                raise ValidationError("Phone number is too long.")
        
        return phone_number

    def clean_address_line1(self):
        address_line1 = self.cleaned_data.get('address_line1', '').strip()
        if not address_line1:
            raise ValidationError("Address line 1 is required.")
        
        # Check for problematic special characters but allow common address characters
        if re.search(r'[!$%^*()_+=<>?/\\|\[\]{}~`]', address_line1):
            raise ValidationError("Address line 1 contains invalid characters. Only letters, numbers, spaces, hyphens, commas, periods, #, and apostrophes are allowed.")
        
        return address_line1

    def clean_address_line2(self):
        address_line2 = self.cleaned_data.get('address_line2', '').strip()
        if address_line2:
            # Check for problematic special characters but allow common address characters
            if re.search(r'[!$%^*()_+=<>?/\\|\[\]{}~`]', address_line2):
                raise ValidationError("Address line 2 contains invalid characters. Only letters, numbers, spaces, hyphens, commas, periods, #, and apostrophes are allowed.")
        
        return address_line2

    def clean_city(self):
        city = self.cleaned_data.get('city', '').strip()
        if not city:
            raise ValidationError("City is required.")
        
        # Check for special characters and numbers
        if re.search(r'[!@#$%^&*()_+=<>?/\\|\[\]{}~`\d]', city):
            raise ValidationError("City should contain only letters, spaces, and hyphens.")
        
        return city

    def clean_state(self):
        state = self.cleaned_data.get('state', '').strip()
        if not state:
            raise ValidationError("State is required.")
        
        # Check for special characters and numbers
        if re.search(r'[!@#$%^&*()_+=<>?/\\|\[\]{}~`\d]', state):
            raise ValidationError("State should contain only letters, spaces, and hyphens.")
        
        return state

    def clean_zip_code(self):
        zip_code = self.cleaned_data.get('zip_code', '').strip()
        if not zip_code:
            raise ValidationError("ZIP code is required.")
        
        # Allow only numbers and hyphens for ZIP codes
        if not re.match(r'^[\d\-]+$', zip_code):
            raise ValidationError("ZIP code should contain only numbers and hyphens.")
        
        # Remove hyphens and check length
        digits_only = re.sub(r'[^\d]', '', zip_code)
        if len(digits_only) < 5:
            raise ValidationError("ZIP code should be at least 5 digits long.")
        
        if len(digits_only) > 10:
            raise ValidationError("ZIP code is too long.")
        
        return zip_code

    def clean_country(self):
        country = self.cleaned_data.get('country', '').strip()
        if not country:
            raise ValidationError("Country is required.")
        
        # Check for special characters and numbers
        if re.search(r'[!@#$%^&*()_+=<>?/\\|\[\]{}~`\d]', country):
            raise ValidationError("Country should contain only letters, spaces, and hyphens.")
        
        return country

    def clean_instructions(self):
        instructions = self.cleaned_data.get('instructions', '').strip()
        if instructions:
            # Count words (split by spaces and filter out empty strings)
            words = [word for word in instructions.split() if word.strip()]
            
            if len(words) < 5:
                raise ValidationError("Delivery instructions must contain at least 5 words.")
            
            # Check for excessive special characters
            if re.search(r'[!$%^&*()_+=<>?/\\|\[\]{}~`]{2,}', instructions):
                raise ValidationError("Delivery instructions contain too many consecutive special characters.")
        
        return instructions

    def clean(self):
        cleaned_data = super().clean()
        
        # Additional validation that requires multiple fields
        address_line1 = cleaned_data.get('address_line1')
        city = cleaned_data.get('city')
        state = cleaned_data.get('state')
        zip_code = cleaned_data.get('zip_code')
        
        # Ensure all required address components are present
        if address_line1 and not city:
            self.add_error('city', 'City is required when address is provided.')
        
        if address_line1 and not state:
            self.add_error('state', 'State is required when address is provided.')
        
        if address_line1 and not zip_code:
            self.add_error('zip_code', 'ZIP code is required when address is provided.')
        
        return cleaned_data