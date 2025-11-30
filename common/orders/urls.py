from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('create-razorpay-order/', views.create_razorpay_order_view, name='create_razorpay_order'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/failure/', views.payment_failure, name='payment_failure'),
    path('payment-webhook/', views.payment_webhook, name='payment_webhook'),
    path('', views.order_list, name='order_list'),
    path('<int:order_id>/', views.order_detail, name='order_detail'),
    path('<int:order_id>/cancel/', views.cancel_order, name='cancel_order'),
]