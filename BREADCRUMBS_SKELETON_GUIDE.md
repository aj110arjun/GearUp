# Breadcrumbs & Skeleton Loading - Implementation Guide

## Overview
This guide shows how to add breadcrumbs and skeleton loading to ALL main application templates (products, orders, cart, wishlist, profile, etc.)

## ✅ Already Implemented
- **Base Template** (`user/base.html`) - Styles and blocks added
- **Product List** - Already has breadcrumbs and skeleton loading

## 🎯 Implementation Pattern

### Step 1: Add to Template (After `{% extends "user/base.html" %}`)

```django
{% extends "user/base.html" %}
{% load static %}
{% block title %}Page Title{% endblock %}

{# BREADCRUMBS BLOCK #}
{% block breadcrumbs %}
<div class="breadcrumb">
    <div class="container mx-auto px-4 lg:px-6">
        <nav aria-label="Breadcrumb">
            <ol class="flex items-center text-sm text-gray-600">
                <li class="breadcrumb-item">
                    <a href="{% url 'user_home:home' %}" class="hover:text-emerald-600 transition-colors">
                        <i class="fas fa-home mr-1"></i>Home
                    </a>
                </li>
                <li class="breadcrumb-item">
                    <a href="{% url 'current_section:list' %}" class="hover:text-emerald-600 transition-colors">
                        Section Name
                    </a>
                </li>
                <li class="breadcrumb-item text-emerald-600 font-medium" aria-current="page">
                    Current Page
                </li>
            </ol>
        </nav>
    </div>
</div>
{% endblock breadcrumbs %}

{# SKELETON LOADING BLOCK #}
{% block skeleton %}
<div id="skeleton-loader" class="container mx-auto px-4 lg:px-6 py-8">
    <!-- Skeleton content here -->
    <div class="skeleton skeleton-title mb-4"></div>
    <div class="skeleton skeleton-text w-3/4 mb-6"></div>
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        {% for i in "123" %}
        <div class="skeleton skeleton-card"></div>
        {% endfor %}
    </div>
</div>
{% endblock skeleton %}

{# MAIN CONTENT #}
{% block content %}
<div id="main-content" class="container mx-auto px-4 lg:px-6 py-8" style="display: none;">
    <!-- Your actual content here -->
</div>

<script>
// Show content after loading
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

## 📋 Breadcrumb Examples for Each Page

### 1. **Cart Page**
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
{% endblock %}
```

### 2. **Wishlist Page**
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
                    My Wishlist
                </li>
            </ol>
        </nav>
    </div>
</div>
{% endblock %}
```

### 3. **Orders List**
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
{% endblock %}
```

### 4. **Order Details**
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
{% endblock %}
```

### 5. **Product Details**
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
{% endblock %}
```

### 6. **Profile Page**
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
{% endblock %}
```

### 7. **Wallet Dashboard**
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
{% endblock %}
```

### 8. **Checkout Page**
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
{% endblock %}
```

## 🎨 Skeleton Loading Examples

### Cart Page Skeleton
```django
{% block skeleton %}
<div id="skeleton-loader" class="container mx-auto px-4 lg:px-6 py-8">
    <div class="skeleton skeleton-title mb-6"></div>
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div class="lg:col-span-2 space-y-4">
            {% for i in "123" %}
            <div class="bg-white p-4 rounded-lg border">
                <div class="flex gap-4">
                    <div class="skeleton w-24 h-24 rounded"></div>
                    <div class="flex-1 space-y-2">
                        <div class="skeleton skeleton-text w-3/4"></div>
                        <div class="skeleton skeleton-text w-1/2"></div>
                        <div class="skeleton skeleton-button"></div>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
        <div class="skeleton skeleton-card"></div>
    </div>
</div>
{% endblock %}
```

### Order List Skeleton
```django
{% block skeleton %}
<div id="skeleton-loader" class="container mx-auto px-4 lg:px-6 py-8">
    <div class="skeleton skeleton-title mb-6"></div>
    <div class="space-y-4">
        {% for i in "12345" %}
        <div class="bg-white p-6 rounded-lg border">
            <div class="flex justify-between items-start mb-4">
                <div class="space-y-2 flex-1">
                    <div class="skeleton skeleton-text w-1/3"></div>
                    <div class="skeleton skeleton-text w-1/4"></div>
                </div>
                <div class="skeleton skeleton-button"></div>
            </div>
            <div class="skeleton skeleton-text w-full"></div>
        </div>
        {% endfor %}
    </div>
