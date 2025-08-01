import random

from django.db import models
from django.utils.timezone import now
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class AccountInfo(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE)
	profile = models.ImageField(upload_to='profile_pics/', default='images/default.png')

	pending_email = models.EmailField(blank=True, null=True)
	email_otp = models.CharField(max_length=6, blank=True, null=True)
	otp_created_at = models.DateTimeField(blank=True, null=True)

	def generate_email_otp(self):
		otp = str(random.randint(1000, 9999))
		self.email_otp = otp
		self.otp_created_at = now()
		self.save()
		return otp

	def __str__(self):
		return self.user.first_name

@receiver(post_save, sender=User)
def create_accountinfo(sender, instance, created, **kwargs):
    if created:
        AccountInfo.objects.create(user=instance)


