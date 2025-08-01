from django.urls import path
from . import views

urlpatterns = [
    path('view/', views.account_info, name='account'),
    path('admin/view/', views.admin_account, name='admin_account'),
    path('account/edit/', views.edit_account, name='edit_account'),
    path('verify/email/', views.verify_email_otp, name='verify_email_otp'),
] 