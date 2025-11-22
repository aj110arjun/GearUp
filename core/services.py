# core/services.py
import random
from django.core.mail import send_mail
from django.conf import settings


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