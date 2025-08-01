from django.apps import AppConfig


class AccountConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'account'

    def ready(self):
        import account.signals


class RegisterConfig(AppConfig):  # replace Register with your app name
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'register'  # change to your app name

    def ready(self):
        import register.models  # Import signals when app is ready


