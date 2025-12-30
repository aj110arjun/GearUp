from django.urls import path
from . import views


urlpatterns = [
    path('toggle-wishlist/', views.toggle_wishlist, name='toggle_wishlist'),
    path('ajax/cart-items/', views.ajax_cart_count, name='ajax_cart_items'),
    
    path('product/<slug:product_slug>/review/submit/', views.submit_review, name='submit_review'),
    path('review/vote/<int:review_id>/', views.vote_review, name='vote_review'),
    path('review/delete/<int:review_id>/', views.delete_review, name='delete_review'),
    path('product/<slug:product_slug>/reviews/ajax/', views.ajax_reviews, name='ajax_reviews'),
    path('review/get/<int:review_id>/', views.get_review, name='get_review'),
    path('review/update/<int:review_id>/', views.update_review, name='update_review'),
    
    path('<slug:product_slug>/', views.product_detail_user, name='product_detail_user'),
    path('', views.product_list_user, name='product_list_user'),
]
