# Coupon System Implementation Guide

## ✅ What Has Been Done

### 1. **Models Created** (`common/orders/models.py`)

#### **Coupon Model**
- `code` - Unique coupon code (auto-converts to uppercase)
- `description` - Description of the offer
- `discount_percentage` - Percentage discount (e.g., 10.00 for 10% off)
- `max_uses` - Maximum total uses (0 = unlimited)
- `used_count` - Tracks how many times used
- `max_uses_per_user` - Maximum uses per user
- `minimum_order_amount` - Minimum order required
- `max_discount_amount` - Optional cap on discount
- `valid_from` / `valid_until` - Validity period
- `is_active` - Enable/disable coupon

**Methods:**
- `is_valid()` - Check if coupon is currently valid
- `can_be_used_by_user(user)` - Check user eligibility
- `calculate_discount(amount)` - Calculate discount for order
- `increment_usage()` - Increment usage count

#### **CouponUsage Model**
Tracks each coupon usage:
- `coupon` - Which coupon was used
- `user` - Who used it
- `order` - Which order it was applied to
- `discount_amount` - Actual discount given
- `used_at` - Timestamp

#### **Order Model Updates**
Added fields:
- `coupon_code` - Stores applied coupon code
- `coupon_discount` - Stores discount amount

### 2. **Admin Interface Created** (`common/orders/admin.py`)

#### **CouponAdmin Features:**
- **List Display**: Code, discount %, usage stats, validity status
- **Filters**: Active status, validity dates
- **Search**: By code or description
- **Fieldsets**: Organized into logical sections
- **Custom Displays**:
  - Usage info with color coding (green/orange/red)
  - Validity status with visual indicators
- **Actions**: Bulk activate/deactivate coupons
- **Auto-set**: Created_by field on save

#### **CouponUsageAdmin Features:**
- **Read-only**: Cannot add/edit manually
- **Displays**: Coupon code, user, order, discount, date
- **Tracking**: Complete audit trail of all coupon uses

## 🔧 Next Steps - Implementation

### Step 1: Run Migrations

```bash
# In your terminal where the server is running, stop it (Ctrl+C)
python manage.py makemigrations
python manage.py migrate

# Restart server
python manage.py runserver
```

### Step 2: Create API View for Coupon Validation

Create `/common/orders/views.py` (or add to existing):

```python
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json
from decimal import Decimal
from .models import Coupon

@login_required
@require_POST
def validate_coupon(request):
    """
    Validate and apply coupon code
    """
    try:
        data = json.loads(request.body)
        coupon_code = data.get('coupon_code', '').strip().upper()
        order_amount = Decimal(str(data.get('order_amount', 0)))
        
        if not coupon_code:
            return JsonResponse({
                'success': False,
                'message': 'Please enter a coupon code'
            })
        
        # Get coupon
        try:
            coupon = Coupon.objects.get(code=coupon_code)
        except Coupon.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Invalid coupon code'
            })
        
        # Check if coupon is valid
        is_valid, message = coupon.is_valid()
        if not is_valid:
            return JsonResponse({
                'success': False,
                'message': message
            })
        
        # Check if user can use this coupon
        can_use, message = coupon.can_be_used_by_user(request.user)
        if not can_use:
            return JsonResponse({
                'success': False,
                'message': message
            })
        
        # Check minimum order amount
        if order_amount < coupon.minimum_order_amount:
            return JsonResponse({
                'success': False,
                'message': f'Minimum order amount of ₹{coupon.minimum_order_amount} required'
            })
        
        # Calculate discount
        discount_amount = coupon.calculate_discount(order_amount)
        new_total = order_amount - discount_amount
        
        return JsonResponse({
            'success': True,
            'message': f'Coupon "{coupon.code}" applied successfully!',
            'coupon_code': coupon.code,
            'discount_percentage': float(coupon.discount_percentage),
            'discount_amount': float(discount_amount),
            'original_amount': float(order_amount),
            'new_total': float(new_total)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)
```

### Step 3: Add URL Pattern

In `/common/orders/urls.py`:

```python
from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # ... existing patterns ...
    path('validate-coupon/', views.validate_coupon, name='validate_coupon'),
]
```

### Step 4: Update Checkout Template

Add this to `/templates/user/orders/checkout.html` in the order summary section:

```html
<!-- Coupon Section -->
<div class="bg-white rounded-lg shadow-sm p-6 mb-6">
    <h3 class="text-lg font-semibold text-gray-800 mb-4 flex items-center">
        <i class="fas fa-tag text-emerald-500 mr-2"></i>
        Apply Coupon Code
    </h3>
    
    <div class="flex gap-2">
        <input type="text" 
               id="coupon-code-input"
               placeholder="Enter coupon code" 
               class="flex-1 px-4 py-3 border-2 border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent uppercase"
               maxlength="50">
        <button id="apply-coupon-btn"
                class="bg-emerald-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-emerald-700 transition-colors flex items-center gap-2">
            <i class="fas fa-check"></i>
            Apply
        </button>
    </div>
    
    <!-- Coupon Message -->
    <div id="coupon-message" class="mt-3 hidden"></div>
    
    <!-- Applied Coupon Display -->
    <div id="applied-coupon" class="mt-4 hidden">
        <div class="bg-emerald-50 border-2 border-emerald-200 rounded-lg p-4 flex items-center justify-between">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 bg-emerald-500 rounded-full flex items-center justify-center">
                    <i class="fas fa-check text-white"></i>
                </div>
                <div>
                    <p class="font-semibold text-emerald-800" id="applied-coupon-code"></p>
                    <p class="text-sm text-emerald-600" id="applied-coupon-discount"></p>
                </div>
            </div>
            <button id="remove-coupon-btn" 
                    class="text-red-600 hover:text-red-700 font-medium">
                <i class="fas fa-times"></i> Remove
            </button>
        </div>
    </div>
</div>

<!-- Update Order Summary to show discount -->
<div class="bg-white rounded-lg shadow-sm p-6">
    <h3 class="text-lg font-semibold mb-4">Order Summary</h3>
    
    <div class="space-y-3">
        <div class="flex justify-between">
            <span>Subtotal</span>
            <span id="subtotal-amount">₹{{ cart.subtotal }}</span>
        </div>
        
        <!-- Coupon Discount Line -->
        <div id="coupon-discount-line" class="flex justify-between text-green-600 hidden">
            <span>Coupon Discount</span>
            <span id="coupon-discount-amount">-₹0.00</span>
        </div>
        
        <div class="flex justify-between">
            <span>Shipping</span>
            <span class="text-green-600">FREE</span>
        </div>
        
        <div class="border-t pt-3 flex justify-between items-center">
            <span class="text-lg font-bold">Total</span>
            <span class="text-2xl font-bold text-emerald-600" id="final-total">₹{{ cart.final_total }}</span>
        </div>
    </div>
</div>

<script>
// Coupon functionality
let appliedCoupon = null;
let originalTotal = parseFloat('{{ cart.final_total }}');

document.getElementById('apply-coupon-btn').addEventListener('click', function() {
    const couponCode = document.getElementById('coupon-code-input').value.trim();
    
    if (!couponCode) {
        showCouponMessage('Please enter a coupon code', 'error');
        return;
    }
    
    // Show loading
    this.disabled = true;
    this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Applying...';
    
    fetch('{% url "orders:validate_coupon" %}', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': '{{ csrf_token }}'
        },
        body: JSON.stringify({
            coupon_code: couponCode,
            order_amount: originalTotal
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            appliedCoupon = data;
            showAppliedCoupon(data);
            updateOrderTotal(data);
            showCouponMessage(data.message, 'success');
        } else {
            showCouponMessage(data.message, 'error');
        }
    })
    .catch(error => {
        showCouponMessage('Error applying coupon. Please try again.', 'error');
    })
    .finally(() => {
        document.getElementById('apply-coupon-btn').disabled = false;
        document.getElementById('apply-coupon-btn').innerHTML = '<i class="fas fa-check"></i> Apply';
    });
});

document.getElementById('remove-coupon-btn').addEventListener('click', function() {
    appliedCoupon = null;
    document.getElementById('applied-coupon').classList.add('hidden');
    document.getElementById('coupon-discount-line').classList.add('hidden');
    document.getElementById('final-total').textContent = '₹' + originalTotal.toFixed(2);
    document.getElementById('coupon-code-input').value = '';
    showCouponMessage('Coupon removed', 'info');
});

function showAppliedCoupon(data) {
    document.getElementById('applied-coupon').classList.remove('hidden');
    document.getElementById('applied-coupon-code').textContent = data.coupon_code;
    document.getElementById('applied-coupon-discount').textContent = 
        `${data.discount_percentage}% off - Save ₹${data.discount_amount.toFixed(2)}`;
}

function updateOrderTotal(data) {
    document.getElementById('coupon-discount-line').classList.remove('hidden');
    document.getElementById('coupon-discount-amount').textContent = '-₹' + data.discount_amount.toFixed(2);
    document.getElementById('final-total').textContent = '₹' + data.new_total.toFixed(2);
}

function showCouponMessage(message, type) {
    const messageDiv = document.getElementById('coupon-message');
    messageDiv.classList.remove('hidden');
    
    const colors = {
        success: 'bg-green-50 border-green-200 text-green-800',
        error: 'bg-red-50 border-red-200 text-red-800',
        info: 'bg-blue-50 border-blue-200 text-blue-800'
    };
    
    messageDiv.className = `mt-3 p-3 rounded-lg border-2 ${colors[type]}`;
    messageDiv.innerHTML = `<i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i> ${message}`;
    
    setTimeout(() => {
        messageDiv.classList.add('hidden');
    }, 5000);
}
</script>
```

