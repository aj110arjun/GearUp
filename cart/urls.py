from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('view/', views.view_cart, name='view_cart'),
    
]
