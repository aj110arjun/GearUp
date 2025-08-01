from django.db import models
from django.contrib.auth.models import User


class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    full_address = models.TextField()
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, default="Not set")
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, default="Not set")
    landmark = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=10)
    is_default = models.BooleanField(default=False)

    class Meta:
    	verbose_name_plural = "Addresses"

    def __str__(self):
        return f"{self.full_name} - {self.city}"

