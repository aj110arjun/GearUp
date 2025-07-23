from django.db import models
from django.contrib.auth.models import User


class AccountInfo(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE)
	address = models.TextField(default='no data')
	city = models.CharField(max_length=100, default='no data')
	landmark = models.CharField(max_length=100, default='no data')
	street = models.CharField(max_length=100, default='no data')
	pincode = models.BigIntegerField(default=0)

	def __str__(self):
		return self.user.first_name


