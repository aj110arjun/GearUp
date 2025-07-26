from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # path('admin/', admin.site.urls),
    # path('accounts/', include('django.contrib.auth.urls')),includes login, logout, password change etc.
    path('', include('home.urls')),
    path('products/', include('products.urls')),
    path('register/', include('register.urls')),
    path('account/', include('account.urls')),
    path('admin/users/', include('users.urls')),
    path('auth/', include('social_django.urls', namespace='social')),

    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
