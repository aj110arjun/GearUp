# Custom Admin Coupon Management - Complete Implementation

## ✅ Backend Complete!

### What's Been Done:

1. **Views Created** (`common/admin/auth_dashboard/views.py`)
   - ✅ `coupon_list` - List all coupons with search & filters
   - ✅ `coupon_create` - Create new coupons
   - ✅ `coupon_edit` - Edit existing coupons
   - ✅ `coupon_delete` - Delete coupons
   - ✅ `coupon_toggle_active` - Activate/deactivate coupons
   - ✅ `coupon_usage_list` - View coupon usage history

2. **URLs Added** (`common/admin/auth_dashboard/urls.py`)
   - ✅ `/admin/coupons/` - List coupons
   - ✅ `/admin/coupons/create/` - Create coupon
   - ✅ `/admin/coupons/<id>/edit/` - Edit coupon
   - ✅ `/admin/coupons/<id>/delete/` - Delete coupon
   - ✅ `/admin/coupons/<id>/toggle-active/` - Toggle status
   - ✅ `/admin/coupons/usage/` - Usage history

## 📁 Templates to Create

### 1. Coupon List Template

**File:** `/templates/admin/coupons/coupon_list.html`

```html
{% extends 'admin/base_admin.html' %}
{% load static %}

{% block title %}Coupon Management - Admin{% endblock %}

{% block content %}
<div class="container-fluid py-4">
    <!-- Header -->
    <div class="d-flex justify-content-between align-items-center mb-4">
        <div>
            <h2 class="mb-0"><i class="fas fa-tags text-primary"></i> Coupon Management</h2>
            <p class="text-muted mb-0">Manage discount coupons and promotional codes</p>
        </div>
        <a href="{% url 'auth_dashboard:coupon_create' %}" class="btn btn-primary">
            <i class="fas fa-plus"></i> Create New Coupon
        </a>
    </div>

    <!-- Statistics Cards -->
    <div class="row mb-4">
        <div class="col-md-4">
            <div class="card border-left-primary shadow h-100 py-2">
                <div class="card-body">
                    <div class="row no-gutters align-items-center">
                        <div class="col mr-2">
                            <div class="text-xs font-weight-bold text-primary text-uppercase mb-1">
                                Total Coupons
                            </div>
                            <div class="h5 mb-0 font-weight-bold text-gray-800">{{ total_coupons }}</div>
                        </div>
                        <div class="col-auto">
                            <i class="fas fa-tags fa-2x text-gray-300"></i>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="col-md-4">
            <div class="card border-left-success shadow h-100 py-2">
                <div class="card-body">
                    <div class="row no-gutters align-items-center">
                        <div class="col mr-2">
                            <div class="text-xs font-weight-bold text-success text-uppercase mb-1">
                                Active Coupons
                            </div>
                            <div class="h5 mb-0 font-weight-bold text-gray-800">{{ active_coupons }}</div>
                        </div>
                        <div class="col-auto">
                            <i class="fas fa-check-circle fa-2x text-gray-300"></i>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="col-md-4">
            <div class="card border-left-danger shadow h-100 py-2">
                <div class="card-body">
                    <div class="row no-gutters align-items-center">
                        <div class="col mr-2">
                            <div class="text-xs font-weight-bold text-danger text-uppercase mb-1">
                                Expired Coupons
                            </div>
                            <div class="h5 mb-0 font-weight-bold text-gray-800">{{ expired_coupons }}</div>
                        </div>
                        <div class="col-auto">
                            <i class="fas fa-clock fa-2x text-gray-300"></i>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Search and Filter -->
    <div class="card shadow mb-4">
        <div class="card-header py-3">
            <h6 class="m-0 font-weight-bold text-primary">Search & Filter</h6>
        </div>
        <div class="card-body">
            <form method="get" class="form-inline">
                <div class="form-group mr-3">
                    <input type="text" name="search" class="form-control" placeholder="Search coupons..." value="{{ search_query }}">
                </div>
                <div class="form-group mr-3">
                    <select name="status" class="form-control">
                        <option value="">All Status</option>
                        <option value="active" {% if status_filter == 'active' %}selected{% endif %}>Active</option>
                        <option value="inactive" {% if status_filter == 'inactive' %}selected{% endif %}>Inactive</option>
                        <option value="expired" {% if status_filter == 'expired' %}selected{% endif %}>Expired</option>
                        <option value="upcoming" {% if status_filter == 'upcoming' %}selected{% endif %}>Upcoming</option>
                    </select>
                </div>
                <button type="submit" class="btn btn-primary mr-2">
                    <i class="fas fa-search"></i> Search
                </button>
                <a href="{% url 'auth_dashboard:coupon_list' %}" class="btn btn-secondary">
                    <i class="fas fa-redo"></i> Reset
                </a>
            </form>
        </div>
    </div>

    <!-- Coupons Table -->
    <div class="card shadow mb-4">
        <div class="card-header py-3">
            <h6 class="m-0 font-weight-bold text-primary">All Coupons</h6>
        </div>
        <div class="card-body">
            <div class="table-responsive">
                <table class="table table-bordered table-hover">
                    <thead class="thead-light">
                        <tr>
                            <th>Code</th>
                            <th>Discount</th>
                            <th>Usage</th>
                            <th>Min. Order</th>
                            <th>Valid Period</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for coupon in coupons %}
                        <tr>
                            <td>
                                <strong class="text-primary">{{ coupon.code }}</strong>
                                {% if coupon.description %}
                                <br><small class="text-muted">{{ coupon.description|truncatewords:10 }}</small>
                                {% endif %}
                            </td>
                            <td>
                                <span class="badge badge-success">{{ coupon.discount_percentage }}% OFF</span>
                                {% if coupon.max_discount_amount %}
                                <br><small class="text-muted">Max: ₹{{ coupon.max_discount_amount }}</small>
                                {% endif %}
                            </td>
                            <td>
                                {% if coupon.max_uses == 0 %}
                                    <span class="text-success">{{ coupon.used_count }} / Unlimited</span>
                                {% else %}
                                    {% widthratio coupon.used_count coupon.max_uses 100 as usage_percent %}
                                    <div class="progress" style="height: 20px;">
                                        <div class="progress-bar {% if usage_percent >= 90 %}bg-danger{% elif usage_percent >= 70 %}bg-warning{% else %}bg-success{% endif %}" 
                                             role="progressbar" 
                                             style="width: {{ usage_percent }}%">
                                            {{ coupon.used_count }} / {{ coupon.max_uses }}
                                        </div>
                                    </div>
                                {% endif %}
                            </td>
                            <td>₹{{ coupon.minimum_order_amount }}</td>
                            <td>
                                <small>
                                    <strong>From:</strong> {{ coupon.valid_from|date:"M d, Y H:i" }}<br>
                                    <strong>Until:</strong> {{ coupon.valid_until|date:"M d, Y H:i" }}
                                </small>
                            </td>
                            <td>
                                {% if coupon.is_active %}
                                    {% if coupon.valid_until < now %}
                                        <span class="badge badge-danger">Expired</span>
                                    {% elif coupon.valid_from > now %}
                                        <span class="badge badge-info">Upcoming</span>
                                    {% else %}
                                        <span class="badge badge-success">Active</span>
                                    {% endif %}
                                {% else %}
                                    <span class="badge badge-secondary">Inactive</span>
                                {% endif %}
                            </td>
                            <td>
                                <div class="btn-group" role="group">
                                    <a href="{% url 'auth_dashboard:coupon_edit' coupon.id %}" 
                                       class="btn btn-sm btn-info" title="Edit">
                                        <i class="fas fa-edit"></i>
                                    </a>
                                    <form method="post" action="{% url 'auth_dashboard:coupon_toggle_active' coupon.id %}" style="display: inline;">
                                        {% csrf_token %}
                                        <button type="submit" class="btn btn-sm {% if coupon.is_active %}btn-warning{% else %}btn-success{% endif %}" 
                                                title="{% if coupon.is_active %}Deactivate{% else %}Activate{% endif %}">
                                            <i class="fas fa-{% if coupon.is_active %}pause{% else %}play{% endif %}"></i>
                                        </button>
                                    </form>
                                    <a href="{% url 'auth_dashboard:coupon_delete' coupon.id %}" 
                                       class="btn btn-sm btn-danger" title="Delete">
                                        <i class="fas fa-trash"></i>
                                    </a>
                                </div>
                            </td>
                        </tr>
                        {% empty %}
                        <tr>
                            <td colspan="7" class="text-center text-muted py-4">
                                <i class="fas fa-inbox fa-3x mb-3"></i>
                                <p>No coupons found</p>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>

            <!-- Pagination -->
            {% if page_obj.has_other_pages %}
            <nav>
                <ul class="pagination justify-content-center">
                    {% if page_obj.has_previous %}
                    <li class="page-item">
                        <a class="page-link" href="?page={{ page_obj.previous_page_number }}{% if search_query %}&search={{ search_query }}{% endif %}{% if status_filter %}&status={{ status_filter }}{% endif %}">Previous</a>
                    </li>
                    {% endif %}
                    
                    {% for num in page_obj.paginator.page_range %}
                    <li class="page-item {% if page_obj.number == num %}active{% endif %}">
                        <a class="page-link" href="?page={{ num }}{% if search_query %}&search={{ search_query }}{% endif %}{% if status_filter %}&status={{ status_filter }}{% endif %}">{{ num }}</a>
                    </li>
                    {% endfor %}
                    
                    {% if page_obj.has_next %}
                    <li class="page-item">
                        <a class="page-link" href="?page={{ page_obj.next_page_number }}{% if search_query %}&search={{ search_query }}{% endif %}{% if status_filter %}&status={{ status_filter }}{% endif %}">Next</a>
                    </li>
                    {% endif %}
                </ul>
            </nav>
            {% endif %}
        </div>
    </div>

    <!-- Quick Link to Usage History -->
    <div class="text-center">
        <a href="{% url 'auth_dashboard:coupon_usage_list' %}" class="btn btn-outline-primary">
            <i class="fas fa-history"></i> View Coupon Usage History
        </a>
    </div>
</div>
{% endblock %}
```

