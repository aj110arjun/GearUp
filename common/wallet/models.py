from django.db import models
import uuid
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.conf import settings
from decimal import Decimal
import time

class Wallet(models.Model):
    TRANSACTION_TYPES = (
        ('credit', 'Credit'),
        ('debit', 'Debit'),
    )
    
    TRANSACTION_CATEGORIES = (
        ('purchase', 'Purchase'),
        ('refund', 'Refund'),
        ('cashback', 'Cashback'),
        ('referral', 'Referral Bonus'),
        ('promotional', 'Promotional Credit'),
        ('withdrawal', 'Withdrawal'),
        ('transfer', 'Transfer'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='wallet'
    )
    balance = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Wallet'
        verbose_name_plural = 'Wallets'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - ₹{self.balance}"

    def credit(self, amount, transaction_type='credit', category='promotional', description=''):
        """Credit amount to wallet"""
        print(f"🚀 CREDIT CALLED - Balance: {self.balance}, Amount: {amount}")
        
        # Convert amount to Decimal safely
        if isinstance(amount, float):
            amount = Decimal(str(amount))
        elif isinstance(amount, int):
            amount = Decimal(amount)
        elif isinstance(amount, str):
            amount = Decimal(amount)
        
        if amount <= Decimal('0.00'):
            raise ValueError("Amount must be greater than zero")
        
        # Perform the credit operation
        self.balance += amount
        self.save()
        
        # Create transaction record
        transaction = WalletTransaction.objects.create(
            wallet=self,
            amount=amount,
            transaction_type='credit',
            category=category,
            description=description,
            balance_after=self.balance
        )
        
        print(f"✅ CREDIT SUCCESS - New Balance: {self.balance}, Transaction: {transaction.id}")
        return True

    def debit(self, amount, transaction_type='debit', category='purchase', description=''):
        """Debit amount from wallet"""
        # Convert amount to Decimal safely
        if isinstance(amount, float):
            amount = Decimal(str(amount))
        elif isinstance(amount, int):
            amount = Decimal(amount)
        elif isinstance(amount, str):
            amount = Decimal(amount)
        
        if amount <= Decimal('0.00'):
            raise ValueError("Amount must be greater than zero")
        
        if self.balance < amount:
            raise ValueError("Insufficient balance")
        
        self.balance -= amount
        self.save()
        
        # Create transaction record
        WalletTransaction.objects.create(
            wallet=self,
            amount=amount,
            transaction_type='debit',
            category=category,
            description=description,
            balance_after=self.balance
        )
        return True

class WalletTransaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet = models.ForeignKey(
        Wallet, 
        on_delete=models.CASCADE, 
        related_name='transactions'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=Wallet.TRANSACTION_TYPES)
    category = models.CharField(max_length=20, choices=Wallet.TRANSACTION_CATEGORIES)
    description = models.TextField(blank=True)
    balance_after = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=Wallet.STATUS_CHOICES, default='completed')
    reference_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Wallet Transaction'
        verbose_name_plural = 'Wallet Transactions'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.wallet.user.email} - {self.transaction_type} - ₹{self.amount}"
    
    def save(self, *args, **kwargs):
        # Generate reference_id only if it doesn't exist
        if not self.reference_id:
            timestamp = time.strftime('%Y%m%d%H%M%S')
            unique_id = str(self.id)[:8].upper()
            self.reference_id = f"WT{timestamp}{unique_id}"
        super().save(*args, **kwargs)