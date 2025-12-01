# In your models.py or utils.py
from django.utils import timezone
from django.conf import settings

def create_referral_relationship(referred_user, referral_code):
    """Create referral relationship between referrer and referred user"""
    try:
        # Find referrer by code
        referrer = UserModel.objects.get(referral_code=referral_code)
        
        # Prevent self-referral (extra check)
        if referrer.id == referred_user.id:
            return None
        
        # Create referral record
        from .models import Referral  # Import here to avoid circular import
        referral = Referral.objects.create(
            referrer=referrer,
            referred_user=referred_user,
            referral_code_used=referral_code
        )
        
        # Set referred_by for the new user
        referred_user.referred_by = referrer
        referred_user.save(update_fields=['referred_by'])
        
        # Award bonus points to referred user
        from .models import ReferralSettings
        settings = ReferralSettings.get_settings()
        referred_user.add_referral_points(
            settings.signup_bonus_points,
            f"Signup bonus via referral from {referrer.email}"
        )
        
        return referral
        
    except settings.AUTH_USER_MODEL.DoesNotExist:
        return None
    except Exception as e:
        # Log the error but don't fail the signup
        print(f"Error creating referral: {e}")
        return None