### 2. Coupon Form Template (Create/Edit)

**File:** `/templates/admin/coupons/coupon_form.html`

```html
{% extends 'admin/base_admin.html' %}
{% load static %}

{% block title %}{{ title }} - Admin{% endblock %}

{% block content %}
<div class="container-fluid py-4">
    <div class="row">
        <div class="col-lg-8 offset-lg-2">
            <!-- Header -->
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h2><i class="fas fa-tag text-primary"></i> {{ title }}</h2>
                <a href="{% url 'auth_dashboard:coupon_list' %}" class="btn btn-secondary">
                    <i class="fas fa-arrow-left"></i> Back to List
                </a>
            </div>

            <!-- Form Card -->
            <div class="card shadow">
                <div class="card-body">
                    <form method="post">
                        {% csrf_token %}
                        
                        <!-- Basic Information -->
                        <h5 class="border-bottom pb-2 mb-3">Basic Information</h5>
                        <div class="row">
                            <div class="col-md-6">
                                <div class="form-group">
                                    <label for="code">Coupon Code <span class="text-danger">*</span></label>
                                    <input type="text" 
                                           class="form-control text-uppercase" 
                                           id="code" 
                                           name="code" 
                                           value="{% if coupon %}{{ coupon.code }}{% endif %}"
                                           required
                                           maxlength="50"
                                           placeholder="e.g., SAVE20">
                                    <small class="form-text text-muted">Will be converted to uppercase</small>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="form-group">
                                    <label for="is_active">Status</label>
                                    <div class="custom-control custom-switch">
                                        <input type="checkbox" 
                                               class="custom-control-input" 
                                               id="is_active" 
                                               name="is_active"
                                               {% if not coupon or coupon.is_active %}checked{% endif %}>
                                        <label class="custom-control-label" for="is_active">Active</label>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="form-group">
                            <label for="description">Description</label>
                            <textarea class="form-control" 
                                      id="description" 
                                      name="description" 
                                      rows="3"
                                      placeholder="Brief description of the offer">{% if coupon %}{{ coupon.description }}{% endif %}</textarea>
                        </div>

                        <!-- Discount Details -->
                        <h5 class="border-bottom pb-2 mb-3 mt-4">Discount Details</h5>
                        <div class="row">
                            <div class="col-md-6">
                                <div class="form-group">
                                    <label for="discount_percentage">Discount Percentage <span class="text-danger">*</span></label>
                                    <div class="input-group">
                                        <input type="number" 
                                               class="form-control" 
                                               id="discount_percentage" 
                                               name="discount_percentage" 
                                               value="{% if coupon %}{{ coupon.discount_percentage }}{% endif %}"
                                               step="0.01"
                                               min="0"
                                               max="100"
                                               required
                                               placeholder="10.00">
                                        <div class="input-group-append">
                                            <span class="input-group-text">%</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="form-group">
                                    <label for="max_discount_amount">Max Discount Amount (Optional)</label>
                                    <div class="input-group">
                                        <div class="input-group-prepend">
                                            <span class="input-group-text">₹</span>
                                        </div>
                                        <input type="number" 
                                               class="form-control" 
                                               id="max_discount_amount" 
                                               name="max_discount_amount" 
                                               value="{% if coupon.max_discount_amount %}{{ coupon.max_discount_amount }}{% endif %}"
                                               step="0.01"
                                               min="0"
                                               placeholder="200.00">
                                    </div>
                                    <small class="form-text text-muted">Leave empty for no cap</small>
                                </div>
                            </div>
                        </div>

                        <div class="form-group">
                            <label for="minimum_order_amount">Minimum Order Amount</label>
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text">₹</span>
                                </div>
                                <input type="number" 
                                       class="form-control" 
                                       id="minimum_order_amount" 
                                       name="minimum_order_amount" 
                                       value="{% if coupon %}{{ coupon.minimum_order_amount }}{% else %}0{% endif %}"
                                       step="0.01"
                                       min="0"
                                       placeholder="0.00">
                            </div>
                            <small class="form-text text-muted">Set to 0 for no minimum</small>
                        </div>

                        <!-- Usage Limits -->
                        <h5 class="border-bottom pb-2 mb-3 mt-4">Usage Limits</h5>
                        <div class="row">
                            <div class="col-md-6">
                                <div class="form-group">
                                    <label for="max_uses">Maximum Total Uses</label>
                                    <input type="number" 
                                           class="form-control" 
                                           id="max_uses" 
                                           name="max_uses" 
                                           value="{% if coupon %}{{ coupon.max_uses }}{% else %}0{% endif %}"
                                           min="0"
                                           placeholder="0">
                                    <small class="form-text text-muted">Set to 0 for unlimited</small>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="form-group">
                                    <label for="max_uses_per_user">Max Uses Per User</label>
                                    <input type="number" 
                                           class="form-control" 
                                           id="max_uses_per_user" 
                                           name="max_uses_per_user" 
                                           value="{% if coupon %}{{ coupon.max_uses_per_user }}{% else %}1{% endif %}"
                                           min="0"
                                           placeholder="1">
                                    <small class="form-text text-muted">Set to 0 for unlimited per user</small>
                                </div>
                            </div>
                        </div>

                        <!-- Validity Period -->
                        <h5 class="border-bottom pb-2 mb-3 mt-4">Validity Period</h5>
                        <div class="row">
                            <div class="col-md-6">
                                <div class="form-group">
                                    <label for="valid_from">Valid From <span class="text-danger">*</span></label>
                                    <input type="datetime-local" 
                                           class="form-control" 
                                           id="valid_from" 
                                           name="valid_from" 
                                           value="{% if coupon %}{{ coupon.valid_from|date:'Y-m-d\TH:i' }}{% else %}{{ now }}{% endif %}"
                                           required>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="form-group">
                                    <label for="valid_until">Valid Until <span class="text-danger">*</span></label>
                                    <input type="datetime-local" 
                                           class="form-control" 
                                           id="valid_until" 
                                           name="valid_until" 
                                           value="{% if coupon %}{{ coupon.valid_until|date:'Y-m-d\TH:i' }}{% endif %}"
                                           required>
                                </div>
                            </div>
                        </div>

                        <!-- Submit Buttons -->
                        <div class="form-group mt-4">
                            <button type="submit" class="btn btn-primary btn-lg">
                                <i class="fas fa-save"></i> {% if coupon %}Update{% else %}Create{% endif %} Coupon
                            </button>
                            <a href="{% url 'auth_dashboard:coupon_list' %}" class="btn btn-secondary btn-lg">
                                <i class="fas fa-times"></i> Cancel
                            </a>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

### 3. Delete Confirmation Template

**File:** `/templates/admin/coupons/coupon_confirm_delete.html`

```html
{% extends 'admin/base_admin.html' %}

