from django.urls import path, include
from . import views

app_name = 'orders'

urlpatterns = [
  path('checkout/', views.checkout, name='checkout'),
]
