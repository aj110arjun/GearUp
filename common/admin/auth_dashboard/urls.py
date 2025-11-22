from django.urls import path
from . import views

app_name = 'auth_dashboard'

urlpatterns = [
    path('signin/', views.admin_signin, name='signin'),
    path('signout/', views.admin_signout, name='signout'),
    path('', views.dashboard, name='dashboard'),
]