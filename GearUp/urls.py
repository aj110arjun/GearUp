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
    path('django-admin/', django_admin.site.urls),
    path('auth/', include('common.user.auths.urls', namespace='user_auth')),
    path('', include('common.user.home.urls'),),
    path('admin/', include('common.admin.auth_dashboard.urls', namespace='auth_dashboard')),
    path('accounts/', include('allauth.urls')),
    path('products/', include('common.products.urls', namespace='products')),
    path('shop/', include('common.user.cart_wishlist.urls', namespace='shop')),
    path('orders/', include('common.orders.urls', namespace='orders')),
    # path('profile/', include('common.user.user_profile.urls', namespace='profile')),
    path('address/', include('common.user.address.urls', namespace='address')),
    path('wallet/', include('common.wallet.urls', namespace='wallet')),
    path('transactions/', include('common.admin.transactions.urls', namespace='transactions')),
]
