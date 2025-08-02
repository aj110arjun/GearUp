from django.urls import path
from . import views

urlpatterns = [
    path('list/', views.product_list, name='product_list'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('admin/product/list/', views.admin_product_list, name='admin_product_list'),  # View all products
    path('admin/products/view/<slug:slug>/', views.admin_product_view, name='admin_product_view'),
    # path('admin/products/edit/<slug:slug>/', views.edit_product, name='edit_product'),
    path('admin/products/delete/<slug:slug>/', views.delete_product, name='delete_product'),
    path('admin/product/toggle-status/<slug:slug>/', views.toggle_product_status, name='toggle_product_status'),
    path('admin/product/add/', views.add_product_view, name='add_product'),
    path('admin/category/ajax-add/', views.ajax_add_category, name='ajax_add_category'),
    path('admin/product/<slug:slug>/delete-main-image/', views.delete_main_image, name='delete_main_image'),
    path('admin/product/delete-additional-image/<int:image_id>/', views.delete_additional_image, name='delete_additional_image'),
    path('product/<uuid:pk>/edit/', views.edit_product, name='edit_product'),
    path('admin/products/additional-image/delete/<int:image_id>/', views.delete_additional_image, name='delete_additional_image'),
    
    path('product/<uuid:pk>/edit/', views.edit_product, name='edit_product'),
    path('product/<uuid:pk>/add-variant/', views.add_variant, name='add_variant'),
    path('variant/<uuid:pk>/edit/', views.edit_variant, name='edit_variant'),
    path('variant/<uuid:pk>/delete/', views.delete_variant, name='delete_variant'),






] 