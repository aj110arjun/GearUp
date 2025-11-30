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
        ('refunded', 'Refunded'),  # Added refunded status
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('partially_refunded', 'Partially Refunded'),  # Added partial refund
    ]

    PAYMENT_METHOD_CHOICES = [
        ('cash_on_delivery', 'Cash On Delivery'),
        ('razorpay', 'RazorPay'),
        ('wallet', 'Wallet'),
        ('card', 'Credit/Debit Card'),  # More specific
        ('upi', 'UPI'),
    ]

    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='orders'
    )
    
    order_number = models.CharField(max_length=20, unique=True)
    
    # Product ForeignKey relationship
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
    
    # Razorpay fields for online payments
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)
    
    # Status
    order_status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    
    # Shipping Address
    shipping_address = models.ForeignKey(
        'address.Address', 
        on_delete=models.PROTECT,  # Changed from SET_NULL to PROTECT to preserve order history
        null=True, 
        blank=True, 
        related_name='shipping_orders'
    )
    
    # Tracking information
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    carrier = models.CharField(max_length=100, blank=True, null=True)
    
    # Customer notes
    customer_notes = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['order_status', 'payment_status']),
        ]
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'

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
            
        # Auto-set timestamps based on status changes
        if self.order_status == 'delivered' and not self.delivered_at:
            self.delivered_at = timezone.now()
        elif self.order_status == 'cancelled' and not self.cancelled_at:
            self.cancelled_at = timezone.now()
            
        super().save(*args, **kwargs)

    def generate_order_number(self):
        timestamp = int(timezone.now().timestamp())
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"ORD{timestamp}{random_str}"

    @property
    def can_be_cancelled(self):
        """Check if order can be cancelled"""
        return self.order_status in ['pending', 'confirmed']

    @property
    def can_be_returned(self):
        """Check if order can be returned (within 7 days of delivery)"""
        if self.order_status == 'delivered' and self.delivered_at:
            return (timezone.now() - self.delivered_at).days <= 7
        return False

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

    @property
    def variant_sku(self):
        return self.variant.sku if self.variant else ''

    def get_status_display_class(self):
        status_classes = {
            'pending': 'bg-yellow-100 text-yellow-800',
            'confirmed': 'bg-blue-100 text-blue-800',
            'processing': 'bg-indigo-100 text-indigo-800',
            'shipped': 'bg-purple-100 text-purple-800',
            'delivered': 'bg-green-100 text-green-800',
            'cancelled': 'bg-red-100 text-red-800',
            'returned': 'bg-orange-100 text-orange-800',
            'refunded': 'bg-gray-100 text-gray-800',
        }
        return status_classes.get(self.order_status, 'bg-gray-100 text-gray-800')

    def get_payment_status_class(self):
        status_classes = {
            'pending': 'bg-yellow-100 text-yellow-800',
            'paid': 'bg-green-100 text-green-800',
            'failed': 'bg-red-100 text-red-800',
            'refunded': 'bg-gray-100 text-gray-800',
            'partially_refunded': 'bg-orange-100 text-orange-800',
        }
        return status_classes.get(self.payment_status, 'bg-gray-100 text-gray-800')

    def mark_as_paid(self, payment_method='razorpay', razorpay_data=None):
        """Mark order as paid and update related fields"""
        self.payment_status = 'paid'
        self.payment_method = payment_method
        self.paid_at = timezone.now()
        
        if razorpay_data:
            self.razorpay_payment_id = razorpay_data.get('razorpay_payment_id')
            self.razorpay_order_id = razorpay_data.get('razorpay_order_id')
            self.razorpay_signature = razorpay_data.get('razorpay_signature')
        
        self.save()

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('orders:order_detail', kwargs={'order_id': self.id})


class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('partially_refunded', 'Partially Refunded'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('razorpay', 'Razorpay'),
        ('cash_on_delivery', 'Cash on Delivery'),
        ('wallet', 'Wallet'),
        ('card', 'Credit/Debit Card'),
        ('upi', 'UPI'),
        ('netbanking', 'Net Banking'),
    ]
    
    # Link to Order
    order = models.ForeignKey(
        'Order', 
        on_delete=models.CASCADE, 
        related_name='payments'
    )
    
    # Razorpay fields
    razorpay_payment_id = models.CharField(max_length=100, unique=True, blank=True, null=True)
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)
    
    # Payment details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='INR')
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    
    # Additional payment details from gateway
    bank = models.CharField(max_length=100, blank=True, null=True)
    wallet = models.CharField(max_length=100, blank=True, null=True)
    card_id = models.CharField(max_length=100, blank=True, null=True)
    vpa = models.CharField(max_length=100, blank=True, null=True, verbose_name='UPI ID')  # For UPI payments
    
    # Refund information
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    refund_id = models.CharField(max_length=100, blank=True, null=True)
    refund_reason = models.TextField(blank=True, null=True)
    
    # Gateway response data (store raw response for debugging)
    gateway_response = models.JSONField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['razorpay_payment_id']),
            models.Index(fields=['order', 'status']),
        ]
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
    
    def __str__(self):
        return f"Payment {self.razorpay_payment_id or self.id} - {self.status}"

    def mark_as_completed(self, gateway_data=None):
        """Mark payment as completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        if gateway_data:
            self.gateway_response = gateway_data
        self.save()

    def initiate_refund(self, amount=None, reason=""):
        """Initiate refund process"""
        refund_amount = amount or self.amount
        self.refund_amount = refund_amount
        self.refund_reason = reason
        self.status = 'refunded' if refund_amount == self.amount else 'partially_refunded'
        self.save()

    @property
    def is_refundable(self):
        """Check if payment can be refunded"""
        return self.status == 'completed' and self.refund_amount < self.amount


class OrderNote(models.Model):
    """Model to track order notes and status changes"""
    NOTE_TYPES = [
        ('system', 'System Note'),
        ('customer', 'Customer Note'),
        ('admin', 'Admin Note'),
        ('support', 'Support Note'),
    ]
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='notes'
    )
    note_type = models.CharField(max_length=20, choices=NOTE_TYPES, default='system')
    content = models.TextField()
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_visible_to_customer = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Note for Order #{self.order.order_number}"