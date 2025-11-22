from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    # Other URL patterns...
    path('products/<slug:product_slug>/', views.product_detail, name='product_detail'),
    path('products/', views.product_listing, name='product_list'),
    path('create/', views.product_create, name='product_create'),
    path('<slug:product_slug>/edit/', views.product_edit, name='product_edit'),
]