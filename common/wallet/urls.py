from django.urls import path
from . import views

app_name = 'wallet'

urlpatterns = [
    path('', views.wallet_dashboard, name='dashboard'),
    path('transactions/', views.wallet_transactions, name='transactions'),
    path('add-money/', views.add_money, name='add_money'),
    path('withdraw/', views.withdraw_money, name='withdraw'),
    path('balance/', views.ajax_wallet_balance, name='ajax_balance'),
    path('verify-payment/', views.verify_payment, name='verify_payment'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('payment-failed/', views.payment_failed, name='payment_failed'),
]