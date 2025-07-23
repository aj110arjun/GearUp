from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.core.mail import send_mail

@receiver(user_logged_in)
def send_login_email(sender, request, user, **kwargs):
    send_mail(
        subject='New Login Detected',
        message=f'Welcome,{user.first_name}. You have successfully logged into your GearUp Account. Happy Adventure!!!!',
        from_email='aj110arjun@gmail.com',
        recipient_list=[user.email],
        fail_silently=True,
    )
