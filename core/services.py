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


def send_password_reset_otp_email(email, otp_code):
    """Send password reset OTP email using HTML template"""
    from django.template.loader import render_to_string
    from django.core.mail import EmailMultiAlternatives
    
    subject = 'GearUp - Password Reset Verification Code'
    
    # Plain text version
    text_message = f'''
GearUp - Password Reset Request

Hello!

We received a request to reset the password for your GearUp account.

Your verification code is: {otp_code}

This code will expire in 2 minutes.

If you didn't request this password reset, please ignore this email.

Stay prepared,
The GearUp Team
'''
    
    # HTML version from template
    html_message = render_to_string('user/auth/password_reset_otp_email.html', {
        'otp_code': otp_code
    })
    
    # Create email with both plain text and HTML
    email_msg = EmailMultiAlternatives(
        subject,
        text_message,
        settings.DEFAULT_FROM_EMAIL,
        [email]
    )
    email_msg.attach_alternative(html_message, "text/html")
    email_msg.send(fail_silently=False)




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
            )
            
            # Update wallet balance
            wallet.balance -= amount
            wallet.save()
            
            return transaction
        
    @staticmethod
    def make_refund(wallet, amount, description=""):
        """Process a refund to wallet"""
        with db_transaction.atomic():
            if amount <= 0:
                raise ValueError("Refund amount must be greater than zero")
            
            # Create transaction record
            transaction = Transaction.objects.create(
                wallet=wallet,
                transaction_type='refund',
                amount=amount,
                description=description,
                status='completed',
            )
            
            # Update wallet balance (add amount back to wallet)
            wallet.balance += amount
            wallet.save()
            
            return transaction

    @staticmethod
    def get_transaction_history(wallet, limit=10):
        return wallet.transactions.all()[:limit]