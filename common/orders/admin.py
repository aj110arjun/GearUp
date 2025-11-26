# orders/admin.py
from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import Order

User = get_user_model()  # This gets your UserModel

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user_email', 'product_name', 'total_amount', 'order_status']
    list_filter = ['order_status', 'created_at']
    search_fields = ['order_number', 'user__email', 'product_name']
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')