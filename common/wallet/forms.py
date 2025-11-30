from django import forms
from .models import Wallet, WalletTransaction

class AddMoneyForm(forms.Form):
    AMOUNT_CHOICES = [
        (100, '₹100'),
        (200, '₹200'),
        (500, '₹500'),
        (1000, '₹1,000'),
        (2000, '₹2,000'),
        (5000, '₹5,000'),
    ]
    
    amount = forms.ChoiceField(
        choices=AMOUNT_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'amount-radio'}),
        label="Select Amount"
    )
    custom_amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        min_value=10,
        max_value=10000,
        label="Or enter custom amount",
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter amount (₹10 - ₹10,000)',
            'min': '10',
            'max': '10000'
        })
    )

class WithdrawalForm(forms.Form):
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=100,
        max_value=10000,
        label="Withdrawal Amount",
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter amount (₹100 - ₹10,000)',
            'min': '100',
            'max': '10000'
        })
    )
    bank_account = forms.CharField(
        max_length=255,
        required=True,
        label="Bank Account Number",
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your bank account number'
        })
    )
    ifsc_code = forms.CharField(
        max_length=20,
        required=True,
        label="IFSC Code",
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter IFSC code'
        })
    )