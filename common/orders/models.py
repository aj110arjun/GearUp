import random
import string
import uuid

from django.db import models
from django.conf import settings
from decimal import Decimal
from django.utils import timezone
from django.utils.text import slugify

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

    RETURN_REASON_CHOICES = [
        ('product_defective', 'Product Defective/Damaged'),
        ('wrong_item', 'Wrong Item Received'),
        ('size_issue', 'Size Not Fit'),
        ('color_issue', 'Color Not as Expected'),
        ('quality_issue', 'Quality Issue'),
        ('not_as_described', 'Not as Described'),
        ('changed_mind', 'Changed Mind'),
        ('duplicate_order', 'Duplicate Order'),
        ('late_delivery', 'Late Delivery'),
        ('other', 'Other'),
    ]
    CANCELLATION_REASON_CHOICES = [
        ('mind_changed', 'Changed My Mind'),
        ('wrong_product', 'Ordered Wrong Product'),
        ('price_issue', 'Found Better Price Elsewhere'),
        ('shipping_delay', 'Delivery Taking Too Long'),
        ('payment_issue', 'Payment Problem'),
        ('duplicate_order', 'Duplicate Order'),
        ('coupon_issue', 'Forgot to Apply Coupon'),
        ('other', 'Other (Please Specify)'),
    ]

    order_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        unique=True
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='orders'
    )
    
    order_number = models.CharField(max_length=20, unique=True)
    slug = models.SlugField(max_length=225, unique=True, blank=True)
    
    # Product relationship - using ForeignKey
    product = models.ForeignKey(
        'products.Product',  # Update with your actual product app name
        on_delete=models.PROTECT,  # Prevent deletion if orders exist
        related_name='orders'
    )
    
    # Variant relationship (if you have product variants)
    variant = models.ForeignKey(
        'products.ProductVariant',  # Update with your actual variant model path
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='orders'
    )
    
    # Order details
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at time of order
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Coupon/Discount
    coupon_code = models.CharField(max_length=50, blank=True, null=True)
    coupon_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    
    # Status
    order_status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)

    payment_attempts = models.IntegerField(default=0)
    last_payment_attempt = models.DateTimeField(null=True, blank=True)
    payment_failure_reason = models.TextField(blank=True, null=True)

    return_requested_at = models.DateTimeField(null=True, blank=True)
    return_reason = models.CharField(max_length=50, choices=RETURN_REASON_CHOICES, null=True, blank=True)
    return_description = models.TextField(null=True, blank=True)
    return_images = models.JSONField(null=True, blank=True)  # Store image URLs as JSON array
    return_approved_at = models.DateTimeField(null=True, blank=True)
    return_rejected_at = models.DateTimeField(null=True, blank=True)
    return_rejection_reason = models.TextField(null=True, blank=True)
    returned_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.CharField(max_length=50, choices=CANCELLATION_REASON_CHOICES, null=True, blank=True)
    cancellation_description = models.TextField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    razorpay_payment_id = models.CharField(max_length=100, null=True, blank=True)
    razorpay_order_id = models.CharField(max_length=100, null=True, blank=True)
    razorpay_signature = models.CharField(max_length=200, null=True, blank=True)
    
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
        if not self.subtotal:
            self.subtotal = self.unit_price * self.quantity
        
        if not self.total_amount:
            self.total_amount = self.subtotal + self.tax_amount + self.shipping_cost
        
        if not self.slug:
            # Create a unique slug using order number and a small portion of UUID
            self.slug = slugify(f"{self.order_number}")
        
        # Ensure slug is unique
        if not self.pk:  # For new orders
            original_slug = self.slug
            counter = 1
            while Order.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
            
        super().save(*args, **kwargs)

    def generate_order_number(self):
        timestamp = int(timezone.now().timestamp())
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"ORD{timestamp}{random_str}"

    @property
    def product_name(self):
        """Backward compatibility - get product name from relationship"""
        return self.product.name

    @property
    def product_image_url(self):
        """Get product image URL from relationship"""
        if self.product.image:
            return self.product.image.url
        return ''

    @property
    def product_sku(self):
        """Get SKU from product or variant"""
        if self.variant and self.variant.sku:
            return self.variant.sku
        return self.product.sku if hasattr(self.product, 'sku') else f"SKU-{self.product.id}"

    @property
    def can_be_cancelled(self):
        return self.order_status in ['pending', 'confirmed']
    
    @property
    def can_be_returned(self):
        """Check if order is eligible for return"""
        # SIMPLE CHECK: Only check if order is delivered and no return has been requested
        if self.order_status != 'delivered':
            return False
        
        # Check if already has return request (using existing fields)
        if (self.return_requested_at or 
            self.return_approved_at or 
            self.return_rejected_at or
            self.returned_at):
            return False
        
        # Check if return status is already set (if you're using return_status field)
        if hasattr(self, 'return_status') and self.return_status != 'none':
            return False
        
        return True
    
    @property
    def is_return_requested(self):
        return self.return_requested_at is not None

    @property
    def is_return_approved(self):
        return self.return_approved_at is not None

    @property
    def is_return_rejected(self):
        return self.return_rejected_at is not None

    def get_status_display_class(self):
        status_classes = {
            'pending': 'bg-yellow-100 text-yellow-800',
            'confirmed': 'bg-blue-100 text-blue-800',
            'processing': 'bg-indigo-100 text-indigo-800',
            'shipped': 'bg-purple-100 text-purple-800',
            'delivered': 'bg-green-100 text-green-800',
            'cancelled': 'bg-red-100 text-red-800',
            'returned': 'bg-red-100 text-red-800',
            'return_requested': 'bg-orange-100 text-orange-800',
            'return_rejected': 'bg-red-100 text-red-800',
            'return_approved': 'bg-blue-100 text-blue-800',
        }
        return status_classes.get(self.order_status, 'bg-gray-100 text-gray-800')

    def get_payment_status_class(self):
        status_classes = {
            'pending': 'bg-yellow-100 text-yellow-800',
            'paid': 'bg-green-100 text-green-800',
            'failed': 'bg-red-100 text-red-800',
            'refunded': 'bg-gray-100 text-gray-800',
            'refund_pending': 'bg-orange-100 text-orange-800',
            
        }
        return status_classes.get(self.payment_status, 'bg-gray-100 text-gray-800')
    
    @property
    def can_retry_payment(self):
        """Check if payment can be retried - simplified version"""
        # Allow retry if payment is failed
        return self.payment_status == 'failed'


