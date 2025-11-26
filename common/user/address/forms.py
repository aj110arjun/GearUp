from django import forms
from .models import Address
import re

class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = [
            'address_type', 'full_name', 'phone_number', 
            'address_line1', 'address_line2', 'city', 
            'state', 'zip_code', 'country', 'instructions', 'is_default'
        ]
        widgets = {
            'address_type': forms.Select(attrs={
                'class': 'form-select',
            }),
            'full_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Full Name'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Phone Number (Optional)'
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
            'instructions': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Delivery instructions (Optional)',
                'rows': 3
            }),
            'is_default': forms.CheckboxInput(attrs={
                'class': 'form-checkbox'
            }),
        }

    def clean_full_name(self):
        full_name = self.cleaned_data.get('full_name', '').strip()
        
        if not full_name:
            raise forms.ValidationError("Full name is required.")
        
        if len(full_name) < 2:
            raise forms.ValidationError("Full name must be at least 2 characters long.")
        
        if len(full_name) > 100:
            raise forms.ValidationError("Full name cannot exceed 100 characters.")
        
        # Check for valid name format (letters, spaces, hyphens, apostrophes)
        if not re.match(r'^[A-Za-z\s\-\'\.]+$', full_name):
            raise forms.ValidationError("Full name can only contain letters, spaces, hyphens, and apostrophes.")
        
        # Check if name has at least two parts (first and last name)
        name_parts = full_name.split()
        if len(name_parts) < 2:
            raise forms.ValidationError("Please enter both first and last name.")
        
        return full_name

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number', '').strip()
        
        if not phone_number:  # Optional field
            return phone_number
        
        # Remove all non-digit characters except +
        cleaned_phone = re.sub(r'[^\d+]', '', phone_number)
        
        # Check if it's a valid phone number format
        # Supports: +1234567890, 1234567890, (123) 456-7890, etc.
        if not re.match(r'^(\+\d{1,3})?\d{7,15}$', cleaned_phone):
            raise forms.ValidationError("Please enter a valid phone number.")
        
        # Check length
        if len(cleaned_phone) < 10 or len(cleaned_phone) > 15:
            raise forms.ValidationError("Phone number must be between 10 and 15 digits.")
        
        return phone_number  # Return original formatted number

    def clean_address_line1(self):
        address_line1 = self.cleaned_data.get('address_line1', '').strip()
        
        if not address_line1:
            raise forms.ValidationError("Address line 1 is required.")
        
        if len(address_line1) < 5:
            raise forms.ValidationError("Address line 1 must be at least 5 characters long.")
        
        if len(address_line1) > 255:
            raise forms.ValidationError("Address line 1 cannot exceed 255 characters.")
        
        # Basic address validation - should contain at least a number and street name
        if not re.match(r'^[0-9].*[A-Za-z]|[A-Za-z].*[0-9]', address_line1):
            raise forms.ValidationError("Please enter a valid street address with building number and street name.")
        
        return address_line1

    def clean_address_line2(self):
        address_line2 = self.cleaned_data.get('address_line2', '').strip()
        
        if address_line2 and len(address_line2) > 255:
            raise forms.ValidationError("Address line 2 cannot exceed 255 characters.")
        
        return address_line2

    def clean_city(self):
        city = self.cleaned_data.get('city', '').strip()
        
        if not city:
            raise forms.ValidationError("City is required.")
        
        if len(city) < 2:
            raise forms.ValidationError("City name must be at least 2 characters long.")
        
        if len(city) > 100:
            raise forms.ValidationError("City name cannot exceed 100 characters.")
        
        # City should only contain letters, spaces, hyphens
        if not re.match(r'^[A-Za-z\s\-\.]+$', city):
            raise forms.ValidationError("City name can only contain letters, spaces, hyphens, and periods.")
        
        return city

    def clean_state(self):
        state = self.cleaned_data.get('state', '').strip()
        
        if not state:
            raise forms.ValidationError("State is required.")
        
        if len(state) < 2:
            raise forms.ValidationError("State name must be at least 2 characters long.")
        
        if len(state) > 100:
            raise forms.ValidationError("State name cannot exceed 100 characters.")
        
        # State should only contain letters and spaces
        if not re.match(r'^[A-Za-z\s]+$', state):
            raise forms.ValidationError("State name can only contain letters and spaces.")
        
        return state

    def clean_zip_code(self):
        zip_code = self.cleaned_data.get('zip_code', '').strip()
        
        if not zip_code:
            raise forms.ValidationError("ZIP code is required.")
        
        # Remove all non-alphanumeric characters
        cleaned_zip = re.sub(r'[^A-Za-z0-9]', '', zip_code)
        
        # US ZIP code validation (5 digits or 5+4 format)
        if re.match(r'^\d{5}$', cleaned_zip) or re.match(r'^\d{5}\d{4}$', cleaned_zip):
            return zip_code
        
        # Canadian postal code validation (A1A 1A1 format)
        if re.match(r'^[A-Za-z]\d[A-Za-z]\d[A-Za-z]\d$', cleaned_zip, re.IGNORECASE):
            return zip_code
        
        # UK postcode validation
        if re.match(r'^[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}$', zip_code, re.IGNORECASE):
            return zip_code
        
        # Generic validation for other countries (at least 3 characters)
        if len(cleaned_zip) >= 3 and len(cleaned_zip) <= 10:
            return zip_code
        
        raise forms.ValidationError("Please enter a valid ZIP/postal code.")

    def clean_country(self):
        country = self.cleaned_data.get('country', '').strip()
        
        if not country:
            raise forms.ValidationError("Country is required.")
        
        if len(country) < 2:
            raise forms.ValidationError("Country name must be at least 2 characters long.")
        
        if len(country) > 100:
            raise forms.ValidationError("Country name cannot exceed 100 characters.")
        
        # Country should only contain letters and spaces
        if not re.match(r'^[A-Za-z\s\-]+$', country):
            raise forms.ValidationError("Country name can only contain letters, spaces, and hyphens.")
        
        return country

    def clean_instructions(self):
        instructions = self.cleaned_data.get('instructions', '').strip()
        
        if instructions and len(instructions) > 500:
            raise forms.ValidationError("Delivery instructions cannot exceed 500 characters.")
        
        return instructions

    def clean(self):
        cleaned_data = super().clean()
        
        # Additional cross-field validation
        address_line1 = cleaned_data.get('address_line1')
        city = cleaned_data.get('city')
        state = cleaned_data.get('state')
        zip_code = cleaned_data.get('zip_code')
        country = cleaned_data.get('country')
        
        # Check if all required address components are present
        required_fields = [address_line1, city, state, zip_code, country]
        if all(required_fields):
            # Validate that the address doesn't already exist for this user
            user = self.instance.user if self.instance.pk else None
            if user:
                existing_address = Address.objects.filter(
                    user=user,
                    address_line1__iexact=address_line1,
                    city__iexact=city,
                    state__iexact=state,
                    zip_code__iexact=zip_code,
                    country__iexact=country,
                    is_active=True
                ).exclude(pk=self.instance.pk if self.instance.pk else None)
                
                if existing_address.exists():
                    raise forms.ValidationError(
                        "This address already exists in your address book."
                    )
        
        return cleaned_data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add required attribute to required fields
        required_fields = ['full_name', 'address_line1', 'city', 'state', 'zip_code', 'country']
        for field_name in required_fields:
            self.fields[field_name].required = True
            
        # Set initial country if not provided
        if not self.instance.pk and not self.data.get('country'):
            self.fields['country'].initial = 'India'