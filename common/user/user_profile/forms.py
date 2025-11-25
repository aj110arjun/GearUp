# common/forms.py
from django import forms
from common.user.auths.models import UserModel

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserModel
        fields = ['first_name', 'last_name', 'phone_number', 'date_of_birth', 'profile_image']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add CSS classes to form fields
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-input'
            })