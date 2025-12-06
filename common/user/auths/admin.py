# admin.py
from django.contrib import admin
from .models import PasswordResetToken

@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token', 'created_at', 'expires_at', 'is_used', 'ip_address')
    list_filter = ('is_used', 'created_at')
    search_fields = ('user__email', 'user__username', 'token')
    readonly_fields = ('token', 'created_at', 'expires_at', 'ip_address', 'user_agent')
    list_per_page = 20
    
    def has_add_permission(self, request):
        # Prevent manual creation of tokens through admin
        return False