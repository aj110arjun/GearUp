from django.urls import path
from . import views

urlpatterns = [
    path('list/', views.product_list, name='product_list'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('admin/product/list/', views.admin_product_list, name='admin_product_list'),  # View all products
    path('admin/products/view/<slug:slug>/', views.admin_product_view, name='admin_product_view'),
    # path('admin/products/view/<slug:slug>/', admin_product_view, name='admin_product_view'),
    # path('admin/products/edit/<slug:slug>/', admin_product_edit, name='admin_product_edit'),
    # path('admin/products/delete/<slug:slug>/', admin_product_delete, name='admin_product_delete'),
    # path('admin/products/block/<slug:slug>/', admin_product_block_toggle, name='admin_product_block'),


] 