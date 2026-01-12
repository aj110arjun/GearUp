# Production Deployment Guide - Static Files

## Issue
Product page works in development but not in production. JavaScript functions (selectVariant, addToCart, etc.) are undefined.

## Root Cause
Static files (JavaScript) not uploaded to Cloudinary in production environment.

## Solution Steps

### 1. Activate Virtual Environment
```bash
cd /home/arjun-aj/Documents/project/project3
source venv/bin/activate
cd src/GearUp
```

### 2. Collect and Upload Static Files to Cloudinary
```bash
python manage.py collectstatic --noinput --clear
```

**Expected Output:**
- Should show files being uploaded to Cloudinary
- Look for: "X static files copied to Cloudinary"

### 3. Verify Upload
1. Go to https://cloudinary.com/console
2. Navigate to Media Library
3. Find `staticfiles/js/user/product_details.js`
4. Check timestamp is recent

### 4. Test in Production
1. Open production site in **incognito/private mode** (to avoid cache)
2. Open DevTools (F12) → Console tab
3. Reload product page
4. Look for these console messages:
   - `[ProductDetails] Script executing...`
   - `[ProductDetails] Main script loaded successfully`
   
5. Test functionality:
   - Click variant chips → images should change
   - Click +/- quantity buttons → should work
   - Click "Add to Cart" → should add to cart
   - Check price updates when selecting variants

### 5. If Still Not Working

**Check Network Tab:**
- Look for `product_details.js` in Network tab
- If 404: File not uploaded to Cloudinary
- If 403: Permission issue with Cloudinary
- If 200 but still broken: Check Console for JavaScript errors

**Clear All Caches:**
```bash
# In browser
Ctrl+Shift+Delete → Clear all cache

# Or use incognito mode
Ctrl+Shift+N (Chrome)
Ctrl+Shift+P (Firefox)
```

**Re-deploy with higher version:**
- Edit template line 941
- Change `v=6` to `v=7`
- Run collectstatic again

## What Changed

### Template (product_details.html)
- Added preload hint for faster script loading
- Implemented action queue system
- Enhanced stub functions to queue user actions
- Added error handling and user feedback
- Version bumped to v=6

### JavaScript (product_details.js)
- Added console logging for debugging
- Script now signals when it loads successfully

## Version History
- v=4: Original version
- v=5: Added dynamic timestamp cache busting
- v=6: Added action queue and error handling (current)

## Troubleshooting

### Problem: "Failed to load page resources"
**Solution:** 
- Check Cloudinary credentials in .env
- Verify STATICFILES_STORAGE setting
- Run collectstatic command

### Problem: Stub functions still being called
**Solution:**
- Check browser console for script load errors
- Verify script URL in Network tab
- Ensure Cloudinary has the file

### Problem: Old version loading
**Solution:**
- Hard refresh: Ctrl+Shift+R
- Clear browser cache completely
- Increment version number in template

## Production Checklist

Before deploying:
- [ ] Test locally with DEBUG=True
- [ ] Run collectstatic command
- [ ] Verify Cloudinary upload
- [ ] Test in incognito mode
- [ ] Check browser console
- [ ] Test all interactive features
- [ ] Monitor error logs
