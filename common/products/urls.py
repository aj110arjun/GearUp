from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    # Other URL patterns...
    path('products/<slug:product_slug>/', views.product_detail, name='product_detail'),
    path('products/', views.product_listing, name='products_list'),
]