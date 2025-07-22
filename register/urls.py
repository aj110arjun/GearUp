from django.urls import path
from . import views

urlpatterns = [
    path('signup/',views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('verify/otp/', views.verify_otp_view, name='verify_otp'),
]
