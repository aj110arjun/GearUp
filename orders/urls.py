from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('view/', views.view_orders, name='view_orders'),
    path('track/', views.track_orders, name='track_orders'),
    path('<uuid:order_id>/', views.order_detail, name='order_detail'),  
    path('checkout/', views.checkout, name='checkout'),
]
