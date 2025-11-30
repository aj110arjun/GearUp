# core/services.py
import random
from django.core.mail import send_mail
from django.conf import settings

import uuid
from django.db import transaction as db_transaction
from common.wallet.models import Wallet, Transaction


def generate_otp_code():
    """Generate a 4-digit OTP code"""
    return str(random.randint(1000, 9999))


def send_otp_email(email, otp_code):
    """Send OTP email to user"""
    subject = 'GearUp - Email Verification Code'
    message = f'''
Welcome to GearUp Survival Toolkit!

Your email verification code is: {otp_code}

This code will expire in 2 minutes.

If you didn't request this code, please ignore this email.

Stay prepared,
The GearUp Team
'''

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )


def send_welcome_email(email, first_name):
    """Send welcome email after successful verification"""
    subject = 'Welcome to GearUp Survival Toolkit!'
    message = f'''
Hi {first_name},

Welcome to GearUp! Your account has been successfully created.

Start exploring our premium survival gear and outdoor equipment.

Stay prepared for your next adventure!

Best regards,
The GearUp Team
'''

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )


# services.py


class WalletService:
    @staticmethod
    def deposit(wallet, amount, description=""):
        with db_transaction.atomic():
            # Create transaction record
            transaction = Transaction.objects.create(
                wallet=wallet,
                transaction_type='deposit',
                amount=amount,
                description=description,
                status='completed',
                reference=f"DEP_{uuid.uuid4().hex[:10]}"
            )
            
            # Update wallet balance
            wallet.balance += amount
            wallet.save()
            
            return transaction

    @staticmethod
    def make_payment(wallet, amount, description=""):
        with db_transaction.atomic():
            # Check if user has sufficient balance
            if wallet.balance < amount:
                raise ValueError("Insufficient balance")
            
            # Create transaction record
            transaction = Transaction.objects.create(
                wallet=wallet,
                transaction_type='payment',
                amount=amount,
                description=description,
                status='completed',
                reference=f"PAY_{uuid.uuid4().hex[:10]}"
            )
            
            # Update wallet balance
            wallet.balance -= amount
            wallet.save()
            
            return transaction

    @staticmethod
    def get_transaction_history(wallet, limit=10):
        return wallet.transactions.all()[:limit]