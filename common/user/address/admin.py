# common/user/address/admin.py
from django.contrib import admin
from .models import Address

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'user', 'city', 'state', 'is_default', 'is_active']
    list_filter = ['is_default', 'is_active', 'address_type', 'city', 'state']
    search_fields = ['full_name', 'user__username', 'user__email', 'city']
    list_editable = ['is_default', 'is_active']