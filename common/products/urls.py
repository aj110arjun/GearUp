from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    # Other URL patterns...
    path('list/', views.product_listing, name='product_list'),
    path('create/', views.product_create, name='product_create'),  # Simple creation
    path('details/<slug:product_slug>/', views.product_detail, name='product_detail'),
    path('<slug:product_slug>/edit/', views.product_edit, name='product_edit'),

    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<slug:category_slug>/edit/', views.category_edit, name='category_edit'),

    path('', views.product_list_user, name='product_list_user'),
    path('<slug:product_slug>/', views.product_detail_user, name='product_detail_user'),
]