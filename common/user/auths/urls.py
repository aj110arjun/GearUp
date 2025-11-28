from django.urls import path, include
from . import views
from allauth.socialaccount.providers.google import views as google_views


app_name = 'user_auth'


urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('signin/', views.signin, name='signin'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),

    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/upload-image/', views.profile_image_upload, name='profile_image_upload'),
    path('change-password/', views.change_password, name='change_password'),
    
    # Custom Google OAuth URL
    path('google/', google_views.oauth2_login, name='google_login'),
    path('google/callback/', google_views.oauth2_callback, name='google_callback'),

    # auths/urls.py
    path('logout/', views.user_logout, name='logout'),
    
    # Or use allauth's built-in URLs
    # path('social/', include('allauth.socialaccount.urls')),
]