</div>
{% endblock %}
```

### Product Details Skeleton
```django
{% block skeleton %}
<div id="skeleton-loader" class="container mx-auto px-4 lg:px-6 py-8">
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div class="skeleton skeleton-card" style="height: 500px;"></div>
        <div class="space-y-4">
            <div class="skeleton skeleton-title"></div>
            <div class="skeleton skeleton-text w-3/4"></div>
            <div class="skeleton skeleton-text w-1/2"></div>
            <div class="skeleton skeleton-text w-full"></div>
            <div class="skeleton skeleton-text w-full"></div>
            <div class="skeleton skeleton-button w-full" style="height: 3rem;"></div>
        </div>
    </div>
</div>
{% endblock %}
```

## 📝 Complete Template Example

```django
{% extends "user/base.html" %}
{% load static %}

{% block title %}My Orders - GearUp{% endblock %}

{% block breadcrumbs %}
<div class="breadcrumb">
    <div class="container mx-auto px-4 lg:px-6">
        <nav aria-label="Breadcrumb">
            <ol class="flex items-center text-sm text-gray-600">
                <li class="breadcrumb-item">
                    <a href="{% url 'user_home:home' %}">
                        <i class="fas fa-home mr-1"></i>Home
                    </a>
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
{% endblock %}

{% block skeleton %}
<div id="skeleton-loader" class="container mx-auto px-4 lg:px-6 py-8">
    <div class="skeleton skeleton-title mb-6"></div>
    <div class="space-y-4">
        {% for i in "12345" %}
        <div class="skeleton skeleton-card"></div>
        {% endfor %}
    </div>
</div>
{% endblock %}

{% block content %}
<div id="main-content" class="container mx-auto px-4 lg:px-6 py-8" style="display: none;">
    <h1 class="text-3xl font-bold mb-6">My Orders</h1>
    
    <!-- Your actual content here -->
    {% for order in orders %}
    <div class="bg-white p-6 rounded-lg border mb-4">
        <!-- Order content -->
    </div>
    {% endfor %}
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

## 🎯 Templates That Need Updates

### Priority 1 (Most Used):
- [ ] `/user/cart/cart_view.html` - Shopping Cart
- [ ] `/user/products/product_details.html` - Product Details
- [ ] `/user/orders/order_list.html` - Order List
- [ ] `/user/orders/order_details.html` - Order Details
- [ ] `/user/profile/profile.html` - User Profile

### Priority 2 (Frequently Used):
- [ ] `/user/wallet/dashboard.html` - Wallet Dashboard
- [ ] `/user/orders/checkout.html` - Checkout
- [ ] `/user/address/address_list.html` - Address Management
- [ ] `/user/orders/order_success.html` - Order Success

### Priority 3 (Less Frequent):
- [ ] `/user/wallet/deposit.html` - Wallet Deposit
- [ ] `/user/address/address_form.html` - Add/Edit Address
- [ ] `/user/orders/request_return.html` - Return Request

## ⚡ Quick Implementation Checklist

For each template:
1. [ ] Add `{% block breadcrumbs %}` with appropriate navigation path
2. [ ] Add `{% block skeleton %}` with loading placeholders
3. [ ] Wrap main content in div with `id="main-content"` and `style="display: none;"`
4. [ ] Add JavaScript to hide skeleton and show content after 800ms
5. [ ] Test the page loads correctly
6. [ ] Verify breadcrumbs are clickable
7. [ ] Check skeleton matches content layout

## 🚀 Benefits

✅ **Better UX** - Users see loading state immediately
✅ **Clear Navigation** - Always know where you are
✅ **Professional** - Modern, polished appearance
✅ **Consistent** - Same pattern across all pages
✅ **Accessible** - Proper ARIA labels
✅ **Fast Perceived Load** - Feels faster than blank screens

## 📌 Notes

- **Auth pages** (signin, signup, forgot password) don't need breadcrumbs
- **Skeleton timing** can be adjusted (currently 800ms)
- **Breadcrumb separator** is "›" but can be customized
- **Styles** are already in base.html, just use the classes
