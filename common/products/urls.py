from django.urls import path, re_path, register_converter
from . import views
from django.urls.converters import UUIDConverter
register_converter(UUIDConverter, 'uuid')

app_name = 'products'

urlpatterns = [
    # Fixed URLs - put specific patterns BEFORE slug patterns
    path('toggle-wishlist/', views.toggle_wishlist, name='toggle_wishlist'),
    
    # Other fixed URLs
    path('list/', views.product_listing, name='product_list'),
    path('create/', views.product_create, name='product_create'),
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<slug:category_slug>/edit/', views.category_edit, name='category_edit'),
    
    # Slug patterns - these should come LAST
    path('details/<slug:product_slug>/', views.product_detail, name='product_detail'),
    path('<slug:product_slug>/edit/', views.product_edit, name='product_edit'),
    path('<slug:product_slug>/', views.product_detail_user, name='product_detail_user'),
    path('ajax/cart-items/', views.ajax_cart_count, name='ajax_cart_items'),
    path('<slug:product_slug>/variants/', views.ManageVariantsView.as_view(), name='manage_variants'),
    path('<slug:product_slug>/variants/add/', views.AddVariantView.as_view(), name='add_variant'),
    path('<slug:product_slug>/variants/<uuid:variant_id>/edit/', views.EditVariantView.as_view(), name='edit_variant'),
    path('<slug:product_slug>/variants/<uuid:variant_id>/delete/', views.DeleteVariantView.as_view(), name='delete_variant'),
    
    # Root pattern
    path('', views.product_list_user, name='product_list_user'),
]