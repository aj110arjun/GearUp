from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import logout

class PortalIsolationMiddleware:
    """
    Ensures that admin sessions and customer sessions are completely isolated.
    - Admin portal sessions (tagged 'admin') cannot access customer-facing pages.
    - Customer portal sessions (tagged 'user') cannot access admin-facing pages.
    - Explicitly validates is_staff status for admin portal access.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            path = request.path
            portal = request.session.get('auth_portal')
            
            # Resolve the URL to check namespace and name
            from django.urls import resolve
            try:
                resolver_match = resolve(path)
                namespace = resolver_match.namespace
                url_name = resolver_match.url_name
            except:
                namespace = None
                url_name = None

            # 1. Define Admin-Only Contexts
            is_admin_path = (
                path.startswith('/admin/') or 
                path.startswith('/django-admin/') or 
                path.startswith('/transactions/') or
                namespace in ['auth_dashboard', 'transactions'] or
                (namespace == 'orders' and (url_name and url_name.startswith('admin_'))) or
                (namespace == 'products' and url_name in [
                    'product_create', 'product_edit', 'product_delete',
                    'category_list', 'category_create', 'category_edit',
                    'add_variant_admin', 'edit_variant_admin', 'delete_variant_admin',
                    'offer_list', 'product_offer_create', 'product_offer_edit', 'product_offer_delete',
                    'category_offer_create', 'category_offer_edit', 'category_offer_delete'
                ])
            )

            # 2. Define Customer-Only Contexts (Sensitive areas)
            # We want to prevent Admins from using their admin session to browse/buy as a customer
            is_customer_sensitive_path = (
                path.startswith('/accounts/') or
                namespace in ['shop', 'address', 'wallet', 'user_auth', 'account'] or
                (namespace == 'orders' and not (url_name and url_name.startswith('admin_'))) or
                (namespace == 'products' and url_name in ['submit_review', 'update_review', 'delete_review', 'toggle_wishlist'])
            )

            # 3. Enforcement Logic
            
            # A. Accessing Admin Path
            if is_admin_path:
                # Must be staff
                if not request.user.is_staff:
                    messages.error(request, "Access denied. Admin privileges required.")
                    return redirect('user_home:home')
                
                # Must have logged in via Admin portal
                if portal != 'admin' and url_name not in ['signin', 'signout']:
                    messages.warning(request, "Please sign in through the admin portal to access management tools.")
                    return redirect('auth_dashboard:signin')

            # B. Accessing Customer Path with Admin Session
            else:
                if portal == 'admin':
                    # 1. Block access to sensitive customer areas entirely
                    if is_customer_sensitive_path:
                        messages.error(request, "Admin sessions cannot be used for customer activities. Please use a separate customer account.")
                        return redirect('auth_dashboard:dashboard')
                    
                    # 2. For general customer areas (Home, Product Detail, etc.)
                    # Force the user to be seen as Anonymous. 
                    # This prevents "leaking" the admin authentication state into the storefront.
                    from django.contrib.auth.models import AnonymousUser
                    request.user = AnonymousUser()
            
            # C. Accessing Customer Path with User Session
            # Generally allowed, but we could add more checks if needed for specific routes.
                
        response = self.get_response(request)
        return response
