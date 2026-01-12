from django.contrib import admin as django_admin
from django.urls import path, include

urlpatterns = [
    # 1. Base & Authentication
    path('django-admin/', django_admin.site.urls),
    path('', include('common.user.home.urls')),
    path('auth/', include('common.user.auths.urls', namespace='user_auth')),
    path('accounts/', include('allauth.urls')),
    
    # 2. Namespaced App Groups (Unified namespaces for Admin and User portals)
    # This pattern merges /admin/ and / routes into the same app_name namespace.
    
    path('', include(([
        path('admin/products/', include('common.products.admin_urls')),
        path('products/', include('common.products.user_urls')),
    ], 'products'))),

    path('', include(([
        path('admin/orders/', include('common.orders.admin_urls')),
        path('orders/', include('common.orders.user_urls')),
    ], 'orders'))),

    # 3. Admin Core Portal (Dashboard, Transactions, etc.)
    path('admin/', include([
        path('', include('common.admin.auth_dashboard.urls')),
        path('transactions/', include('common.admin.transactions.urls')),
    ])),

    # 4. Independent User Apps
    path('shop/', include('common.user.cart_wishlist.urls')),
    path('address/', include('common.user.address.urls')),
    path('wallet/', include('common.wallet.urls')),
]

from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


handler404 = 'common.user.home.views.custom_404_view'




