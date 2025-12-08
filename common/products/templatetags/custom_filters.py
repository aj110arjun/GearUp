# common/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    """Get an item from a dictionary using a key."""
    if dictionary and key in dictionary:
        return dictionary.get(key)
    return None

# Alternative: If you want to access nested dictionaries
@register.filter(name='get_item')
def get_item(dictionary, key_path):
    """Get an item from a dictionary using dot notation for nested keys."""
    if not dictionary:
        return None
    
    keys = str(key_path).split('.')
    value = dictionary
    
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return None
    return value