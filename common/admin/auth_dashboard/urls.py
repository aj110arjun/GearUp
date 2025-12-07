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
    
    # Coupon Management URLs
    path('coupons/', views.coupon_list, name='coupon_list'),
    path('coupons/create/', views.coupon_create, name='coupon_create'),
    path('coupons/<int:coupon_id>/edit/', views.coupon_edit, name='coupon_edit'),
    path('coupons/<int:coupon_id>/delete/', views.coupon_delete, name='coupon_delete'),
    path('coupons/<int:coupon_id>/toggle-active/', views.coupon_toggle_active, name='coupon_toggle_active'),
    path('coupons/usage/', views.coupon_usage_list, name='coupon_usage_list'),
]