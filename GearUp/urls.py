from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('accounts/', include('django.contrib.auth.urls')),includes login, logout, password change etc.
    path('', include('home.urls')),
    path('products/', include('products.urls')),
    path('register/', include('register.urls')),
    path('account/', include('account.urls')),
    path('custom/admin/', include('custom_admin.urls')),
    path('custom/admin/register/', include('admin_register.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
