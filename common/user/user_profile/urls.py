from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views

app_name = 'profile'

urlpatterns = [
  path('profile/', views.profile, name='profile'),
  path('password-change/', views.CustomPasswordChangeView.as_view(), name='change_password'),
  path('password-change/done/', views.CustomPasswordChangeDoneView.as_view(), name='password_change_done'),
]
