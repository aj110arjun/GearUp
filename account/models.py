from django.db import models
from django.contrib.auth.models import User


class AccountInfo(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE)
	profile = models.ImageField(upload_to='profile_pics/', default='images/default.png')
	def __str__(self):
		return self.user.first_name


