from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('view/', views.view_orders, name='view_orders'),
    path('track/', views.track_orders, name='track_orders'),
    path('<uuid:order_id>/', views.order_detail, name='order_detail'),  
    path('checkout/', views.checkout, name='checkout'),
    path('orders/', views.admin_order_list, name='admin_order_list'),
    path('orders/<uuid:order_id>/', views.admin_order_detail, name='admin_order_detail'),
    path('order-success/', views.order_success, name='order_success'),
    path('orders/<uuid:order_id>/cancel/', views.cancel_order, name='cancel_order'),
    path('orders/<uuid:order_id>/return/', views.return_order, name='return_order'),
    path('admin/returns/', views.admin_return_requests, name='admin_return_requests'),
    path('admin/returns/<uuid:order_id>/<str:action>/', views.admin_return_action, name='admin_return_action'),
    path('admin/returns/<uuid:order_id>/', views.admin_return_detail, name='admin_return_detail'),


]
