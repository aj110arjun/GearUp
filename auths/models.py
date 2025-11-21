from django.db import models
from django.contrib.auth.models import AbstractUser
from cloudinary.models import CloudinaryField


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
