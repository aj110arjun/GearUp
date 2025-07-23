from django.db import models


class AccountInfo(models.Model):
	address = models.TextField(default='no data')
	city = models.CharField(max_length=100, default='no data')
	landmark = models.CharField(max_length=100, default='no data')
	street = models.CharField(max_length=100, default='no data')
	pincode = models.BigIntegerField(default=0)


