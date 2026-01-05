# Variant Selection Debug Guide

## Overview
This guide helps debug variant image selection issues on product detail pages.

## Console Debug Messages to Look For

### 1. On Page Load
```
[DEBUG] Product Details JS Init...
[DEBUG] initVariants (Attribute Based) started
[DEBUG] Loaded configuration: { variantCount: X, variants: [...], attributes: {...} }
```
**What to Check:**
- `variantCount` should match the number of product variants
- `variants` array should contain objects with: id, price, discounted_price, stock, attributes, main_image, gallery
- `attributes` object should have attribute names as keys (e.g., {"Color": ["Red", "Blue"], "Size": ["M", "L"]})

### 2. When Clicking an Attribute Button (e.g., Color: Red)
```
[DEBUG] Attribute Selected: Color = Red
[DEBUG] Updated selectedAttributes: {Color: "Red"}
[DEBUG] Selection Check: 1/2
```
**What to Check:**
- Attribute name and value should match exactly
- `selectedAttributes` should accumulate selections
- Selection count should increase with each attribute selected

### 3. When All Attributes Selected
```
[DEBUG] Selection Check: 2/2
[DEBUG] Match Found: <variant-uuid>
[DEBUG] Gallery Update: { variantId: "...", mainImageUrl: "...", galleryCount: 3, gallery: [...] }
[DEBUG] updateGallery called: { mainImageUrl: "...", galleryString: "..." }
[DEBUG] DOM elements: { hasMainImg: true, hasThumbContainer: true }
[DEBUG] Updating main image to: <url>
[DEBUG] Generating thumbnails for 3 images
[DEBUG] Thumbnails updated, re-initializing gallery
```
**What to Check:**
- "Match Found" confirms a variant was identified
- `mainImageUrl` should be a valid image URL
- `galleryCount` should be > 0
- DOM elements should both be `true`
- Thumbnails should be generated

### 4. When Using "Select" Button in Variations Table
```
[DEBUG] selectVariantFromTable called with variantId: <uuid>
[DEBUG] Found variant: {...}
[DEBUG] Variant attributes: {Color: "Red", Size: "M"}
[DEBUG] Processing 2 attributes: ["Color", "Size"]
[DEBUG] Looking for attribute: Color = Red
[DEBUG] Found button for Color, clicking...
[DEBUG] Clicked Color button
[DEBUG] Looking for attribute: Size = M
[DEBUG] Found button for Size, clicking...
[DEBUG] Clicked Size button
```
**What to Check:**
- Variant should be found
- All attributes should have matching buttons
- Clicks should be sequential (100ms apart)
- Each click should trigger the normal attribute selection flow above

## Common Issues and Solutions

### Issue 1: "Variant not found" Error
**Symptom:** Console shows `[DEBUG] Variant not found: <id>`
**Cause:** Variant ID from table doesn't match IDs in variants_json
**Solution:** Check backend view is properly serializing variant IDs as strings

### Issue 2: "Button not found for..." Error
**Symptom:** Console shows `[DEBUG] Button not found for Color = Red`
**Cause:** Attribute name or value doesn't match HTML data attributes
**Solution:** 
- Check HTML: `<button data-attribute-value="Red">` matches exactly
- Check attribute group: `<div data-attribute-name="Color">` matches exactly
- Case sensitivity matters!

### Issue 3: Images Don't Update
**Symptom:** Variant matches but images don't change
**Causes:**
1. No gallery images in variant data → Check backend is populating `v_gallery`
2. DOM elements not found → Check `hasMainImg` and `hasThumbContainer` are both true
3. Image URLs are invalid → Check `mainImageUrl` in console

### Issue 4: Add to Cart Still Disabled
**Symptom:** All attributes selected but cart button disabled
**Cause:** `updateProductUI` not being called or stock is 0
**Solution:**
- Verify "Match Found" message appears
- Check `variant.stock` value in console
- Verify button enable code is executing

## Testing Checklist

1. [ ] Open browser DevTools (F12) and go to Console tab
2. [ ] Navigate to a product with multiple variants
3. [ ] Verify initial configuration logs appear
4. [ ] Click first attribute (e.g., Color)
5. [ ] Verify "Attribute Selected" message
6. [ ] Click second attribute (e.g., Size)  
7. [ ] Verify "Match Found" and "Gallery Update" messages
8. [ ] Verify images update visually
9. [ ] Click "Select" button in variations table
10. [ ] Verify all debug messages for table selection
11. [ ] Verify images update again

## Expected Behavior

✅ When functioning correctly:
- Attribute buttons change appearance when clicked (green border)
- Price updates after all attributes selected
- Stock status updates
- Main image changes immediately
- Thumbnail gallery rebuilds with new images
- "Add to Cart" button becomes enabled (if in stock)
- Clicking thumbnails changes main image

## Files Modified for Debugging

```
common/products/views.py         - JSON serialization of variant data
templates/user/products/product_details.html - Config object, selectVariantFromTable
static/js/user/product_details.js - All variant selection logic, gallery updates
```
