from django.urls import path
from . import views

urlpatterns = [
    path('view/', views.account_info, name='account')
] 