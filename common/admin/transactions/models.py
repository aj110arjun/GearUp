from django.db import models
import uuid
from common.orders.models import Order
from django.conf import settings


class AdminTransaction(models.Model):

    PAYMENT_METHOD = [
        ('cod','Cash On Delivery'),
        ('wallet','Wallet'),
        ('razorpay','Razorpay'),
    ]

    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('failed', 'Failed'),
        ('completed', 'Completed'),
    ]

    PAYMENT_TYPE = [
        ('debit', 'Debit'),
        ('credit', 'Credit'),
    ]

    transaction_id = models.UUIDField(primary_key=True, unique=True, editable=False, default=uuid.uuid4, verbose_name='Transaction ID')
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, )
    description = models.TextField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=100, default='INR')
    payment_method = models.CharField(max_length=200, choices=PAYMENT_METHOD)
    payment_status = models.CharField(max_length=200, choices=PAYMENT_STATUS, blank=True)
    payment_type = models.CharField(max_length=200, choices=PAYMENT_TYPE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
