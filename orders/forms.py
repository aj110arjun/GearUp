from django import forms
from .models import Order

class OrderStatusForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['status']
        
class ReturnOrderForm(forms.Form):
    reason = forms.CharField(
        label="Return Reason",
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Please explain why you want to return this order..."}),
        required=True
    )