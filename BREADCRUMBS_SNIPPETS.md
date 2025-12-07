# Breadcrumbs & Skeleton Loading - Copy-Paste Snippets

## Quick Reference for All Pages

### 1. CART PAGE (`cart/cart_view.html`)

```django
{% block breadcrumbs %}
<div class="breadcrumb">
    <div class="container mx-auto px-4 lg:px-6">
        <nav aria-label="Breadcrumb">
            <ol class="flex items-center text-sm text-gray-600">
                <li class="breadcrumb-item">
                    <a href="{% url 'user_home:home' %}"><i class="fas fa-home mr-1"></i>Home</a>
                </li>
                <li class="breadcrumb-item">
                    <a href="{% url 'products:product_list_user' %}">Shop</a>
                </li>
                <li class="breadcrumb-item text-emerald-600 font-medium" aria-current="page">
                    Shopping Cart
                </li>
            </ol>
        </nav>
    </div>
</div>
{% endblock breadcrumbs %}
```

### 2. PRODUCT DETAILS (`products/product_details.html`)

```django
{% block breadcrumbs %}
<div class="breadcrumb">
    <div class="container mx-auto px-4 lg:px-6">
        <nav aria-label="Breadcrumb">
            <ol class="flex items-center text-sm text-gray-600">
                <li class="breadcrumb-item">
                    <a href="{% url 'user_home:home' %}"><i class="fas fa-home mr-1"></i>Home</a>
                </li>
                <li class="breadcrumb-item">
                    <a href="{% url 'products:product_list_user' %}">Shop</a>
                </li>
                <li class="breadcrumb-item">
                    <a href="{% url 'products:product_list_user' %}?category={{ product.category.id }}">
                        {{ product.category.name }}
                    </a>
                </li>
                <li class="breadcrumb-item text-emerald-600 font-medium" aria-current="page">
                    {{ product.name|truncatewords:5 }}
                </li>
            </ol>
        </nav>
    </div>
</div>
{% endblock breadcrumbs %}
```

### 3. CHECKOUT (`orders/checkout.html`)

```django
{% block breadcrumbs %}
<div class="breadcrumb">
    <div class="container mx-auto px-4 lg:px-6">
        <nav aria-label="Breadcrumb">
            <ol class="flex items-center text-sm text-gray-600">
                <li class="breadcrumb-item">
                    <a href="{% url 'user_home:home' %}"><i class="fas fa-home mr-1"></i>Home</a>
                </li>
                <li class="breadcrumb-item">
                    <a href="{% url 'shop:cart' %}">Cart</a>
                </li>
                <li class="breadcrumb-item text-emerald-600 font-medium" aria-current="page">
                    Checkout
                </li>
            </ol>
        </nav>
    </div>
</div>
{% endblock breadcrumbs %}
```

### 4. ORDER SUCCESS (`orders/order_success.html`)

```django
{% block breadcrumbs %}
<div class="breadcrumb">
    <div class="container mx-auto px-4 lg:px-6">
        <nav aria-label="Breadcrumb">
            <ol class="flex items-center text-sm text-gray-600">
                <li class="breadcrumb-item">
                    <a href="{% url 'user_home:home' %}"><i class="fas fa-home mr-1"></i>Home</a>
                </li>
                <li class="breadcrumb-item">
                    <a href="{% url 'shop:cart' %}">Cart</a>
                </li>
                <li class="breadcrumb-item">
                    <a href="{% url 'orders:checkout' %}">Checkout</a>
                </li>
                <li class="breadcrumb-item text-emerald-600 font-medium" aria-current="page">
                    Order Confirmed
                </li>
            </ol>
        </nav>
    </div>
</div>
{% endblock breadcrumbs %}
```

### 5. PROFILE (`profile/profile.html`)

```django
{% block breadcrumbs %}
<div class="breadcrumb">
    <div class="container mx-auto px-4 lg:px-6">
        <nav aria-label="Breadcrumb">
            <ol class="flex items-center text-sm text-gray-600">
                <li class="breadcrumb-item">
                    <a href="{% url 'user_home:home' %}"><i class="fas fa-home mr-1"></i>Home</a>
                </li>
                <li class="breadcrumb-item text-emerald-600 font-medium" aria-current="page">
                    My Profile
                </li>
            </ol>
        </nav>
    </div>
</div>
{% endblock breadcrumbs %}
```

### 6. ORDERS LIST (`orders/order_list.html`)

```django
{% block breadcrumbs %}
<div class="breadcrumb">
    <div class="container mx-auto px-4 lg:px-6">
        <nav aria-label="Breadcrumb">
            <ol class="flex items-center text-sm text-gray-600">
                <li class="breadcrumb-item">
                    <a href="{% url 'user_home:home' %}"><i class="fas fa-home mr-1"></i>Home</a>
                </li>
                <li class="breadcrumb-item">
                    <a href="{% url 'user_auth:profile' %}">My Account</a>
                </li>
                <li class="breadcrumb-item text-emerald-600 font-medium" aria-current="page">
                    My Orders
                </li>
            </ol>
        </nav>
    </div>
</div>
{% endblock breadcrumbs %}
```

### 7. ORDER DETAILS (`orders/order_details.html`)

