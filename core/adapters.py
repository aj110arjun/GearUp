from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings
from core.services import get_login_redirect_url
from django.shortcuts import resolve_url

class RoleBasedAccountAdapter(DefaultAccountAdapter):
    def get_login_redirect_url(self, request):
        """
        Redirect users based on their role after successful login.
        """
        # Get the default next parameter from the request
        next_url = request.GET.get('next') or request.POST.get('next')
        
        # Use our centralized redirection logic
        # Note: resolve_url handles both named URL patterns and raw URLs
        return resolve_url(get_login_redirect_url(request.user, next_url))