{% block title %}Delete Coupon - Admin{% endblock %}

{% block content %}
<div class="container-fluid py-4">
    <div class="row">
        <div class="col-lg-6 offset-lg-3">
            <div class="card shadow border-danger">
                <div class="card-header bg-danger text-white">
                    <h5 class="mb-0"><i class="fas fa-exclamation-triangle"></i> Confirm Deletion</h5>
                </div>
                <div class="card-body">
                    <p class="lead">Are you sure you want to delete this coupon?</p>
                    
                    <div class="alert alert-warning">
                        <strong>Coupon Code:</strong> {{ coupon.code }}<br>
                        <strong>Discount:</strong> {{ coupon.discount_percentage }}% OFF<br>
                        <strong>Times Used:</strong> {{ coupon.used_count }}
                    </div>
                    
                    <p class="text-danger">
                        <i class="fas fa-exclamation-circle"></i> 
                        This action cannot be undone!
                    </p>
                    
                    <form method="post" class="d-inline">
                        {% csrf_token %}
                        <button type="submit" class="btn btn-danger">
                            <i class="fas fa-trash"></i> Yes, Delete Coupon
                        </button>
                        <a href="{% url 'auth_dashboard:coupon_list' %}" class="btn btn-secondary">
                            <i class="fas fa-times"></i> Cancel
                        </a>
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

