from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('view/', views.view_address, name='view_address'),
    path('add/', views.add_address, name='add_address'),
    
]
