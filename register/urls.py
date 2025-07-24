from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('signup/',views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('verify/otp/', views.verify_otp_view, name='verify_otp'),
    path('logout/', views.logout_view, name='logout'),

    path('password/reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'), name='password_reset'),
    path('password/reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),

    path('admin/login', views.admin_login, name='admin_login'),
    path('admin/logout', views.admin_logout, name='admin_logout')


]