### 4. Usage History Template

**File:** `/templates/admin/coupons/coupon_usage_list.html`

```html
{% extends 'admin/base_admin.html' %}

{% block title %}Coupon Usage History - Admin{% endblock %}

{% block content %}
<div class="container-fluid py-4">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2><i class="fas fa-history text-primary"></i> Coupon Usage History</h2>
        <a href="{% url 'auth_dashboard:coupon_list' %}" class="btn btn-secondary">
            <i class="fas fa-arrow-left"></i> Back to Coupons
        </a>
    </div>

    <!-- Filter -->
    <div class="card shadow mb-4">
        <div class="card-body">
            <form method="get" class="form-inline">
                <div class="form-group mr-3">
                    <input type="text" name="coupon" class="form-control" placeholder="Filter by coupon code..." value="{{ coupon_filter }}">
                </div>
                <button type="submit" class="btn btn-primary mr-2">
                    <i class="fas fa-filter"></i> Filter
                </button>
                <a href="{% url 'auth_dashboard:coupon_usage_list' %}" class="btn btn-secondary">
                    <i class="fas fa-redo"></i> Reset
                </a>
            </form>
        </div>
    </div>

    <!-- Usage Table -->
    <div class="card shadow">
        <div class="card-body">
            <div class="table-responsive">
                <table class="table table-bordered table-hover">
                    <thead class="thead-light">
                        <tr>
                            <th>Coupon Code</th>
                            <th>User</th>
                            <th>Order</th>
                            <th>Discount Amount</th>
                            <th>Used At</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for usage in usages %}
                        <tr>
                            <td><strong class="text-primary">{{ usage.coupon.code }}</strong></td>
                            <td>{{ usage.user.email }}</td>
                            <td>
                                {% if usage.order %}
                                    <a href="#">#{{ usage.order.order_number }}</a>
                                {% else %}
                                    N/A
                                {% endif %}
                            </td>
                            <td><span class="badge badge-success">₹{{ usage.discount_amount }}</span></td>
                            <td>{{ usage.used_at|date:"M d, Y H:i" }}</td>
                        </tr>
                        {% empty %}
                        <tr>
                            <td colspan="5" class="text-center text-muted py-4">
                                <i class="fas fa-inbox fa-3x mb-3"></i>
                                <p>No usage records found</p>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>

            <!-- Pagination -->
            {% if page_obj.has_other_pages %}
            <nav>
                <ul class="pagination justify-content-center">
                    {% if page_obj.has_previous %}
                    <li class="page-item">
                        <a class="page-link" href="?page={{ page_obj.previous_page_number }}{% if coupon_filter %}&coupon={{ coupon_filter }}{% endif %}">Previous</a>
                    </li>
                    {% endif %}
                    
                    {% for num in page_obj.paginator.page_range %}
                    <li class="page-item {% if page_obj.number == num %}active{% endif %}">
                        <a class="page-link" href="?page={{ num }}{% if coupon_filter %}&coupon={{ coupon_filter }}{% endif %}">{{ num }}</a>
                    </li>
                    {% endfor %}
                    
                    {% if page_obj.has_next %}
                    <li class="page-item">
                        <a class="page-link" href="?page={{ page_obj.next_page_number }}{% if coupon_filter %}&coupon={{ coupon_filter }}{% endif %}">Next</a>
                    </li>
                    {% endif %}
                </ul>
            </nav>
            {% endif %}
        </div>
    </div>
</div>
{% endblock %}
```

## 🎯 Implementation Steps

1. **Create Templates Directory**
   ```bash
   mkdir -p templates/admin/coupons
   ```

2. **Create Template Files**
   - Copy each template code above into the respective files
   - Adjust Bootstrap classes if your admin uses different styling

3. **Add Navigation Link**
   In your `base_admin.html` sidebar, add:
   ```html
   <li class="nav-item">
       <a class="nav-link" href="{% url 'auth_dashboard:coupon_list' %}">
           <i class="fas fa-tags"></i>
           <span>Coupons</span>
       </a>
   </li>
   ```

4. **Test the System**
   - Visit `/admin/coupons/`
   - Create a test coupon
   - Edit, activate/deactivate, delete

## ✨ Features

✅ Full CRUD operations
✅ Search & filter functionality
✅ Usage statistics
✅ Visual progress bars
✅ Status badges
✅ Pagination
✅ Usage history tracking
✅ Responsive design
✅ User-friendly interface

All backend code is complete! Just create the template files and you're ready to go!