### Step 5: Update Checkout View

In your checkout view, when creating orders, apply the coupon:

```python
# In your checkout view
if appliedCoupon:
    coupon = Coupon.objects.get(code=appliedCoupon['coupon_code'])
    discount_amount = coupon.calculate_discount(order_total)
    
    # Update order
    order.coupon_code = coupon.code
    order.coupon_discount = discount_amount
    order.total_amount = order_total - discount_amount
    order.save()
    
    # Record usage
    CouponUsage.objects.create(
        coupon=coupon,
        user=request.user,
        order=order,
        discount_amount=discount_amount
    )
    
    # Increment coupon usage
    coupon.increment_usage()
```

## 📊 Admin Usage

### Creating a Coupon

1. Go to Django Admin
2. Click "Coupons" → "Add Coupon"
3. Fill in:
   - **Code**: SAVE20 (will auto-convert to uppercase)
   - **Description**: "20% off on all orders"
   - **Discount Percentage**: 20.00
   - **Max Uses**: 100 (or 0 for unlimited)
   - **Max Uses Per User**: 1
   - **Minimum Order Amount**: 500.00
   - **Max Discount Amount**: 200.00 (optional cap)
   - **Valid From**: Start date/time
   - **Valid Until**: End date/time
   - **Is Active**: ✓ Checked

### Managing Coupons

- **View Usage**: See how many times each coupon has been used
- **Activate/Deactivate**: Bulk actions to enable/disable coupons
- **Track Usage**: View all coupon usages in "Coupon Usages"

## 🎯 Features

✅ **Percentage-based discounts**
✅ **Usage limits** (total and per user)
✅ **Minimum order requirements**
✅ **Maximum discount caps**
✅ **Validity periods**
✅ **Active/inactive status**
✅ **Complete audit trail**
✅ **Admin CRUD interface**
✅ **Real-time validation**
✅ **User-friendly checkout integration**

## 🔒 Security Features

- Uppercase code normalization
- Validation before application
- Usage tracking per user
- Expiry date enforcement
- Maximum usage limits
- Minimum order requirements

## 📝 Example Coupons

```
WELCOME10 - 10% off, no minimum, 1 use per user
SAVE20    - 20% off, ₹500 minimum, max ₹200 discount
MEGA50    - 50% off, ₹2000 minimum, max ₹500 discount, limited to 50 uses
```

## Next: Run migrations and test!
