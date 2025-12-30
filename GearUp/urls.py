"""
URL configuration for GearUp project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
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

handler404 = 'common.user.home.views.custom_404_view'




