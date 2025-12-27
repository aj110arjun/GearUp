from django.dispatch import receiver
from allauth.account.signals import user_logged_in

@receiver(user_logged_in)
def set_auth_portal_on_social_login(request, user, **kwargs):
    """
    Ensure that users logging in via Allauth (like Google) 
    get a default 'user' portal tag if one isn't already set.
    """
    if 'auth_portal' not in request.session:
        request.session['auth_portal'] = 'user'
