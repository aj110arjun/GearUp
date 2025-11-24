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