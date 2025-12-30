from django.urls import path
from . import views


urlpatterns = [
    path('', views.admin_order_list, name='admin_order_list'),
    path('export/', views.admin_order_export, name='admin_order_export'),
    path('returns/', views.admin_return_requests, name='admin_return_requests'),
    path('returns/approved/', views.admin_approved_returns, name='admin_approved_returns'),
    path('returns/rejected/', views.admin_rejected_returns, name='admin_rejected_returns'),
    path('returns/<uuid:order_id>/view/', views.admin_view_return, name='admin_view_return'),
    path('<uuid:order_id>/', views.admin_order_detail, name='admin_order_detail'),
    path('<uuid:order_id>/update-status/', views.admin_order_update_status, name='admin_order_update_status'),
    path('<uuid:order_id>/update-payment-status/', views.admin_order_update_payment_status, name='admin_order_update_payment_status'),
    path('<uuid:order_id>/cancel/', views.admin_order_cancel, name='admin_order_cancel'),
    path('<uuid:order_id>/invoice/', views.admin_download_invoice, name='admin_download_invoice'),
    path('<uuid:order_id>/return/approve/', views.admin_approve_return, name='admin_approve_return'),
    path('<uuid:order_id>/return/reject/', views.admin_reject_return, name='admin_reject_return'),
    path('<uuid:order_id>/return/complete/', views.admin_complete_return, name='admin_complete_return'),
    
    # Coupon Management URLs
    path('coupons/', views.coupon_list, name='coupon_list'),
    path('coupons/create/', views.coupon_create, name='coupon_create'),
    path('coupons/<int:coupon_id>/edit/', views.coupon_edit, name='coupon_edit'),
    path('coupons/<int:coupon_id>/delete/', views.coupon_delete, name='coupon_delete'),
    path('coupons/<int:coupon_id>/toggle-active/', views.coupon_toggle_active, name='coupon_toggle_active'),
    path('coupons/usage/', views.coupon_usage_list, name='coupon_usage_list'),
]
