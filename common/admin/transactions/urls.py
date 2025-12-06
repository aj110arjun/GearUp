# orders/urls.py
from django.urls import path
from . import views

app_name = 'transactions'

urlpatterns = [
    path('list/', views.transaction_list, name='transaction_list'),
    path('detail/<uuid:transaction_id>', views.transaction_detail, name='transaction_detail'),
]