from django.urls import path
from . import views


urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('create-razorpay-order/', views.create_razorpay_order, name='create_razorpay_order'),
    path('validate-coupon/', views.validate_coupon, name='validate_coupon'),
    
    path('success/', views.order_success, name='order_success'),
    path('success/<uuid:order_id>/', views.order_success, name='order_success'),
    
    path('details/<uuid:order_id>/', views.order_detail, name='order_detail'),
    path('<uuid:order_id>/track/', views.track_order, name='track_order'),
    path('<uuid:order_id>/cancel/', views.cancel_order, name='cancel_order'),
    path('<uuid:order_id>/request-return/', views.request_return, name='request_return'),
    path('<uuid:order_id>/invoice/', views.download_invoice, name='download_invoice'),
    path('<uuid:order_id>/receipt/', views.download_receipt, name='download_receipt'),
    
    path('payment-failed/<uuid:order_id>/', views.payment_failed, name='payment_failed'),
    path('retry-payment/<uuid:order_id>/', views.retry_payment, name='retry_payment'),
    path('retry-razorpay-payment/<str:order_id>/', views.retry_razorpay_payment, name='retry_razorpay_payment'),
    path('verify-retry-payment/<uuid:order_id>/', views.verify_retry_payment, name='verify_retry_payment'),
    
    path('', views.order_list, name='order_list'),
]
