# common/templatetags/custom_filters.py (or your app's templatetags directory)
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary by key"""
    return dictionary.get(str(key))

@register.filter
def get_item_int(dictionary, key):
    """Get an item from a dictionary by integer key"""
    return dictionary.get(int(key))