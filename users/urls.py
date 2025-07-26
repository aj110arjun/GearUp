from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('list/', views.user_view, name='user_list'),
    path('<int:id>/', views.admin_user_detail, name='admin_user_detail'),
    path('<int:id>/toggle-status/', views.toggle_user_status, name='toggle_user_status'),
]
