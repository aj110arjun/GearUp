from django.contrib import admin
from .models import Cart, CartItem, Wishlist, WishlistItem

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_items', 'subtotal', 'created_at']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart', 'variant', 'quantity', 'total_price', 'added_at']
    list_filter = ['added_at']
    readonly_fields = ['added_at']

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_items', 'created_at']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ['wishlist', 'product', 'added_at']
    list_filter = ['added_at']
    readonly_fields = ['added_at']