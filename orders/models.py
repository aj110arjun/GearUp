import uuid

from django.db import models
from django.conf import settings

from products.models import Product, Variant
from address.models import Address

class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PLACED', 'Placed'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
        ('RETURNED', 'Returned'),
    ]

    RETURN_STATUS_CHOICES = [
        ('NONE', 'No Return'),
        ('REQUESTED', 'Return Requested'),
        ('APPROVED', 'Return Approved'),
        ('REJECTED', 'Return Rejected'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('COD', 'Cash on Delivery'),
        ('UPI', 'UPI'),                # For future
        ('NET_BANKING', 'Net Banking'),# For future
        ('DEBIT_CARD', 'Debit Card'),  # For future
        ('CREDIT_CARD', 'Credit Card'),# For future
    ]

    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='COD')
    order_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    sequential_number = models.PositiveIntegerField(unique=True, editable=False, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='PENDING')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, blank=True)
    return_status = models.CharField(max_length=20, choices=RETURN_STATUS_CHOICES, default='NONE')
    return_reason = models.TextField(blank=True, null=True, default="none")


    def __str__(self):
        return f"Order {self.order_id} by {self.user}"

    def approve_return(self):
        if self.return_status == 'REQUESTED':
        # Restore stock
            for item in self.items.all():
                if item.variant:
                    item.variant.stock += item.quantity
                    item.variant.save()
                else:
                    item.product.stock += item.quantity
                    item.product.save()

        # Update statuses
        self.return_status = 'APPROVED'
        self.status = 'RETURNED'  # ✅ So template can display "Return Approved"
        self.save()


    def reject_return(self):
        """Reject the return request."""
        if self.return_status == 'REQUESTED':
            self.return_status = 'REJECTED'
            self.save()

    def save(self, *args, **kwargs):
        if not self.sequential_number:
            last_order = (
                Order.objects.exclude(sequential_number__isnull=True)
                .order_by('-sequential_number')
                .first()
            )
            self.sequential_number = 1 if not last_order else (last_order.sequential_number + 1)
        super().save(*args, **kwargs)


    @property
    def order_number(self):
        if not self.sequential_number:
            return "#GEARUP-UNASSIGNED"
        return f"GEARUP{self.sequential_number:03d}"



class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(Variant, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def subtotal(self):
        return self.price * self.quantity
