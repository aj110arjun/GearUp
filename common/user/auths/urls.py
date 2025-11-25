from django.urls import path, include
from . import views
from allauth.socialaccount.providers.google import views as google_views


app_name = 'user_auth'


urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('signin/', views.signin, name='signin'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path('password-change/', views.change_password, name='change_password'),
    path('logout/', views.custom_logout, name='logout'),
    # Custom Google OAuth URL
    path('google/', google_views.oauth2_login, name='google_login'),
    path('google/callback/', google_views.oauth2_callback, name='google_callback'),
    
    # Or use allauth's built-in URLs
    # path('social/', include('allauth.socialaccount.urls')),
]
