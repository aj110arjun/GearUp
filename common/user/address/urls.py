# urls.py (add to your user_profile URLs)
from django.urls import path
from . import views

app_name = 'address'

urlpatterns = [
    path('', views.address_list, name='address_list'),
    path('create/', views.address_create, name='address_create'),
    path('<int:pk>/edit/', views.address_edit, name='address_edit'),
    path('<int:pk>/delete/', views.address_delete, name='address_delete'),
    path('<int:pk>/set-default/', views.set_default_address, name='set_default_address'),
    path('<int:pk>/json/', views.get_address_json, name='get_address_json'),
]