import random
import uuid

from django.db import models
from django.contrib.auth.models import AbstractUser
from cloudinary.models import CloudinaryField
from django.utils import timezone
from django.conf import settings

from core.services import generate_otp_code


class UserModel(AbstractUser):
    profile_image = CloudinaryField(
        'profile_image',
        folder='gearup/profiles/',
        blank=True,
        null=True,
        transformation=[
            {'width': 200, 'height': 200, 'crop': 'fill'},
        ]
    )
    email = models.EmailField(unique=True)
    bio = models.TextField(max_length=500, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    email_verified = models.BooleanField(default=False)
    
    # Social links
    twitter = models.CharField(max_length=100, blank=True)
    facebook = models.CharField(max_length=100, blank=True)
    instagram = models.CharField(max_length=100, blank=True)
    linkedin = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.email
        super().save(*args, **kwargs)
    
    def get_display_name(self):
        """Return display name (first name + last name or username)"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    @property
    def profile_completion_percentage(self):
        """Calculate profile completion percentage"""
        fields = [
            self.first_name, self.last_name, self.email,
            self.profile_image, self.bio, self.phone_number,
            self.location, self.date_of_birth
        ]
        completed = sum(1 for field in fields if field)
        return int((completed / len(fields)) * 100)


class OTP(models.Model):
    email = models.EmailField()
    otp_code = models.CharField(max_length=4)  # Changed to 4 digits
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_verified = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)

    class Meta:
        db_table = 'user_otps'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.email} - {self.otp_code}"

    def is_expired(self):
        return timezone.now() > self.expires_at

    def increment_attempts(self):
        self.attempts += 1
        self.save()

    @classmethod
    def create_otp(cls, email):
        """Create a new OTP for email"""
        otp_code = generate_otp_code()  # This now returns 4 digits
        expires_at = timezone.now() + timezone.timedelta(minutes=2)

        # Delete any existing OTPs for this email
        cls.objects.filter(email=email).delete()

        # Create new OTP
        otp = cls.objects.create(
            email=email,
            otp_code=otp_code,
            expires_at=expires_at
        )
        return otp

    @classmethod
    def verify_otp(cls, email, otp_code):
        """Verify OTP code"""
        try:
            otp = cls.objects.filter(
                email=email, 
                is_verified=False
            ).latest('created_at')

            if otp.is_expired():
                return None, "OTP has expired"

            if otp.otp_code != otp_code:
                otp.increment_attempts()
                if otp.attempts >= 3:
                    otp.delete()
                    return None, "Too many failed attempts. Please request a new OTP."
                return None, "Invalid OTP code"

            # Mark as verified
            otp.is_verified = True
            otp.save()
            return otp, "OTP verified successfully"

        except cls.DoesNotExist:
            return None, "OTP not found or already used"
        

class PasswordResetToken(models.Model):
    """
    Model for storing password reset tokens
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='password_reset_tokens'
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['user', 'is_used']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.created_at}"

    def is_valid(self):
        """Check if token is still valid"""
        return not self.is_used and timezone.now() < self.expires_at

    def mark_as_used(self):
        """Mark token as used"""
        self.is_used = True
        self.save()
