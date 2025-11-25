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
    path('profile/', include('common.user.user_profile.urls', namespace='profile')),
]
