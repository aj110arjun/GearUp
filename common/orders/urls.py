# orders/urls.py
from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('', views.order_list, name='order_list'),
    path('details/<uuid:order_id>/', views.order_detail, name='order_detail'),
    path('<uuid:order_id>/track/', views.track_order, name='track_order'),
    path('<uuid:order_id>/cancel/', views.cancel_order, name='cancel_order'),
    path('success/', views.order_success, name='order_success'),  # Add this line
    path('success/<uuid:order_id>/', views.order_success, name='order_success'), 
    path('<uuid:order_id>/request-return/', views.request_return, name='request_return'),
    path('<uuid:order_id>/invoice/', views.download_invoice, name='download_invoice'),
    path('<uuid:order_id>/receipt/', views.download_receipt, name='download_receipt'),
    path('payment-failed/<uuid:order_id>/', views.payment_failed, name='payment_failed'),
    path('retry-payment/<uuid:order_id>/', views.retry_payment, name='retry_payment'),
    path('retry-razorpay-payment/<str:order_id>/', views.retry_razorpay_payment, name='retry_razorpay_payment'),
    path('verify-retry-payment/<uuid:order_id>/', views.verify_retry_payment, name='verify_retry_payment'),

    path('admin/<uuid:order_id>/invoice/', views.admin_download_invoice, name='admin_download_invoice'),
    path('returns/', views.admin_return_requests, name='admin_return_requests'),
    path('returns/approved/', views.admin_approved_returns, name='admin_approved_returns'),
    path('returns/rejected/', views.admin_rejected_returns, name='admin_rejected_returns'),
    path('returns/<uuid:order_id>/view/', views.admin_view_return, name='admin_view_return'),
    path('<uuid:order_id>/return/approve/', views.admin_approve_return, name='admin_approve_return'),
    path('<uuid:order_id>/return/reject/', views.admin_reject_return, name='admin_reject_return'),
    path('<uuid:order_id>/return/complete/', views.admin_complete_return, name='admin_complete_return'),
    path('admin/', views.admin_order_list, name='admin_order_list'),
    path('<uuid:order_id>/', views.admin_order_detail, name='admin_order_detail'),
    path('<uuid:order_id>/update-status/', views.admin_order_update_status, name='admin_order_update_status'),
    path('<uuid:order_id>/update-payment-status/', views.admin_order_update_payment_status, name='admin_order_update_payment_status'),
    path('admin/<uuid:order_id>/cancel/', views.admin_order_cancel, name='admin_order_cancel'),
    path('export/', views.admin_order_export, name='admin_order_export'),
    path('create-razorpay-order/', views.create_razorpay_order, name='create_razorpay_order'),
    path('order/<uuid:order_id>/approve-return/', views.admin_approve_return, name='admin_approve_return'),
    path('order/<uuid:order_id>/reject-return/', views.admin_reject_return, name='admin_reject_return'),
    path('order/<uuid:order_id>/complete-return/', views.admin_complete_return, name='admin_complete_return'),
    
    # Coupon Management URLs
    path('coupons/', views.coupon_list, name='coupon_list'),
    path('coupons/create/', views.coupon_create, name='coupon_create'),
    path('coupons/<int:coupon_id>/edit/', views.coupon_edit, name='coupon_edit'),
    path('coupons/<int:coupon_id>/delete/', views.coupon_delete, name='coupon_delete'),
    path('coupons/<int:coupon_id>/toggle-active/', views.coupon_toggle_active, name='coupon_toggle_active'),
    path('coupons/usage/', views.coupon_usage_list, name='coupon_usage_list'),
    
    # Coupon Validation API
    path('validate-coupon/', views.validate_coupon, name='validate_coupon'),
]