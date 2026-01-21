# orders/forms.py
from django import forms
from django.utils import timezone
from .models import Order, Coupon

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
class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = [
            'code', 'description', 'discount_percentage', 'max_uses', 
            'max_uses_per_user', 'minimum_order_amount', 'max_discount_amount',
            'valid_from', 'valid_until', 'is_active'
        ]
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent uppercase font-mono text-lg',
                'placeholder': 'e.g., SAVE20'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'rows': 3,
                'placeholder': 'Brief description of the offer'
            }),
            'discount_percentage': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 pr-12 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'placeholder': '10.00',
                'step': '0.01',
                'min': '0',
                'max': '100'
            }),
            'max_discount_amount': forms.NumberInput(attrs={
                'class': 'w-full pl-10 pr-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'placeholder': '200.00',
                'step': '0.01',
                'min': '0'
            }),
            'minimum_order_amount': forms.NumberInput(attrs={
                'class': 'w-full pl-10 pr-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            }),
            'max_uses': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'placeholder': '0',
                'min': '0'
            }),
            'max_uses_per_user': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'placeholder': '1',
                'min': '0'
            }),
            'valid_from': forms.DateTimeInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'type': 'datetime-local'
            }, format='%Y-%m-%dT%H:%M'),
            'valid_until': forms.DateTimeInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'type': 'datetime-local'
            }, format='%Y-%m-%dT%H:%M'),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'sr-only peer'
            }),
        }

    def clean_code(self):
        code = self.cleaned_data.get('code', '').strip().upper()
        if not code:
            raise forms.ValidationError("Coupon code is required.")
        
        if any(not c.isalnum() for c in code):
            raise forms.ValidationError("Coupon code should only contain letters and numbers.")

        query = Coupon.objects.filter(code=code)
        if self.instance.pk:
            query = query.exclude(pk=self.instance.pk)
        if query.exists():
            raise forms.ValidationError("A coupon with this code already exists.")
            
        return code

    def clean_discount_percentage(self):
        discount = self.cleaned_data.get('discount_percentage')
        if discount is not None:
            if discount < 10:
                raise forms.ValidationError("Discount percentage must be at least 10%.")
            if discount > 90:
                raise forms.ValidationError("Discount percentage cannot exceed 90%.")
        return discount

    def clean_minimum_order_amount(self):
        amount = self.cleaned_data.get('minimum_order_amount')
        if amount is not None and amount < 0:
            raise forms.ValidationError("Minimum order amount cannot be negative.")
        return amount

    def clean_max_discount_amount(self):
        amount = self.cleaned_data.get('max_discount_amount')
        if amount is not None and amount <= 0:
            raise forms.ValidationError("Maximum discount amount must be greater than 0 if specified.")
        return amount

    def clean_max_uses(self):
        uses = self.cleaned_data.get('max_uses')
        if uses is not None and uses < 0:
            raise forms.ValidationError("Maximum uses cannot be negative.")
        return uses

    def clean_max_uses_per_user(self):
        uses = self.cleaned_data.get('max_uses_per_user')
        if uses is not None and uses < 0:
            raise forms.ValidationError("Maximum uses per user cannot be negative.")
        return uses

    def clean(self):
        cleaned_data = super().clean()
        valid_from = cleaned_data.get('valid_from')
        valid_until = cleaned_data.get('valid_until')
        now = timezone.now()

        if valid_from and valid_until:
            if valid_until <= valid_from:
                self.add_error('valid_until', "Expiry date must be after the start date.")
            
            if valid_until <= now:
                self.add_error('valid_until', "Expiry date must be in the future.")

        return cleaned_data