class Coupon(models.Model):
    """
    Coupon model for discount codes
    """
    code = models.CharField(
        max_length=50, 
        unique=True, 
        help_text="Unique coupon code (e.g., SAVE20, WELCOME10)"
    )
    description = models.TextField(
        blank=True,
        help_text="Description of the coupon offer"
    )
    
    # Discount details
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Discount percentage (e.g., 10.00 for 10% off)"
    )
    
    # Usage limits
    max_uses = models.PositiveIntegerField(
        default=0,
        help_text="Maximum number of times this coupon can be used (0 = unlimited)"
    )
    used_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of times this coupon has been used"
    )
    max_uses_per_user = models.PositiveIntegerField(
        default=1,
        help_text="Maximum uses per user (0 = unlimited)"
    )
    
    # Minimum order requirements
    minimum_order_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Minimum order amount required to use this coupon"
    )
    
    # Maximum discount cap
    max_discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maximum discount amount (optional cap)"
    )
    
    # Validity period
    valid_from = models.DateTimeField(
        help_text="Coupon valid from this date/time"
    )
    valid_until = models.DateTimeField(
        help_text="Coupon valid until this date/time"
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this coupon is currently active"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_coupons'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Coupon'
        verbose_name_plural = 'Coupons'
    
    def __str__(self):
        return f"{self.code} - {self.discount_percentage}% off"
    
    def save(self, *args, **kwargs):
        # Convert code to uppercase for consistency
        self.code = self.code.upper()
        super().save(*args, **kwargs)
    
    def is_valid(self):
        """Check if coupon is currently valid"""
        now = timezone.now()
        
        # Check if active
        if not self.is_active:
            return False, "This coupon is not active"
        
        # Check validity period
        if now < self.valid_from:
            return False, "This coupon is not yet valid"
        
        if now > self.valid_until:
            return False, "This coupon has expired"
        
        # Check usage limit
        if self.max_uses > 0 and self.used_count >= self.max_uses:
            return False, "This coupon has reached its usage limit"
        
        return True, "Coupon is valid"
    
    def can_be_used_by_user(self, user):
        """Check if user can use this coupon"""
        if self.max_uses_per_user == 0:
            return True, "Can use coupon"
        
        # Count how many times user has used this coupon
        user_usage_count = CouponUsage.objects.filter(
            coupon=self,
            user=user
        ).count()
        
        if user_usage_count >= self.max_uses_per_user:
            return False, f"You have already used this coupon {self.max_uses_per_user} time(s)"
        
        return True, "Can use coupon"
    
    def calculate_discount(self, order_amount):
        """Calculate discount amount for given order amount"""
        if order_amount < self.minimum_order_amount:
            return Decimal('0.00')
        
        # Calculate percentage discount
        discount = (order_amount * self.discount_percentage) / Decimal('100')
        
        # Apply max discount cap if set
        if self.max_discount_amount and discount > self.max_discount_amount:
            discount = self.max_discount_amount
        
        return discount.quantize(Decimal('0.01'))
    
    def increment_usage(self):
        """Increment the usage count"""
        self.used_count += 1
        self.save(update_fields=['used_count'])


class CouponUsage(models.Model):
    """
    Track coupon usage by users
    """
    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.CASCADE,
        related_name='usages'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='coupon_usages'
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='coupon_usage',
        null=True,
        blank=True
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Actual discount amount applied"
    )
    used_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-used_at']
        verbose_name = 'Coupon Usage'
        verbose_name_plural = 'Coupon Usages'
    
    def __str__(self):
        return f"{self.user.email} used {self.coupon.code} - ₹{self.discount_amount} off"