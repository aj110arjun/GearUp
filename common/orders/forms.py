# orders/forms.py
from django import forms
from django.utils import timezone
from .models import Order

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





class OrderStatusForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['order_status']
        widgets = {
            'order_status': forms.Select(attrs={
                'class': 'form-select',
                'style': 'min-width: 200px;'
            }),
        }


class OrderPaymentStatusForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['payment_status']
        widgets = {
            'payment_status': forms.Select(attrs={
                'class': 'form-select',
                'style': 'min-width: 200px;'
            }),
        }


class OrderFilterForm(forms.Form):
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search orders...'
        })
    )
    
    order_status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + Order.ORDER_STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    payment_status = forms.ChoiceField(
        choices=[('', 'All Payment Status')] + Order.PAYMENT_STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    payment_method = forms.ChoiceField(
        choices=[('', 'All Payment Methods')] + Order.PAYMENT_METHOD_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    date_filter = forms.ChoiceField(
        choices=[
            ('', 'All Time'),
            ('today', 'Today'),
            ('week', 'Last 7 Days'),
            ('month', 'Last 30 Days'),
            ('year', 'Last Year'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'placeholder': 'Start Date'
        })
    )
    
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'placeholder': 'End Date'
        })
    )
    
    min_amount = forms.DecimalField(
        required=False,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Min Amount',
            'step': '0.01'
        })
    )
    
    max_amount = forms.DecimalField(
        required=False,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Max Amount',
            'step': '0.01'
        })
    )
    
    sort_by = forms.ChoiceField(
        choices=[
            ('-created_at', 'Newest First'),
            ('created_at', 'Oldest First'),
            ('-total_amount', 'Highest Amount'),
            ('total_amount', 'Lowest Amount'),
            ('order_number', 'Order Number A-Z'),
            ('-order_number', 'Order Number Z-A'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class OrderCancelForm(forms.Form):
    cancellation_reason = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter reason for cancellation...'
        })
    )



class ReturnRequestForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['return_reason', 'return_description']
        widgets = {
            'return_reason': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
            }),
            'return_description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
                'rows': 4,
                'placeholder': 'Please provide details about why you want to return this product...'
            }),
        }