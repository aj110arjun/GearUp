from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('view/', views.view_address, name='view_address'),
    path('add/', views.add_address, name='add_address'),
    path('<int:address_id>/set/default/', views.toggle_default_address, name='toggle_default_address'),
    path('<int:address_id>/edit/', views.edit_address, name='edit_address'),
    path('<int:address_id>/delete/', views.delete_address, name='delete_address'),
    
]
