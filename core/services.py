# core/services.py
import random
from django.core.mail import send_mail
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags


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

    # orders/utils.py


def send_order_confirmation_email(order, request):
    """Send beautiful order confirmation email to customer"""
    try:
        subject = f"Order Confirmed! 🎉 - GearUp Order #{order.order_number}"
        
        # Get site URL for links in email
        site_url = f"http://{request.get_host()}"
        
        # Render HTML template
        html_content = render_to_string('emails/order_confirmation.html', {
            'order': order,
            'site_url': site_url,
        })
        
        # Create plain text version
        text_content = strip_tags(html_content)
        
        # Create email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[order.user.email],
            reply_to=[settings.DEFAULT_FROM_EMAIL]
        )
        
        # Attach HTML content
        email.attach_alternative(html_content, "text/html")
        
        # Send email
        email.send()
        
        return True
        
    except Exception as e:
        print(f"Error sending order confirmation email: {str(e)}")
        return False