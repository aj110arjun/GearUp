# urls.py
from django.urls import path
from . import views

app_name = 'wallet'

urlpatterns = [
    path('', views.wallet_dashboard, name='wallet_dashboard'),
    path('deposit/', views.deposit_funds, name='deposit_funds'),
    path('payment/', views.make_payment, name='make_payment'),
    path('history/', views.transaction_history, name='transaction_history'),
    path('transaction/<str:transaction_id>/', views.transaction_detail, name='transaction_detail'),
      path('create-razorpay-order/', views.create_razorpay_order, name='create_razorpay_order'),
    path('verify-razorpay-payment/', views.verify_razorpay_payment, name='verify_razorpay_payment'),
    path('razorpay-webhook/', views.razorpay_webhook, name='razorpay_webhook'),
]