```django
{% block breadcrumbs %}
<div class="breadcrumb">
    <div class="container mx-auto px-4 lg:px-6">
        <nav aria-label="Breadcrumb">
            <ol class="flex items-center text-sm text-gray-600">
                <li class="breadcrumb-item">
                    <a href="{% url 'user_home:home' %}"><i class="fas fa-home mr-1"></i>Home</a>
                </li>
                <li class="breadcrumb-item">
                    <a href="{% url 'user_auth:profile' %}">My Account</a>
                </li>
                <li class="breadcrumb-item">
                    <a href="{% url 'orders:order_list' %}">My Orders</a>
                </li>
                <li class="breadcrumb-item text-emerald-600 font-medium" aria-current="page">
                    Order #{{ order.order_number }}
                </li>
            </ol>
        </nav>
    </div>
</div>
{% endblock breadcrumbs %}
```

### 8. WALLET DASHBOARD (`wallet/dashboard.html`)

```django
{% block breadcrumbs %}
<div class="breadcrumb">
    <div class="container mx-auto px-4 lg:px-6">
        <nav aria-label="Breadcrumb">
            <ol class="flex items-center text-sm text-gray-600">
                <li class="breadcrumb-item">
                    <a href="{% url 'user_home:home' %}"><i class="fas fa-home mr-1"></i>Home</a>
                </li>
                <li class="breadcrumb-item">
                    <a href="{% url 'user_auth:profile' %}">My Account</a>
                </li>
                <li class="breadcrumb-item text-emerald-600 font-medium" aria-current="page">
                    My Wallet
                </li>
            </ol>
        </nav>
    </div>
</div>
{% endblock breadcrumbs %}
```

### 9. ADDRESS LIST (`address/address_list.html`)

```django
{% block breadcrumbs %}
<div class="breadcrumb">
    <div class="container mx-auto px-4 lg:px-6">
        <nav aria-label="Breadcrumb">
            <ol class="flex items-center text-sm text-gray-600">
                <li class="breadcrumb-item">
                    <a href="{% url 'user_home:home' %}"><i class="fas fa-home mr-1"></i>Home</a>
                </li>
                <li class="breadcrumb-item">
                    <a href="{% url 'user_auth:profile' %}">My Account</a>
                </li>
                <li class="breadcrumb-item text-emerald-600 font-medium" aria-current="page">
                    My Addresses
                </li>
            </ol>
        </nav>
    </div>
</div>
{% endblock breadcrumbs %}
```

### 10. ADDRESS FORM (`address/address_form.html`)

```django
{% block breadcrumbs %}
<div class="breadcrumb">
    <div class="container mx-auto px-4 lg:px-6">
        <nav aria-label="Breadcrumb">
            <ol class="flex items-center text-sm text-gray-600">
                <li class="breadcrumb-item">
                    <a href="{% url 'user_home:home' %}"><i class="fas fa-home mr-1"></i>Home</a>
                </li>
                <li class="breadcrumb-item">
                    <a href="{% url 'user_auth:profile' %}">My Account</a>
                </li>
                <li class="breadcrumb-item">
                    <a href="{% url 'user_address:address_list' %}">Addresses</a>
                </li>
                <li class="breadcrumb-item text-emerald-600 font-medium" aria-current="page">
                    {% if address %}Edit{% else %}Add{% endif %} Address
                </li>
            </ol>
        </nav>
    </div>
</div>
{% endblock breadcrumbs %}
```

## Universal Skeleton Loading Block

Add this to ALL templates (customize the skeleton UI to match your page layout):

```django
{% block skeleton %}
<div id="skeleton-loader" class="container mx-auto px-4 lg:px-6 py-8">
    <!-- Page Title Skeleton -->
    <div class="skeleton skeleton-title mb-6"></div>
    <div class="skeleton skeleton-text w-2/3 mb-8"></div>
    
    <!-- Content Skeleton (customize based on page) -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {% for i in "123" %}
        <div class="skeleton skeleton-card"></div>
        {% endfor %}
    </div>
</div>
{% endblock skeleton %}
```

## Universal Content Wrapper & Script

Wrap your existing content and add the loading script:

```django
{% block content %}
<div id="main-content" style="display: none;">
    <!-- YOUR EXISTING CONTENT HERE -->
</div>

<script>
// Skeleton Loading
window.addEventListener('load', function() {
    setTimeout(function() {
        document.getElementById('skeleton-loader').style.display = 'none';
        const content = document.getElementById('main-content');
        content.style.display = 'block';
        content.classList.add('content-loaded');
    }, 800);
});
</script>
{% endblock %}
```

## Implementation Checklist

For each template:
- [ ] Add `{% block breadcrumbs %}` after `{% block title %}`
- [ ] Add `{% block skeleton %}` after breadcrumbs
- [ ] Wrap existing content in `<div id="main-content" style="display: none;">`
- [ ] Add skeleton loading script before `{% endblock %}`
- [ ] Test the page to ensure smooth loading
- [ ] Verify breadcrumbs are clickable

## Quick Copy-Paste Template Structure

```django
{% extends "user/base.html" %}
{% load static %}

{% block title %}Page Title{% endblock %}

{% block breadcrumbs %}
<!-- Copy breadcrumb code from above -->
{% endblock breadcrumbs %}

{% block skeleton %}
<!-- Copy skeleton code from above -->
{% endblock skeleton %}

{% block content %}
<div id="main-content" style="display: none;">
    <!-- Your existing content -->
</div>

<script>
window.addEventListener('load', function() {
    setTimeout(function() {
        document.getElementById('skeleton-loader').style.display = 'none';
        const content = document.getElementById('main-content');
        content.style.display = 'block';
        content.classList.add('content-loaded');
    }, 800);
});
</script>
{% endblock %}
```

## Notes

- All styles are already in `base.html` - no additional CSS needed
- Breadcrumb separator (›) is automatic via CSS
- Skeleton timing is 800ms - adjust if needed
- Use Font Awesome icons for breadcrumb home icon
- Active breadcrumb item is emerald-600 color
