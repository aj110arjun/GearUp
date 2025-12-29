from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    # Cart URLs
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('cart/toggle/', views.toggle_cart_item, name='toggle_cart_item'),
    path('cart/update/<uuid:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('cart/remove/<uuid:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
    path('cart/move-all-to-wishlist/', views.move_all_to_wishlist, name='move_all_to_wishlist'),
    path('cart/move-to-wishlist/<uuid:item_id>/', views.move_to_wishlist, name='move_to_wishlist'),
    path('cart/data/', views.get_cart_data, name='get_cart_data'),
    
    # Wishlist URLs
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/add/<uuid:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<uuid:item_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('wishlist/move-to-cart/<uuid:item_id>/', views.move_to_cart, name='move_to_cart'),
    path('wishlist/toggle/', views.toggle_wishlist, name='toggle_wishlist'),
    path('wishlist/clear/', views.clear_wishlist, name='clear_wishlist'),
    path('wishlist/move-all-to-cart/', views.move_all_to_cart, name='move_all_to_cart'),
    
    # AJAX URLs
    path('ajax/cart-count/', views.ajax_cart_count, name='ajax_cart_count'),
    path('ajax/wishlist-count/', views.ajax_wishlist_count, name='ajax_wishlist_count'),
    path('ajax/csrf-token/', views.get_csrf_token, name='get_csrf_token'),  # NEW
]