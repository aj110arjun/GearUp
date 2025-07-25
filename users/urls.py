from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('list/', views.user_view, name='user_list'),
    path('admin/users/<int:user_id>/', views.admin_user_detail, name='admin_user_detail'),
    path('admin/users/<int:user_id>/toggle-status/', views.toggle_user_status, name='toggle_user_status'),
]
