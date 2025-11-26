# orders/forms.py
from django import forms

class CheckoutForm(forms.Form):
    shipping_address = forms.IntegerField(required=True)  # Address ID
    payment_method = forms.ChoiceField(
        choices=[
        ('cash_on_delivery', 'Cash On Delivery'),
        ('razorpay', 'RazorPay'),
        ('wallet', 'Wallet'),
    ],
        initial='cash_on_delivery'
    )
    agree_terms = forms.BooleanField(required=True)