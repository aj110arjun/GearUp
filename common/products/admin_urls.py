from django.urls import path
from . import views


urlpatterns = [
    path('', views.product_listing, name='product_list'),
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
    
    path('details/<slug:product_slug>/', views.product_detail, name='product_detail'),
    path('edit/<slug:slug>/', views.product_edit, name='product_edit'),
    path('variant/add/<slug:slug>/', views.add_variant_admin, name='add_variant_admin'),
    path('variant/edit/<uuid:variant_id>/', views.edit_variant_admin, name='edit_variant_admin'),
    path('variant/delete/<uuid:variant_id>/', views.delete_variant_admin, name='delete_variant_admin'),
    path('delete/<slug:slug>/', views.product_delete, name='product_delete'),
    path('restore/<slug:slug>/', views.product_restore, name='product_restore'),
    path('toggle-status/<slug:slug>/', views.product_toggle_status, name='product_toggle_status'),
]
