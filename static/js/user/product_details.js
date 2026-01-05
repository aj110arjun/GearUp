(function() {
    'use strict';

    const config = window.PRODUCT_DETAILS_CONFIG || {};
    const variants = config.variants || [];
    const attributes_map = config.attributes || {};
    const selectedAttributes = {};

    // --- Image Gallery Logic ---
    function initGallery() {
        const thumbnails = document.querySelectorAll('.thumb-img');
        const mainImg = document.getElementById('main-product-image');
        const imageContainer = document.getElementById('image-container');

        if (!mainImg) return;

        thumbnails.forEach(thumb => {
            thumb.addEventListener('click', function() {
                const newSrc = this.dataset.full;
                if (!newSrc) return;

                mainImg.style.opacity = '0';
                setTimeout(() => {
                    mainImg.src = newSrc;
                    mainImg.style.opacity = '1';
                }, 200);

                thumbnails.forEach(t => {
                    t.classList.remove('border-emerald-600', 'ring-2', 'ring-emerald-500/20');
                    t.classList.add('border-gray-100');
                });
                this.classList.add('border-emerald-600', 'ring-2', 'ring-emerald-500/20');
                this.classList.remove('border-gray-100');
            });
        });

        if (imageContainer) {
            imageContainer.onmousemove = (e) => {
                const { left, top, width, height } = imageContainer.getBoundingClientRect();
                const x = ((e.pageX - window.scrollX - left) / width) * 100;
                const y = ((e.pageY - window.scrollY - top) / height) * 100;
                mainImg.style.transformOrigin = `${x}% ${y}%`;
                mainImg.style.transform = 'scale(2)';
            };

            imageContainer.onmouseleave = () => {
                mainImg.style.transform = 'scale(1)';
            };
        }
    }

    window.updateGallery = function(mainImageUrl, galleryString) {
        console.log('[DEBUG] updateGallery called:', { mainImageUrl, galleryString });
        
        const mainImg = document.getElementById('main-product-image');
        const thumbContainer = document.getElementById('thumbnail-gallery-container');
        
        console.log('[DEBUG] DOM elements:', {
            hasMainImg: !!mainImg,
            hasThumbContainer: !!thumbContainer
        });
        
        if (mainImg && mainImageUrl) {
            console.log('[DEBUG] Updating main image to:', mainImageUrl);
            mainImg.src = mainImageUrl;
        }

        if (thumbContainer && galleryString) {
            const images = galleryString.split(',');
            console.log('[DEBUG] Generating thumbnails for', images.length, 'images');
            
            let html = '';
            images.forEach((imgUrl, idx) => {
                if (!imgUrl) return;
                const isSelected = imgUrl === mainImageUrl;
                html += `
                    <img src="${imgUrl}" 
                         alt="Product image"
                         data-full="${imgUrl}"
                         class="thumb-img border-2 ${isSelected ? 'border-emerald-600 ring-2 ring-emerald-500/20' : 'border-gray-100'} rounded-lg cursor-pointer h-16 w-16 object-cover transition-all hover:border-emerald-500">
                `;
            });
            thumbContainer.innerHTML = html;
            console.log('[DEBUG] Thumbnails updated, re-initializing gallery');
            initGallery(); // Re-bind events
        }
    };

    // --- Variant Selection Logic ---
    function initVariants() {
        console.log('[DEBUG] initVariants (Attribute Based) started');
        console.log('[DEBUG] Loaded configuration:', {
            variantCount: variants.length,
            variants: variants,
            attributes: attributes_map
        });
        
        const root = document.getElementById('variant-selection-root');
        
        if (!root) {
            console.warn('[DEBUG] No variant selection root found in DOM.');
        }

        // Enable buttons if no attributes exist (simple product or variation-less product)
        if (Object.keys(attributes_map).length === 0 && variants.length > 0) {
            console.log('[DEBUG] Product has variants but no selection attributes. Using table/default selection.');
            const cartBtn = document.getElementById('buy-box-cart-btn');
            if (cartBtn && config.initialVariantId) {
                const initial = variants.find(v => v.id === config.initialVariantId);
                if (initial) updateProductUI(initial);
            }
        } else if (variants.length === 0) {
            // Truly simple product with no variants at all
            const cartBtn = document.getElementById('buy-box-cart-btn');
            if (cartBtn) {
                cartBtn.disabled = false;
                cartBtn.classList.remove('bg-gray-200', 'text-gray-500', 'cursor-not-allowed', 'opacity-75');
                cartBtn.classList.add('bg-emerald-500', 'hover:bg-emerald-600', 'text-white', 'cursor-pointer');
                cartBtn.textContent = 'Add to Cart';
                cartBtn.onclick = () => window.addToCart(null); 
            }
        }
        
        if (root) {
            // Only set up click handlers if root exists
            root.addEventListener('click', function(e) {
                const btn = e.target.closest('.attr-val-btn');
                if (!btn || btn.disabled) {
                    console.log('[DEBUG] Click ignored:', { hasBtn: !!btn, disabled: btn?.disabled });
                    return;
                }

                const group = btn.closest('.attribute-group');
                const attrName = group.dataset.attributeName;
                const attrVal = btn.dataset.attributeValue;

                console.log(`[DEBUG] Attribute Selected: ${attrName} = ${attrVal}`);

                // Mark this button as selected, unmark others in group
                group.querySelectorAll('.attr-val-btn').forEach(b => {
                    b.classList.remove('border-emerald-600', 'bg-emerald-50', 'ring-2', 'ring-emerald-500/20', 'text-emerald-700');
                    b.classList.add('border-gray-100', 'text-gray-900');
                });
                btn.classList.add('border-emerald-600', 'bg-emerald-50', 'ring-2', 'ring-emerald-500/20', 'text-emerald-700');
                btn.classList.remove('border-gray-100', 'text-gray-900');

                // Update selected value display label
                const display = group.querySelector('.selected-value-display');
                if (display) {
                    display.classList.remove('hidden');
                    display.querySelector('.val').textContent = attrVal;
                }

                selectedAttributes[attrName] = attrVal;
                console.log('[DEBUG] Updated selectedAttributes:', selectedAttributes);
                
                checkAndMatchVariant();
            });
        }

        function checkAndMatchVariant() {
            const attrKeys = Object.keys(attributes_map);
            const selectedKeys = Object.keys(selectedAttributes);
            
            console.log(`[DEBUG] Selection Check: ${selectedKeys.length}/${attrKeys.length}`);

            if (selectedKeys.length === attrKeys.length) {
                // All attributes selected, find the matching variant
                const match = variants.find(v => {
                    return attrKeys.every(k => v.attributes[k] === selectedAttributes[k]);
                });

                if (match) {
                    console.log('[DEBUG] Match Found:', match.id);
                    updateProductUI(match);
                } else {
                    console.log('[DEBUG] No matching variant for selection.');
                    handleNoMatch();
                }
            } else {
                handlePartialSelection();
            }
        }

        // Make this function accessible globally so selectVariantFromTable can use it
        window.updateProductUI = updateProductUI;
        
        function updateProductUI(variant) {
            try {
                const vid = variant.id;
                const variantIdInput = document.getElementById('selected-variant-id');
                if (variantIdInput) {
                    variantIdInput.value = vid;
                } else {
                    console.log('[DEBUG] selected-variant-id element not found, variant ID:', vid);
                }

                // Price Updates
                const mainPrice = document.getElementById('main-price-display');
                const mainOriginal = document.getElementById('main-original-price');
                const buyBoxPrice = document.getElementById('buy-box-price');
                
                if (mainPrice) mainPrice.textContent = `₹${variant.discounted_price.toLocaleString()}`;
                if (buyBoxPrice) buyBoxPrice.textContent = `₹${variant.discounted_price.toLocaleString()}`;
                if (mainOriginal) {
                    mainOriginal.textContent = variant.price > variant.discounted_price ? `₹${variant.price.toLocaleString()}` : '';
                }

                // Discount Badge
                const discountPercent = document.getElementById('main-discount-percent');
                if (discountPercent) {
                    const discount = Math.round(((variant.price - variant.discounted_price) / variant.price) * 100);
                    discountPercent.textContent = `-${discount}%`;
                    discountPercent.classList.toggle('hidden', discount <= 0);
                }

                // Stock Status
                const buyBoxStock = document.getElementById('buy-box-stock-text');
                const mainStockBadge = document.getElementById('main-stock-badge');
                const selectionHint = document.getElementById('selection-hint');

                let stockText = 'Out of Stock';
                let stockClass = 'text-red-600';
                let badgeClass = 'bg-red-100 text-red-800';

                if (variant.stock > 0) {
                    stockText = variant.stock <= 5 ? `Only ${variant.stock} left!` : 'In Stock';
                    stockClass = variant.stock <= 5 ? 'text-orange-600' : 'text-green-700';
                    badgeClass = variant.stock <= 5 ? 'bg-orange-100 text-orange-800' : 'bg-green-100 text-green-800';
                }

                if (buyBoxStock) {
                    buyBoxStock.textContent = stockText;
                    buyBoxStock.className = `${stockClass} text-lg font-medium`;
                }

                if (mainStockBadge) {
                    mainStockBadge.innerHTML = `<i class="fas fa-check-circle mr-1"></i> ${stockText}`;
                    mainStockBadge.className = `inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${badgeClass}`;
                }

                if (selectionHint) selectionHint.classList.add('hidden');
                
                // Update table highlight
                document.querySelectorAll('#variants-table-body tr').forEach(row => {
                    row.classList.remove('bg-emerald-50', 'ring-1', 'ring-emerald-200');
                    const btnText = row.querySelector('.select-btn-text');
                    if (btnText) {
                        btnText.textContent = 'Select';
                    }
                    
                    if (row.dataset.variantId === vid) {
                        row.classList.add('bg-emerald-50', 'ring-1', 'ring-emerald-200');
                        if (btnText) {
                            btnText.textContent = 'Selected';
                        }
                    }
                });

                // Buttons
                const cartBtn = document.getElementById('buy-box-cart-btn');
                
                if (cartBtn) {
                    if (variant.in_cart) {
                        cartBtn.disabled = false;
                        cartBtn.classList.remove('bg-gray-200', 'text-gray-500', 'cursor-not-allowed', 'opacity-75', 'bg-emerald-500', 'hover:bg-emerald-600');
                        cartBtn.classList.add('bg-blue-600', 'hover:bg-blue-700', 'text-white', 'cursor-pointer');
                        cartBtn.innerHTML = '<i class="fas fa-shopping-cart mr-2"></i> Go to Cart';
                        cartBtn.onclick = () => window.location.href = config.cartUrl || '/shop/cart/';
                    } else if (variant.stock > 0) {
                        cartBtn.disabled = false;
                        cartBtn.classList.remove('bg-gray-200', 'text-gray-500', 'cursor-not-allowed', 'opacity-75', 'bg-blue-600', 'hover:bg-blue-700');
                        cartBtn.classList.add('bg-emerald-500', 'hover:bg-emerald-600', 'text-white', 'cursor-pointer');
                        cartBtn.innerHTML = 'Add to Cart';
                        cartBtn.onclick = () => window.addToCart(vid);
                    } else {
                        cartBtn.disabled = true;
                        cartBtn.classList.add('bg-gray-200', 'text-gray-500', 'cursor-not-allowed', 'opacity-75');
                        cartBtn.classList.remove('bg-emerald-500', 'hover:bg-emerald-600', 'bg-blue-600', 'hover:bg-blue-700', 'text-white', 'cursor-pointer');
                        cartBtn.textContent = 'Out of Stock';
                    }
                }

                // Gallery Update
                const galleryImages = variant.gallery || [];
                const mainImageUrl = variant.main_image || (galleryImages.length > 0 ? galleryImages[0] : null);
                
                console.log('[DEBUG] Gallery Update:', {
                    variantId: vid,
                    mainImageUrl,
                    galleryCount: galleryImages.length,
                    gallery: galleryImages
                });
                
                if (mainImageUrl && typeof window.updateGallery === 'function') {
                    window.updateGallery(mainImageUrl, galleryImages.join(','));
                } else {
                    console.warn('[DEBUG] Gallery update skipped:', {
                        hasMainImage: !!mainImageUrl,
                        hasUpdateFunction: typeof window.updateGallery === 'function'
                    });
                }

            } catch (err) {
                console.error('[DEBUG] UI Update Error:', err);
            }
        }

        function handlePartialSelection() {
            const buyBoxPrice = document.getElementById('buy-box-price');
            if (buyBoxPrice) buyBoxPrice.textContent = 'Select Options';
            
            const selectionHint = document.getElementById('selection-hint');
            if (selectionHint) selectionHint.classList.remove('hidden');

            const cartBtn = document.getElementById('buy-box-cart-btn');
            if (cartBtn) {
                cartBtn.disabled = true;
                cartBtn.classList.add('bg-gray-200', 'text-gray-500', 'cursor-not-allowed', 'opacity-75');
                cartBtn.classList.remove('bg-emerald-500', 'text-white');
            }
        }

        function handleNoMatch() {
            const buyBoxStock = document.getElementById('buy-box-stock-text');
            if (buyBoxStock) {
                buyBoxStock.textContent = 'Not Available';
                buyBoxStock.className = 'text-gray-500 text-lg font-medium';
            }
            handlePartialSelection();
        }

        // Auto-select initial variant or handle no-attribute variants
        if (config.initialVariantId) {
            const initial = variants.find(v => v.id === config.initialVariantId);
            if (initial) {
                console.log('[DEBUG] Auto-selecting initial variant:', initial.id);
                
                // Check if this variant has attributes
                const hasAttributes = Object.keys(initial.attributes || {}).length > 0;
                
                if (hasAttributes) {
                    // Normal variant with attributes - trigger clicks
                    Object.entries(initial.attributes).forEach(([name, val]) => {
                        if (root) {
                            const btn = root.querySelector(`.attribute-group[data-attribute-name="${name}"] .attr-val-btn[data-attribute-value="${val}"]`);
                            if (btn) btn.click();
                        }
                    });
                } else {
                    // Simple variant with no attributes - directly update UI
                    console.log('[DEBUG] Variant has no attributes, enabling direct purchase');
                    const variantIdInput = document.getElementById('selected-variant-id');
                    if (variantIdInput) {
                        variantIdInput.value = initial.id;
                    } else {
                        console.log('[DEBUG] selected-variant-id element not found during auto-selection');
                    }
                    updateProductUI(initial);
                }
            }
        }
    }

    // --- Star Rating Functionality ---
    function initStarRating(containerId, valueId, labelId, starClass) {
        const container = document.getElementById(containerId);
        if (!container) return;

        const stars = container.querySelectorAll('.star-btn');
        const input = document.getElementById(valueId);
        const label = document.getElementById(labelId);

        const ratings = {
            1: "I hate it",
            2: "I don't like it",
            3: "It's okay",
            4: "I like it",
            5: "I love it"
        };

        stars.forEach(star => {
            star.addEventListener('mouseenter', function() {
                const val = this.dataset.rating;
                updateStars(val, true);
            });

            star.addEventListener('mouseleave', function() {
                updateStars(input.value || 0, false);
            });

            star.addEventListener('click', function() {
                const val = this.dataset.rating;
                input.value = val;
                updateStars(val, false);
                if (label) label.textContent = ratings[val];
            });
        });

        function updateStars(val, isHover) {
            stars.forEach(s => {
                const sVal = s.dataset.rating;
                if (sVal <= val) {
                    s.classList.add('text-yellow-400');
                    s.classList.remove('text-gray-300');
                } else {
                    s.classList.remove('text-yellow-400');
                    s.classList.add('text-gray-300');
                }
            });
        }
    }

    // --- Page Initialization ---
    function init() {
        console.log('[DEBUG] Product Details JS Init...');
        initGallery();
        initVariants();
        
        // Character counters for reviews
        const setupCounter = (inputId, counterId) => {
            const input = document.getElementById(inputId);
            const counter = document.getElementById(counterId);
            if (input && counter) {
                input.addEventListener('input', () => counter.textContent = input.value.length);
            }
        };

        setupCounter('review-comment', 'char-count');
        setupCounter('edit-review-comment', 'edit-char-count');

        initStarRating('star-rating-input', 'rating-value', 'rating-label');
        initStarRating('edit-star-rating-input', 'edit-rating-value', 'edit-rating-label');

        // Review votes using delegation
        const reviewsContainer = document.getElementById('reviews-container');
        if (reviewsContainer) {
            reviewsContainer.addEventListener('click', e => {
                const btn = e.target.closest('.review-vote-btn');
                if (btn) {
                    e.preventDefault();
                    if (window.voteReview) window.voteReview(btn.dataset.reviewId, btn.dataset.voteType);
                }
            });
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();

// Global Utilities
window.addToCart = function(variantId) {
    if (!variantId) {
        console.warn('No variant ID provided to addToCart');
        return;
    }
    const config = window.PRODUCT_DETAILS_CONFIG || {};
    if (!config.isUserAuthenticated) {
        window.location.href = '/auth/login/?next=' + window.location.pathname;
        return;
    }

    if (window.globalApiPOST) {
        // Find the button and show loading state
        const cartBtn = document.getElementById('buy-box-cart-btn');
        const originalText = cartBtn ? cartBtn.textContent : 'Add to Cart';
        
        if (cartBtn) {
            cartBtn.disabled = true;
            cartBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Adding...';
        }

        window.globalApiPOST(config.cartAddUrl || '/cart/add/', {
            variant_id: variantId,
            quantity: 1
        }).then(data => {
            if (data.success) {
                if (window.updateCartCount) window.updateCartCount(data.cart_count);
                
                if (cartBtn) {
                    cartBtn.innerHTML = '<i class="fas fa-check mr-2"></i> Added!';
                    cartBtn.classList.remove('bg-emerald-500', 'hover:bg-emerald-600');
                    cartBtn.classList.add('bg-blue-600', 'hover:bg-blue-700');
                    
                    setTimeout(() => {
                        cartBtn.disabled = false;
                        cartBtn.innerHTML = '<i class="fas fa-shopping-cart mr-2"></i> Go to Cart';
                        cartBtn.onclick = () => window.location.href = config.cartUrl || '/shop/cart/';
                    }, 1500);
                }

                // Update the variant's in_cart status locally so it persists if they switch back/forth
                const v = variants.find(v => v.id === variantId);
                if (v) v.in_cart = true;

                if (window.showNotification) {
                    window.showNotification('Product added to cart!', 'success');
                }
            } else {
                if (cartBtn) {
                    cartBtn.disabled = false;
                    cartBtn.textContent = originalText;
                }
                if (window.showNotification) {
                    window.showNotification(data.message || 'Failed to add product to cart', 'error');
                }
            }
        }).catch(err => {
            console.error('Add to cart error:', err);
            if (cartBtn) {
                cartBtn.disabled = false;
                cartBtn.textContent = originalText;
            }
        });
    }
};

window.confirmDeleteReview = function(form) {
    if (window.showConfirmModal) {
        window.showConfirmModal({
            title: 'Delete Review?',
            message: 'Are you sure you want to delete your review? This action cannot be undone.',
            confirmText: 'Delete',
            cancelText: 'Cancel',
            variant: 'danger',
            onConfirm: () => form.submit()
        });
    } else if (confirm('Are you sure you want to delete your review?')) {
        form.submit();
    }
};
