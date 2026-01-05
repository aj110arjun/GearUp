from django import template

register = template.Library()

@register.filter
def active_products_count(category):
    """Return count of active products in category"""
    return category.products.filter(is_active=True).count()

@register.filter
def total_products_count(category):
    """Return total count of products in category"""
    return category.products.count()

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary by key"""
    if dictionary is None:
        return None
    return dictionary.get(key)

@register.filter
def get_item_str(dictionary, key):
    """Get an item from a dictionary by string key"""
    if dictionary is None:
        return None
    return dictionary.get(str(key))

@register.filter
def get_item_int(dictionary, key):
    """Get an item from a dictionary by integer key"""
    if dictionary is None:
        return None
    try:
        return dictionary.get(int(key))
    except (ValueError, TypeError):
        return None

@register.filter
def sub(value, arg):
    """Subtract the arg from the value"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0