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

    path('password-reset/', 
         views.CustomPasswordResetView.as_view(), 
         name='password_reset'),
    
    path('password-reset/done/', 
         views.CustomPasswordResetDoneView.as_view(), 
         name='password_reset_done'),
    
    path('password-reset/confirm/<uuid:token>/', 
         views.CustomPasswordResetConfirmView.as_view(), 
         name='password_reset_confirm'),
    
    path('password-reset/complete/', 
         views.CustomPasswordResetCompleteView.as_view(), 
         name='password_reset_complete'),
    
    # API endpoints
    path('api/password-reset/check/<uuid:token>/', 
         views.check_reset_token, 
         name='check_reset_token'),
    
    path('password-reset/resend/', 
         views.resend_reset_email, 
         name='resend_reset_email'),
    
    # Or use allauth's built-in URLs
    # path('social/', include('allauth.socialaccount.urls')),
]
