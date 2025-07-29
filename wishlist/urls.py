from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('view/', views.view_wishlist, name='view_wishlist'),
    path('add/<uuid:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('remove/<uuid:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    
]
