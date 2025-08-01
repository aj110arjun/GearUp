from django import forms
from .models import Order

class OrderStatusForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['status']
