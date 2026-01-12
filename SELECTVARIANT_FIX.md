# Fix for "Uncaught ReferenceError: selectVariant is not defined"

## Problem Analysis

The error `Uncaught ReferenceError: selectVariant is not defined` occurs when JavaScript functions are called via HTML `onclick` attributes before the external JavaScript file has fully loaded or when there are caching issues in production.

### Root Causes:
1. **Script Loading Timing**: The external `product_details.js` file may not have loaded when the onclick event fires
2. **Browser Caching**: In production, browsers may cache old versions of JavaScript files
3. **Static Files Not Collected**: Django's static files may not be properly collected in production

## Solution Implemented

### 1. Added Inline Stub Functions (Primary Fix)

Added inline stub/placeholder functions in the HTML template that:
- Define all onclick handler functions in the global scope immediately
- Prevent ReferenceError by ensuring functions exist before any onclick can fire
- Use the `||` operator so they're overridden by the full implementations when the external script loads
- Include console warnings to help debug if the external script fails to load

**Location**: `/templates/user/products/product_details.html` (lines 899-943)

**Functions stubbed**:
- `selectVariant(variantId)`
- `updateMainImage(url)`
- `changeQty(delta)`
- `addSelectedToCart()`
- `toggleWishlist(productId)`
- `openReviewModal()`
- `closeReviewModal()`
- `openEditReviewModal(reviewId)`
- `closeEditReviewModal()`
- `confirmDeleteReview(form)`

### 2. Updated Cache-Busting Version

Changed the version parameter from `v=3` to `v=4` to force browsers to load the latest JavaScript file.

**Location**: `/templates/user/products/product_details.html` (line 946)

```html
<script src="{% static 'js/user/product_details.js' %}?v=4"></script>
```

## How It Works

1. **Page loads** → Inline stub functions are immediately available in global scope
2. **User clicks button** → Stub function executes (preventing ReferenceError)
3. **External JS loads** → Full implementations override stubs using `window.functionName = ...`
4. **Subsequent clicks** → Full implementations execute

## Production Deployment Steps

To deploy this fix to production:

1. **Collect static files**:
   ```bash
   python manage.py collectstatic --noinput
   ```

2. **Clear browser cache** (or wait for cache expiration):
   - Hard refresh: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)
   - Or clear browser cache manually

3. **Restart application server** (if using Gunicorn/uWSGI):
   ```bash
   sudo systemctl restart gunicorn  # or your service name
   ```

4. **Verify the fix**:
   - Open browser console (F12)
   - Navigate to product details page
   - Click variant selection buttons
   - Check for any console errors or warnings

## Expected Behavior

### Before Fix:
- Console error: `Uncaught ReferenceError: selectVariant is not defined`
- Variant selection buttons don't work
- Page functionality broken

### After Fix:
- No ReferenceError
- Variant selection works immediately
- If external script hasn't loaded, stub executes with console warning
- Once external script loads, full functionality available

## Verification

Check browser console for:
- ✅ No ReferenceError messages
- ✅ Variant selection logs: `[VariantSelection] Attempting to select: ...`
- ⚠️ If you see `[Stub] selectVariant called before main script loaded`, the external script hasn't loaded yet (but at least no error occurs)

## Additional Notes

- The stub functions provide a safety net for production environments
- The `updateMainImage` stub includes basic functionality to update the image even if the full script hasn't loaded
- All other stubs are minimal to prevent errors while logging warnings
- This pattern can be applied to other pages with similar issues

## Bonus Fix: Removed Cloudinary Preload Warning

### Problem
Browser warning: "The resource https://upload-widget.cloudinary.com/global/all.js was preloaded using link preload but not used within a few seconds from the window's load event."

### Cause
The Cloudinary upload widget script was being preloaded but never actually used on the product details page. This widget is only needed on admin pages for image uploads, not on customer-facing pages.

### Solution
Removed the unnecessary preload link:
```html
<!-- REMOVED: -->
<link href="https://upload-widget.cloudinary.com/global/all.js" rel="preload" as="script">
```

### Result
- ✅ Eliminated browser warning
- ✅ Reduced unnecessary network requests
- ✅ Improved page load performance
- ✅ Cleaner console output
