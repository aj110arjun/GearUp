# Quick Testing Guide - Cart & Wishlist AJAX Fix

## Prerequisites
- Server is running at http://127.0.0.1:8000/
- You are logged in as a user
- You have products available in the shop

## Test Steps

### Test 1: Add Product from Cart to Wishlist
1. Navigate to the product listing page: http://127.0.0.1:8000/products/
2. Find a product and click "Add to Cart"
   - ✅ Button should turn green and show "In Cart"
   - ✅ Cart badge in header should increase
3. Now click the heart icon (wishlist button) on the same product
   - ✅ Heart should fill with red color
   - ✅ Cart button should immediately change back to "Add to Cart" (emerald color)
   - ✅ Cart badge should decrease
   - ✅ Wishlist badge should increase
   - ✅ Success notification should appear
   - **❌ NO PAGE REFRESH SHOULD BE NEEDED**

### Test 2: Add Product from Wishlist to Cart
1. On the product listing page, find a product NOT in cart
2. Click the heart icon (wishlist button)
   - ✅ Heart should fill with red color
   - ✅ Wishlist badge should increase
3. Now click "Add to Cart" on the same product
   - ✅ Button should turn green and show "In Cart"
   - ✅ Heart should immediately change to outline (gray)
   - ✅ Wishlist badge should decrease
   - ✅ Cart badge should increase
   - ✅ Success notification should appear
   - **❌ NO PAGE REFRESH SHOULD BE NEEDED**

### Test 3: Toggle Cart Button
1. Find a product and click "Add to Cart"
   - ✅ Button turns green, shows "In Cart"
2. Click the same button again
   - ✅ Button should turn emerald, show "Add to Cart"
   - ✅ Cart badge should decrease
   - **❌ NO PAGE REFRESH SHOULD BE NEEDED**

### Test 4: Toggle Wishlist Button
1. Find a product and click the heart icon
   - ✅ Heart fills with red
2. Click the heart icon again
   - ✅ Heart becomes outline (gray)
   - ✅ Wishlist badge should decrease
   - **❌ NO PAGE REFRESH SHOULD BE NEEDED**

### Test 5: Error Handling
1. Open browser console (F12)
2. Temporarily disconnect from internet or stop the server
3. Try to add a product to cart
   - ✅ Error notification should appear
   - ✅ Button should revert to original state
   - ✅ Button should be clickable again

## Expected Behavior Summary

### Cart Button States:
- **Not in Cart**: Emerald background, "Add to Cart" text, shopping cart icon
- **In Cart**: Green background, "In Cart" text, check-circle icon

### Wishlist Button States:
- **Not in Wishlist**: Gray outline heart icon
- **In Wishlist**: Red filled heart icon

### Mutual Exclusivity:
- A product can ONLY be in cart OR wishlist, never both
- When moving from cart to wishlist: cart button updates immediately
- When moving from wishlist to cart: wishlist button updates immediately

## Browser Console Checks

Open the browser console (F12) and verify:
1. No JavaScript errors appear
2. AJAX requests complete successfully (check Network tab)
3. Response includes `success: true`, `cart_count`, and `wishlist_count`

## Common Issues to Watch For

❌ **OLD BEHAVIOR (FIXED):**
- Product in cart, click wishlist → heart fills but cart button stays green
- Need to refresh page to see correct state

✅ **NEW BEHAVIOR (EXPECTED):**
- Product in cart, click wishlist → heart fills AND cart button immediately changes to "Add to Cart"
- All UI updates happen instantly without refresh

## Debugging

If issues occur:
1. Check browser console for errors
2. Check Network tab for AJAX response
3. Verify `showNotification` function exists (should be in base.js)
4. Verify `updateCartCount` and `updateWishlistCount` functions exist
5. Check that CSRF token is present in the page

## Success Criteria

✅ All cart and wishlist actions work via AJAX
✅ No page refresh required for any action
✅ UI state always matches backend state
✅ Button states, icons, and badges update immediately
✅ Clear notifications for all actions
✅ Proper error handling with user feedback
