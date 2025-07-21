from django.db import models
from django.contrib.auth.hashers import make_password, check_password


class User(models.Model):
    fullname = models.CharField(max_length=100)
    email = models.EmailField()
    username = models.CharField(max_length=100)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    password = models.CharField(max_length=50)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password)
    
    def __str__(self):
        return self.fullname
    


