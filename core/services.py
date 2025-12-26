# core/services.py
import random
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.db import transaction as db_transaction
from common.wallet.models import Wallet, Transaction


def generate_otp_code():
    """Generate a 4-digit OTP code"""
    return str(random.randint(1000, 9999))


def _send_standardized_otp(email, otp_code, subject, template_context):
    """
    Internal helper to send a standardized HTML OTP email with plain-text fallback.
    """
    # Plain text version for fallback
    text_message = f"""
{subject}

{template_context.get('intro_text', 'Hello!')}

Your verification code is: {otp_code}

This code will expire in {template_context.get('expiry_time', '2 minutes')}.

{template_context.get('security_notice', 'If you didn\'t request this code, please ignore this email.')}

Stay prepared,
The GearUp Team
"""
    
    # Merge default context
    context = {
        'otp_code': otp_code,
        'expiry_time': '2 minutes',
        **template_context
    }
    
    # HTML version from unified template
    html_message = render_to_string('user/auth/unified_otp_email.html', context)
    
    # Create email with both plain text and HTML
    email_msg = EmailMultiAlternatives(
        subject,
        text_message,
        settings.DEFAULT_FROM_EMAIL,
        [email]
    )
    email_msg.attach_alternative(html_message, "text/html")
    email_msg.send(fail_silently=False)


def send_otp_email(email, otp_code):
    """Send OTP email for User Signup Verification"""
    _send_standardized_otp(
        email=email,
        otp_code=otp_code,
        subject='GearUp - Account Verification Code',
        template_context={
            'icon': '🏕️',
            'title': 'Verify Your Account',
            'intro_text': "Welcome to the GearUp community! We're excited to have you on board. To complete your registration and start your adventure, please use the verification code below:",
            'outro_text': "Once verified, you'll have full access to our premium survival gear, exclusive member deals, and adventure tracking tools.",
            'security_notice': "If you didn't create an account with GearUp, you can safely ignore this email. No account will be created without this verification."
        }
    )


def send_password_reset_otp_email(email, otp_code):
    """Send OTP email for Password Reset"""
    _send_standardized_otp(
        email=email,
        otp_code=otp_code,
        subject='GearUp - Password Reset Verification Code',
        template_context={
            'icon': '🔐',
            'title': 'Reset Your Password',
            'intro_text': "We received a request to reset the password for your GearUp account. For your security, please use the following verification code to proceed:",
            'outro_text': "Stay prepared for your next adventure!",
            'security_notice': "Security Notice: If you didn't request this password reset, please ignore this email. Your password will remain unchanged."
        }
    )


def send_email_change_otp_email(email, otp_code):
    """Send OTP email for Email Change Verification"""
    _send_standardized_otp(
        email=email,
        otp_code=otp_code,
        subject='GearUp - Email Change Verification Code',
        template_context={
            'icon': '📧',
            'title': 'Confirm Email Change',
            'intro_text': "Hello adventurer! You've requested to change your GearUp account email to this address. To confirm this change, please use the verification code below:",
            'outro_text': "Once confirmed, your account notifications and login credentials will be updated to this email address.",
            'security_notice': "If you did not initiate this request, please ignore this email and ensure your account password is secure."
        }
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