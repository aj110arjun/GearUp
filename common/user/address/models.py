from django.db import models
from common.user.auths.models import UserModel

# models.py (add to your existing models)
class Address(models.Model):
    ADDRESS_TYPES = [
        ('home', 'Home'),
        ('work', 'Work'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(UserModel, on_delete=models.CASCADE, related_name='addresses')
    address_type = models.CharField(max_length=20, choices=ADDRESS_TYPES, default='home')
    is_default = models.BooleanField(default=False)
    
    # Address fields
    full_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15, blank=True)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='India')
    
    # Additional info
    instructions = models.TextField(blank=True, help_text="Delivery instructions")
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_addresses'
        ordering = ['-is_default', '-created_at']
        verbose_name_plural = 'Addresses'

    def __str__(self):
        return f"{self.full_name} - {self.city}, {self.state}"

    def save(self, *args, **kwargs):
        # If this address is set as default, remove default from other addresses
        if self.is_default and self.is_active:
            Address.objects.filter(
                user=self.user, 
                is_default=True,
                is_active=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    def get_formatted_address(self):
        """Return formatted address string"""
        lines = [
            self.full_name,
            self.address_line1,
            self.address_line2,
            f"{self.city}, {self.state} {self.zip_code}",
            self.country
        ]
        return '\n'.join(filter(None, lines))

    def get_short_address(self):
        """Return short address for display"""
        return f"{self.city}, {self.state}"

    @property
    def is_complete(self):
        """Check if address has all required fields"""
        required_fields = [self.full_name, self.address_line1, self.city, self.state, self.zip_code, self.country]
        return all(required_fields)
