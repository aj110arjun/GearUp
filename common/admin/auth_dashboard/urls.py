from django.urls import path
from . import views

app_name = 'auth_dashboard'

urlpatterns = [
    path('signin/', views.admin_signin, name='signin'),
    path('signout/', views.admin_signout, name='signout'),
    path('', views.dashboard, name='dashboard'),

    path('users/', views.admin_user_list, name='admin_user_list'),
    path('users/<int:user_id>/', views.admin_user_detail, name='admin_user_detail'),
    path('users/<int:user_id>/toggle-active/', views.admin_user_toggle_active, name='admin_user_toggle_active'),
    path('users/<int:user_id>/activate/', views.admin_user_activate, name='admin_user_activate'),
    path('users/<int:user_id>/deactivate/', views.admin_user_deactivate, name='admin_user_deactivate'),
]
    