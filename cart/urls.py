from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('view/', views.view_cart, name='view_cart'),
    path('add-to-cart/<uuid:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove-from-cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('increment/<int:item_id>/', views.increment_quantity, name='increment_quantity'),
    path('decrement/<int:item_id>/', views.decrement_quantity, name='decrement_quantity'),
    path('update-variant/<int:item_id>/', views.update_cart_variant, name='update_cart_variant'),
]
