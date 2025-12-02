# orders/urls.py
from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('', views.order_list, name='order_list'),
    path('details/<int:order_id>/', views.order_detail, name='order_detail'),
    path('<int:order_id>/cancel/', views.cancel_order, name='cancel_order'),
    path('success/', views.order_success, name='order_success'),  # Add this line
    path('success/<int:order_id>/', views.order_success, name='order_success'), 

    path('admin/', views.admin_order_list, name='admin_order_list'),
    path('<int:order_id>/', views.admin_order_detail, name='admin_order_detail'),
    path('<int:order_id>/update-status/', views.admin_order_update_status, name='admin_order_update_status'),
    path('<int:order_id>/update-payment-status/', views.admin_order_update_payment_status, name='admin_order_update_payment_status'),
    path('admin/<int:order_id>/cancel/', views.admin_order_cancel, name='admin_order_cancel'),
    path('export/', views.admin_order_export, name='admin_order_export'),
    path('create-razorpay-order/', views.create_razorpay_order, name='create_razorpay_order'),
]