from django.urls import path
from . import views

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
    
    # Offer URLs
    path('offers/', views.offer_list, name='offer_list'),
    path('offers/product/create/', views.product_offer_create, name='product_offer_create'),
    path('offers/product/<uuid:offer_id>/edit/', views.product_offer_edit, name='product_offer_edit'),
    path('offers/product/<uuid:offer_id>/delete/', views.product_offer_delete, name='product_offer_delete'),
    path('offers/category/create/', views.category_offer_create, name='category_offer_create'),
    path('offers/category/<uuid:offer_id>/edit/', views.category_offer_edit, name='category_offer_edit'),
    path('offers/category/<uuid:offer_id>/delete/', views.category_offer_delete, name='category_offer_delete'),
    
    # Slug patterns - these should come LAST
    path('details/<slug:product_slug>/', views.product_detail, name='product_detail'),
    path('<slug:product_slug>/edit/', views.product_edit, name='product_edit'),
    path('<slug:product_slug>/', views.product_detail_user, name='product_detail_user'),
    path('ajax/cart-items/', views.ajax_cart_count, name='ajax_cart_items'),
    
    # Root pattern
    path('', views.product_list_user, name='product_list_user'),
]