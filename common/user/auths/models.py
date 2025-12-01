import secrets
import random

from django.db import models
from django.contrib.auth.models import AbstractUser
from cloudinary.models import CloudinaryField
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

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
    
    # Referral fields
    referral_code = models.CharField(max_length=10, unique=True, blank=False)
    total_referrals = models.IntegerField(default=0)
    referred_by = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='referrals'
    )
    referral_points = models.IntegerField(default=0)
    referral_tier = models.CharField(
        max_length=20, 
        default='Bronze',
        choices=[
            ('Bronze', 'Bronze'),
            ('Silver', 'Silver'),
            ('Gold', 'Gold'),
            ('Platinum', 'Platinum')
        ]
    )
    
    # Social links
    twitter = models.CharField(max_length=100, blank=True)
    facebook = models.CharField(max_length=100, blank=True)
    instagram = models.CharField(max_length=100, blank=True)
    linkedin = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Optional: Track when user completes first purchase or action through referral
    has_completed_referral_action = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # Generate username from email if not set
        if not self.username:
            self.username = self.email
        
        # Generate referral code if not set
        if not self.referral_code:
            self.referral_code = self.generate_referral_code()
        
        super().save(*args, **kwargs)
    
    def generate_referral_code(self):
        """Generate a unique referral code"""
        while True:
            code = secrets.token_urlsafe(8)[:10].upper()
            # Ensure code is alphanumeric and doesn't contain confusing characters
            code = ''.join(c for c in code if c.isalnum())
            if not UserModel.objects.filter(referral_code=code).exists():
                return code
    
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
    
    def get_referral_stats(self):
        """Get detailed referral statistics"""
        return {
            'total_referrals': self.total_referrals,
            'referral_points': self.referral_points,
            'referral_tier': self.referral_tier,
            'referral_code': self.referral_code,
            'referral_link': self.get_referral_link(),
            'referred_by': self.referred_by.username if self.referred_by else None
        }
    
    def get_referral_link(self):
        """Generate referral link"""
        # You can customize this based on your frontend URL structure
        return f"http://localhost:8000/signup?ref={self.referral_code}"
    
    def add_referral_points(self, points):
        """Add points for referrals and update tier"""
        self.referral_points += points
        self.update_referral_tier()
        self.save()
    
    def update_referral_tier(self):
        """Update user's referral tier based on points"""
        if self.referral_points >= 1000:
            self.referral_tier = 'Platinum'
        elif self.referral_points >= 500:
            self.referral_tier = 'Gold'
        elif self.referral_points >= 100:
            self.referral_tier = 'Silver'
        else:
            self.referral_tier = 'Bronze'
    
    def increment_referral_count(self):
        """Increment total referrals count"""
        self.total_referrals += 1
        # Add points for each successful referral
        self.add_referral_points(10)  # 10 points per referral
        self.save()
    
    def validate_referral_code(self, code):
        """Validate a referral code"""
        try:
            referrer = UserModel.objects.get(referral_code=code)
            # Prevent self-referral
            if referrer.id == self.id:
                return None
            return referrer
        except UserModel.DoesNotExist:
            return None

    class Meta:
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['referral_code']),
            models.Index(fields=['referred_by']),
            models.Index(fields=['referral_tier']),
        ]


class Referral(models.Model):
    """Model to track individual referrals"""
    referrer = models.ForeignKey(
        UserModel, 
        on_delete=models.CASCADE, 
        related_name='referrals_given'
    )
    referred_user = models.OneToOneField(
        UserModel, 
        on_delete=models.CASCADE, 
        related_name='referral_received'
    )
    referral_code_used = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Track if referral was successful (user completed signup/action)
    is_successful = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Optional: Track reward status
    reward_given = models.BooleanField(default=False)
    reward_type = models.CharField(max_length=50, blank=True)
    reward_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    class Meta:
        unique_together = ['referrer', 'referred_user']
        ordering = ['-created_at']
    
    def mark_successful(self):
        """Mark referral as successful and update referrer stats"""
        if not self.is_successful:
            self.is_successful = True
            self.completed_at = timezone.now()
            self.save()
            
            # Update referrer's stats
            self.referrer.increment_referral_count()
    
    def __str__(self):
        return f"{self.referrer.username} → {self.referred_user.username}"


@receiver(pre_save, sender=UserModel)
def validate_referral_code(sender, instance, **kwargs):
    """Validate referral code before saving"""
    if instance.referral_code:
        # Ensure referral code is unique and valid format
        if not instance.referral_code.isalnum():
            raise ValidationError("Referral code must be alphanumeric")
        
        # Check if another user has this code (excluding current user)
        qs = UserModel.objects.filter(referral_code=instance.referral_code)
        if instance.pk:
            qs = qs.exclude(pk=instance.pk)
        if qs.exists():
            raise ValidationError("Referral code already exists")


def create_referral_relationship(referred_user, referral_code):
    """Function to create referral relationship"""
    try:
        # Find referrer by code
        referrer = UserModel.objects.get(referral_code=referral_code)
        
        # Prevent self-referral
        if referrer.id == referred_user.id:
            return None
        
        # Create referral record
        referral = Referral.objects.create(
            referrer=referrer,
            referred_user=referred_user,
            referral_code_used=referral_code
        )
        
        # Set referred_by for the new user
        referred_user.referred_by = referrer
        referred_user.save()
        
        return referral
    except UserModel.DoesNotExist:
        return None


class ReferralSettings(models.Model):
    """Model to manage referral program settings"""
    points_per_referral = models.IntegerField(default=10)
    signup_bonus_points = models.IntegerField(default=100)  # Bonus for referred user
    purchase_bonus_points = models.IntegerField(default=20)
    min_points_for_reward = models.IntegerField(default=100)
    reward_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=10.0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Referral Settings"
    
    def save(self, *args, **kwargs):
        # If this is the first instance, set it with default values
        if not self.pk and not ReferralSettings.objects.exists():
            super().save(*args, **kwargs)
        elif self.pk:
            # Update existing instance
            super().save(*args, **kwargs)
    
    def __str__(self):
        return "Referral Program Settings"
    
    @classmethod
    def get_settings(cls):
        """Get or create referral settings singleton"""
        try:
            return cls.objects.first()
        except cls.DoesNotExist:
            # Create default settings
            return cls.objects.create()


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
