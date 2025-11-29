# orders/models.py
from django.db import models
from django.conf import settings
from decimal import Decimal
import random
import string
from django.utils import timezone

User = settings.AUTH_USER_MODEL

class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('returned', 'Returned'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('cash_on_delivery', 'Cash On Delivery'),
        ('razorpay', 'RazorPay'),
        ('wallet', 'Wallet'),
    ]

    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='orders'
    )
    
    order_number = models.CharField(max_length=20, unique=True)
    
    # Product ForeignKey relationship - No duplicate data
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.PROTECT,
        related_name='orders',
        verbose_name='Product'
    )
    
    # Variant ForeignKey to track which variant was ordered
    variant = models.ForeignKey(
        'products.ProductVariant',
        on_delete=models.PROTECT,
        related_name='orders',
        verbose_name='Product Variant',
        null=True,
        blank=True
    )
    
    # Order-specific pricing (snapshot at time of order)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    
    # Status
    order_status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    
    # Shipping Address
    shipping_address = models.ForeignKey(
        'address.Address', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='shipping_orders'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.order_number} - {self.product.name}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        
        # Calculate prices if not set
        if not self.subtotal and self.unit_price is not None and self.quantity is not None:
            self.subtotal = self.unit_price * self.quantity
        elif not self.subtotal:
            self.subtotal = Decimal('0.00')
        
        if not self.total_amount:
            tax_amount = self.tax_amount if self.tax_amount is not None else Decimal('0.00')
            shipping_cost = self.shipping_cost if self.shipping_cost is not None else Decimal('0.00')
            self.total_amount = self.subtotal + tax_amount + shipping_cost
            
        super().save(*args, **kwargs)

    def generate_order_number(self):
        timestamp = int(timezone.now().timestamp())
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"ORD{timestamp}{random_str}"

    @property
    def can_be_cancelled(self):
        return self.order_status in ['pending', 'confirmed']

    # Product properties - fetch from related product
    @property
    def product_name(self):
        return self.product.name

    @property
    def product_image(self):
        return self.product.image.url if self.product.image else ''

    @property
    def product_sku(self):
        return self.product.sku

    @property
    def variant_size(self):
        return self.variant.size if self.variant else ''

    @property
    def variant_color(self):
        return self.variant.color if self.variant else ''

    def get_status_display_class(self):
        status_classes = {
            'pending': 'bg-yellow-100 text-yellow-800',
            'confirmed': 'bg-blue-100 text-blue-800',
            'processing': 'bg-indigo-100 text-indigo-800',
            'shipped': 'bg-purple-100 text-purple-800',
            'delivered': 'bg-green-100 text-green-800',
            'cancelled': 'bg-red-100 text-red-800',
        }
        return status_classes.get(self.order_status, 'bg-gray-100 text-gray-800')

    def get_payment_status_class(self):
        status_classes = {
            'pending': 'bg-yellow-100 text-yellow-800',
            'paid': 'bg-green-100 text-green-800',
            'failed': 'bg-red-100 text-red-800',
            'refunded': 'bg-gray-100 text-gray-800',
        }
        return status_classes.get(self.payment_status, 'bg-gray-100 text-gray-800')