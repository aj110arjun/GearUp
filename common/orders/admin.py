# orders/admin.py
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.utils.html import format_html
from django.utils import timezone
from .models import Order, Coupon, CouponUsage

User = get_user_model()  # This gets your UserModel

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user_email', 'product_name', 'total_amount', 'coupon_code', 'coupon_discount', 'order_status']
    list_filter = ['order_status', 'created_at']
    search_fields = ['order_number', 'user__email', 'product_name', 'coupon_code']
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = [
        'code', 
        'discount_percentage', 
        'usage_info',
        'validity_status',
        'minimum_order_amount',
        'max_discount_amount',
        'is_active',
        'valid_from',
        'valid_until'
    ]
    list_filter = ['is_active', 'valid_from', 'valid_until', 'created_at']
    search_fields = ['code', 'description']
    readonly_fields = ['used_count', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'description', 'is_active')
        }),
        ('Discount Details', {
            'fields': ('discount_percentage', 'max_discount_amount', 'minimum_order_amount')
        }),
        ('Usage Limits', {
            'fields': ('max_uses', 'used_count', 'max_uses_per_user')
        }),
        ('Validity Period', {
            'fields': ('valid_from', 'valid_until')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def usage_info(self, obj):
        """Display usage information"""
        if obj.max_uses == 0:
            return format_html(
                '<span style="color: green;">{} / Unlimited</span>',
                obj.used_count
            )
        
        percentage = (obj.used_count / obj.max_uses * 100) if obj.max_uses > 0 else 0
        color = 'red' if percentage >= 90 else 'orange' if percentage >= 70 else 'green'
        
        return format_html(
            '<span style="color: {};">{} / {} ({}%)</span>',
            color,
            obj.used_count,
            obj.max_uses,
            int(percentage)
        )
    usage_info.short_description = 'Usage (Used / Max)'
    
    def validity_status(self, obj):
        """Display validity status with color coding"""
        is_valid, message = obj.is_valid()
        
        if is_valid:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Valid</span>'
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">✗ {}</span>',
                message
            )
    validity_status.short_description = 'Status'
    
    def save_model(self, request, obj, form, change):
        """Set created_by to current user if creating new coupon"""
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    actions = ['activate_coupons', 'deactivate_coupons']
    
    def activate_coupons(self, request, queryset):
        """Activate selected coupons"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} coupon(s) activated successfully.')
    activate_coupons.short_description = 'Activate selected coupons'
    
    def deactivate_coupons(self, request, queryset):
        """Deactivate selected coupons"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} coupon(s) deactivated successfully.')
    deactivate_coupons.short_description = 'Deactivate selected coupons'


@admin.register(CouponUsage)
class CouponUsageAdmin(admin.ModelAdmin):
    list_display = [
        'coupon_code',
        'user_email',
        'order_number',
        'discount_amount',
        'used_at'
    ]
    list_filter = ['used_at', 'coupon']
    search_fields = ['coupon__code', 'user__email', 'order__order_number']
    readonly_fields = ['coupon', 'user', 'order', 'discount_amount', 'used_at']
    
    def coupon_code(self, obj):
        return obj.coupon.code
    coupon_code.short_description = 'Coupon Code'
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'
    
    def order_number(self, obj):
        return obj.order.order_number if obj.order else 'N/A'
    order_number.short_description = 'Order'
    
    def has_add_permission(self, request):
        """Disable manual addition of coupon usage records"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Make coupon usage records read-only"""
        return False