from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.core.mail import send_mail

@receiver(user_logged_in)
def send_login_email(sender, request, user, **kwargs):
    send_mail(
        subject='New Login Detected',
        message=f'Hi {user.email}, you just logged into your GearUp account.',
        from_email='aj110arjun@gmail.com',
        recipient_list=[user.email],
        fail_silently=True,
    )
