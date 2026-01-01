# users/validators.py
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class CustomPasswordValidator:
    def __init__(self):
        self.min_length = 8

    def validate(self, password, user=None):
        # Check minimum length
        if len(password) < self.min_length:
            raise ValidationError(
                _("Password must be at least %(min_length)d characters long."),
                code='password_too_short',
                params={'min_length': self.min_length},
            )

        # Check if password is entirely numeric
        if password.isdigit():
            raise ValidationError(
                _("Password cannot be entirely numeric."),
                code='password_entirely_numeric',
            )

        # Check if password is too common
        common_passwords = [
            'password', '12345678', 'qwerty', 'admin', 'welcome', 
            'password1', '123456789', 'abc123', 'letmein'
        ]
        if password.lower() in common_passwords:
            raise ValidationError(
                _("Password is too common. Please choose a stronger password."),
                code='password_too_common',
            )

        # Check if password is too similar to personal info
        if user:
            user_info = [
                user.username, user.first_name, user.last_name, user.email
                ]
            for info in user_info:
                if info and info.lower() in password.lower():
                    raise ValidationError(
                        _("Password is too similar to your personal information."),
                        code='password_too_similar',
                    )

    def get_help_text(self):
        return _(
            "Your password must be at least 8 characters long, "
            "cannot be entirely numeric, and should not be a common password."
        )

def validate_image_file(value):
    import os
    from django.core.exceptions import ValidationError
    from cloudinary.models import CloudinaryResource
    
    # Skip validation if it's already a CloudinaryResource (already uploaded and validated)
    if isinstance(value, CloudinaryResource):
        return

    if not hasattr(value, 'name'):
        return

    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
    if not ext.lower() in valid_extensions:
        raise ValidationError(f'Unsupported file extension. Allowed extensions are: {", ".join(valid_extensions)}')
    
    # Check if it's actually an image using PIL
    if hasattr(value, 'file'):
        from PIL import Image
        try:
            # Need to seek to beginning if it was read before
            if hasattr(value, 'seek'):
                value.seek(0)
            img = Image.open(value)
            img.verify()
            if hasattr(value, 'seek'):
                value.seek(0)
        except Exception:
            raise ValidationError('Invalid image file.')
