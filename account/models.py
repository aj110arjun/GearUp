from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class AccountInfo(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE)
	profile = models.ImageField(upload_to='profile_pics/', default='images/default.png')
	def __str__(self):
		return self.user.first_name

@receiver(post_save, sender=User)
def create_accountinfo(sender, instance, created, **kwargs):
    if created:
        AccountInfo.objects.create(user=instance)


