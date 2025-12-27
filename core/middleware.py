from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import logout

class PortalIsolationMiddleware:
    """
    Ensures that admin sessions are isolated from regular user sessions.
    Prevents staff members who logged in at the user portal from accessing admin tools
    without explicitly logging in at the admin portal.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            path = request.path
            portal = request.session.get('auth_portal')

            # 1. Admin Area Check
            # If path starts with /admin/ or /django-admin/
            if path.startswith('/admin/') or path.startswith('/django-admin/') or path.startswith('/transactions/'):
                # Redirect if it's not a staff user
                if not request.user.is_staff:
                    messages.error(request, "Access denied. Admin privileges required.")
                    return redirect('user_home:home')
                
                # Verify session was established via Admin Portal
                # Allow access to admin signin/signout regardless
                if portal != 'admin' and 'signin' not in path and 'signout' not in path:
                    messages.warning(request, "Please sign in through the admin portal to access this area.")
                    # We don't necessarily logout, just redirect to the correct signin
                    return redirect('auth_dashboard:signin')

            # 2. User Area Check (Optional: stricter isolation)
            # If an admin is browsing user pages, we generally allow it, 
            # but we could restrict certain actions if needed.
            
        response = self.get_response(request)
        return response
