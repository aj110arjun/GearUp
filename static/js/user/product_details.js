/**
 * Product Details logic for GearUp.
 */

(function() {
    // Signal that this script has loaded
    console.log('[ProductDetails] Script executing...');
    
    const config = window.PRODUCT_DETAILS_CONFIG || {};
    const csrftoken = window.getCookie ? window.getCookie('csrftoken') : null;

    // --- UI State Management ---
    function revealContent() {
        const skeleton = document.getElementById('skeleton-content');
        const real = document.getElementById('real-content');
        if (skeleton) skeleton.classList.add('hidden');
        if (real) {
            real.classList.remove('hidden');
            real.style.opacity = '0';
            requestAnimationFrame(() => {
                real.style.transition = 'opacity 0.5s ease-in-out';
                real.style.opacity = '1';
            });
        }
    }

    function checkInitialization() {
        if (!config.getCartDataUrl) {
            setTimeout(revealContent, 600);
            return;
        }

        fetch(config.getCartDataUrl, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(response => {
            if (!response.ok) throw new Error('API unstable');
            return response.json();
        })
        .then(data => {
            if (data.cart_count !== undefined && window.updateCartCount) {
                window.updateCartCount(data.cart_count);
            }
            setTimeout(revealContent, 600);
        })
        .catch(err => {
            console.warn('Init check failed, revealing anyway:', err);
            setTimeout(revealContent, 1000);
        });
    }

    // --- Review Management ---
    function initStarRating(containerId, inputId, labelId, starsClass) {
        const container = document.getElementById(containerId);
        const input = document.getElementById(inputId);
        const label = document.getElementById(labelId);
        if (!container || !input) return;

        const stars = container.querySelectorAll('.' + starsClass);
        const labels = {
            1: 'Poor - I hate it', 
            2: 'Fair - I don\'t like it', 
            3: 'Good - It\'s okay', 
            4: 'Very Good - I like it', 
            5: 'Excellent - I love it'
        };

        stars.forEach(star => {
            star.addEventListener('mouseenter', function() {
                const val = parseInt(this.dataset.value);
                updateStarsUI(stars, val, true);
            });

            star.addEventListener('mouseleave', function() {
                const currentVal = parseInt(input.value) || 0;
                updateStarsUI(stars, currentVal, false);
            });

            star.addEventListener('click', function() {
                const val = parseInt(this.dataset.value);
                input.value = val;
                if (label) {
                    label.textContent = labels[val];
                    label.className = 'mt-2 text-sm font-medium text-yellow-600';
                }
                updateStarsUI(stars, val, false);
            });
        });
    }

    function updateStarsUI(stars, value, isHover) {
        stars.forEach(star => {
            const val = parseInt(star.dataset.value);
            const icon = star.querySelector('i');
            if (val <= value) {
                icon.classList.replace('far', 'fas');
                icon.classList.add('text-yellow-500');
                if (isHover) icon.style.opacity = '0.7';
                else icon.style.opacity = '1';
            } else {
                icon.classList.replace('fas', 'far');
                icon.classList.remove('text-yellow-500');
                icon.style.opacity = '1';
            }
        });
    }

    window.openEditReviewModal = function(reviewId) {
        const url = config.getReviewUrl.replace('0', reviewId);
        fetch(url, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('edit-review-id').value = reviewId;
                const rating = data.review.rating;
                document.getElementById('edit-rating-value').value = rating;
                
                const stars = document.querySelectorAll('#edit-star-rating-input .edit-rating-star');
                updateStarsUI(stars, rating, false);

                const labels = {
                    1: 'Poor - I hate it', 2: 'Fair - I don\'t like it', 
                    3: 'Good - It\'s okay', 4: 'Very Good - I like it', 5: 'Excellent - I love it'
                };
                const lbl = document.getElementById('edit-rating-label');
                if (lbl) {
                    lbl.textContent = labels[rating];
                    lbl.className = 'mt-2 text-sm font-medium text-yellow-600';
                }
                
                document.getElementById('edit-review-title').value = data.review.title;
                document.getElementById('edit-review-comment').value = data.review.comment;
                document.getElementById('edit-char-count').textContent = data.review.comment.length;
                document.getElementById('edit-review-form').action = config.updateReviewUrl.replace('0', reviewId);
                document.getElementById('edit-review-modal').classList.remove('hidden');
            } else {
                if (window.showNotification) window.showNotification(data.error || 'Error loading review', 'error');
            }
        });
    };

    window.closeEditReviewModal = function() {
        const modal = document.getElementById('edit-review-modal');
        if (modal) modal.classList.add('hidden');
    };

    window.openReviewModal = function() {
        const modal = document.getElementById('review-modal');
        if (modal) modal.classList.remove('hidden');
    };

    window.closeReviewModal = function() {
        const modal = document.getElementById('review-modal');
        if (modal) modal.classList.add('hidden');
    };

    // Global form submission handler
    document.addEventListener('submit', function(e) {
        const form = e.target;
        if (form.id !== 'review-form' && form.id !== 'edit-review-form') return;
        
        e.preventDefault();
        e.stopPropagation();
        
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalHtml = submitBtn ? submitBtn.innerHTML : '';
        
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Processing...';
        }

        const formData = new FormData(form);
        const actionUrl = form.getAttribute('action') || window.location.href;
        
        fetch(actionUrl, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrftoken
            },
            body: formData
        })
        .then(response => {
            if (response.redirected) {
                window.location.href = response.url;
                return null;
            }
            return response.json();
        })
        .then(data => {
            if (!data) return;

            if (data.success) {
                if (form.id === 'review-form') {
                    window.closeReviewModal();
                } else {
                    window.closeEditReviewModal();
                }
                
                setTimeout(() => {
                    window.location.reload(true);
                }, 100);
            } else {
                let errorMessage = 'Please check the form.';
                if (data.errors) {
                    errorMessage = Object.values(data.errors).flat().join(', ');
                } else if (data.message) {
                    errorMessage = data.message;
                }
                
                if (window.showNotification) {
                    window.showNotification(errorMessage, 'error');
                } else {
                    alert('Error: ' + errorMessage);
                }
                
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalHtml;
                }
            }
        })
        .catch(error => {
            console.error('[ReviewForm] Error:', error);
            if (window.showNotification) {
                window.showNotification('Something went wrong. Please try again.', 'error');
            }
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalHtml;
            }
        });
    }, true);

    // --- Cart & Wishlist Actions ---
    window.addToCart = function(variantId) {
        if (window.globalAddToCart) window.globalAddToCart(config.productId, variantId);
    };

    window.toggleWishlist = function(productId) {
        if (window.globalToggleWishlist) window.globalToggleWishlist(productId);
    };

    window.voteReview = function(reviewId, voteType) {
        const container = document.getElementById(`review-${reviewId}`);
        if (!container) return;

        const hBtn = container.querySelector('.vote-btn-helpful');
        const nhBtn = container.querySelector('.vote-btn-nothelpful');
        if (!hBtn || !nhBtn) return;

        const btn = voteType === 'helpful' ? hBtn : nhBtn;
        const hCount = container.querySelector('.helpful-count');
        const nhCount = container.querySelector('.nothelpful-count');
        const statsHelpful = container.querySelector('.review-stats-helpful');

        const oldState = {
            h: hBtn.classList.contains('bg-blue-100'),
            nh: nhBtn.classList.contains('bg-red-100'),
            hc: parseInt(hCount.textContent) || 0,
            nhc: parseInt(nhCount.textContent) || 0
        };

        let nextH = oldState.h;
        let nextNH = oldState.nh;
        let nextHC = oldState.hc;
        let nextNHC = oldState.nhc;

        if (voteType === 'helpful') {
            if (nextH) { nextHC--; nextH = false; }
            else { 
                nextHC++; nextH = true; 
                if (nextNH) { nextNHC--; nextNH = false; }
            }
        } else {
            if (nextNH) { nextNHC--; nextNH = false; }
            else { 
                nextNHC++; nextNH = true; 
                if (nextH) { nextHC--; nextH = false; }
            }
        }

        const applyState = (h, nh, hc, nhc) => {
            hCount.textContent = hc;
            nhCount.textContent = nhc;
            if (statsHelpful) statsHelpful.textContent = `${hc} found this helpful`;

            if (h) {
                hBtn.classList.add('bg-blue-100', 'border-blue-300');
                hBtn.querySelector('i').className = 'fas fa-thumbs-up mr-2 text-blue-600';
            } else {
                hBtn.classList.remove('bg-blue-100', 'border-blue-300');
                hBtn.querySelector('i').className = 'fas fa-thumbs-up mr-2 text-gray-600';
            }

            if (nh) {
                nhBtn.classList.add('bg-red-100', 'border-red-300');
                nhBtn.querySelector('i').className = 'fas fa-thumbs-down mr-2 text-red-600';
            } else {
                nhBtn.classList.remove('bg-red-100', 'border-red-300');
                nhBtn.querySelector('i').className = 'fas fa-thumbs-down mr-2 text-gray-600';
            }
        };

        applyState(nextH, nextNH, nextHC, nextNHC);
        btn.style.transform = 'scale(0.95)';
        setTimeout(() => btn.style.transform = 'scale(1)', 100);

        if (!csrftoken) {
            if (window.showNotification) window.showNotification('Login required', 'warning');
            applyState(oldState.h, oldState.nh, oldState.hc, oldState.nhc);
            return;
        }

        const url = config.voteReviewUrl.replace('999999', reviewId);
        fetch(url, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json', 
                'X-CSRFToken': csrftoken, 
                'X-Requested-With': 'XMLHttpRequest' 
            },
            body: JSON.stringify({ vote_type: voteType })
        })
        .then(async response => {
            if (response.status === 403) {
                if (window.showNotification) window.showNotification('Please login to vote', 'warning');
                throw new Error('AUTH');
            }
            if (!response.ok) throw new Error('SERVER');
            return response.json();
        })
        .then(data => {
            if (data && data.success) {
                applyState(data.user_helpful_vote === true, data.user_helpful_vote === false, data.helpful_votes, data.not_helpful_votes);
                const actionMsg = data.action === 'added' ? 'Vote recorded' : data.action === 'changed' ? 'Vote updated' : 'Vote removed';
                if (window.showNotification) window.showNotification(actionMsg, 'success');
            } else {
                throw new Error(data.error || 'FAIL');
            }
        })
        .catch(error => {
            console.error('[Vote] Error:', error);
            if (error.message !== 'AUTH') {
                if (window.showNotification) window.showNotification('Update failed. Reverting...', 'error');
                applyState(oldState.h, oldState.nh, oldState.hc, oldState.nhc);
            }
        });
    };

    window.selectVariant = function(variantId) {
        console.log(`[VariantSelection] Attempting to select: ${variantId}`);
        const v = config.variants[variantId];
        
        if (!v) {
            console.error(`[VariantSelection] Error: Variant ${variantId} not found in config.`);
            return;
        }

        // Assertion: Ensure variant has images
        if (!v.images || v.images.length === 0 || !v.images[0]) {
            console.error(`[VariantSelection] Error: Selected variant ${variantId} has NO images. This is a critical failure.`);
            if (window.showNotification) window.showNotification('This variant has no images and cannot be displayed properly.', 'error');
            return;
        }

        console.log(`[VariantSelection] Success: Variant ${variantId} selected. Images:`, v.images);

        // 1. Update selection UI (cards/chips)
        document.querySelectorAll('.variant-item, .variant-chip').forEach(item => {
            item.classList.remove('selected-variant', 'border-emerald-500', 'ring-2', 'ring-emerald-500/20');
            item.classList.add('border-gray-100');
        });
        const selectedChip = document.querySelector(`.variant-chip[data-variant-id="${variantId}"]`);
        if (selectedChip) {
            selectedChip.classList.add('border-emerald-500', 'ring-2', 'ring-emerald-500/20');
            selectedChip.classList.remove('border-gray-100');
        }

        // 2. Update Hidden Input & Dropdown
        const hiddenInput = document.getElementById('selected-variant-id-hidden');
        if (hiddenInput) {
            hiddenInput.value = variantId;
            console.log(`[VariantSelection] Hidden input updated to: ${variantId}`);
        }
        
        const dropdown = document.getElementById('variant-select-dropdown');
        if (dropdown) {
            dropdown.value = variantId;
        }

        // 3. Update Price Display
        const currentPriceEl = document.getElementById('current-price');
        const originalPriceEl = document.getElementById('original-price');
        const discountBadge = document.getElementById('discount-badge');
        
        if (currentPriceEl) {
            currentPriceEl.textContent = `₹${v.discountedPrice.toFixed(2)}`;
            if (v.discount > 0) {
                if (originalPriceEl) {
                    originalPriceEl.textContent = `₹${v.price.toFixed(2)}`;
                    originalPriceEl.classList.remove('hidden');
                }
                if (discountBadge) {
                    discountBadge.textContent = `${v.discount}% OFF`;
                    discountBadge.classList.remove('hidden');
                }
            } else {
                if (originalPriceEl) originalPriceEl.classList.add('hidden');
                if (discountBadge) discountBadge.classList.add('hidden');
            }
        }

        // 4. Update Stock Status
        const stockStatusEl = document.getElementById('main-stock-status');
        if (stockStatusEl) {
            if (v.stock > 0) {
                stockStatusEl.innerHTML = `
                    <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                        <i class="fas fa-check-circle mr-1"></i>
                        ${v.isLowStock ? `Only ${v.stock} left!` : 'In Stock'}
                    </span>
                `;
            } else {
                stockStatusEl.innerHTML = `
                    <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-red-100 text-red-800">
                        <i class="fas fa-times-circle mr-1"></i>
                        Out of Stock
                    </span>
                `;
            }
        }

        // 5. Update Variant Info Text
        const infoEl = document.getElementById('selected-variant-info');
        if (infoEl) {
            const card = document.querySelector(`.variant-item[data-variant-id="${variantId}"]`);
            if (card) {
                const color = card.querySelector('.bg-emerald-100')?.textContent.trim() || '';
                const size = card.querySelector('.bg-teal-100')?.textContent.trim() || '';
                let text = 'Selected: ';
                if (color) text += color;
                if (color && size) text += ' / ';
                if (size) text += size;
                infoEl.textContent = text;
            }
        }

        // 6. Update Button State
        const mainBtn = document.getElementById('main-add-to-cart-btn');
        if (mainBtn) {
            if (v.stock > 0) {
                mainBtn.disabled = false;
                mainBtn.classList.remove('opacity-50', 'cursor-not-allowed');
                
                // Show "In Cart" state if variant is already in cart
                if (v.inCart) {
                    mainBtn.classList.replace('from-emerald-600', 'from-green-600');
                    mainBtn.innerHTML = '<i class="fas fa-check-circle"></i><span>In Cart</span>';
                } else {
                    mainBtn.classList.replace('from-green-600', 'from-emerald-600');
                    mainBtn.innerHTML = '<i class="fas fa-cart-plus"></i><span>Add to Cart</span>';
                }
            } else {
                mainBtn.disabled = true;
                mainBtn.classList.add('opacity-50', 'cursor-not-allowed');
                mainBtn.innerHTML = '<i class="fas fa-times-circle"></i><span>Out of Stock</span>';
            }
        }

        // 7. Update Gallery
        updateGallery(variantId);
    };

    function updateGallery(variantId) {
        console.log(`[Gallery] Updating gallery for variant: ${variantId}`);
        const v = config.variants[variantId];
        if (!v) {
            console.warn(`[Gallery] No config found for variant: ${variantId}`);
            return;
        }
        
        // Filter out any invalid URLs to avoid "undefined" 404 errors
        const images = (v.images || []).filter(url => url && url !== 'undefined');
        const gallery = document.getElementById('thumbnail-gallery');
        const mainImg = document.getElementById('main-product-image');
        
        if (!gallery || !mainImg) return;

        // Clear existing thumbnails
        gallery.innerHTML = '';

        if (images.length > 0) {
            // Preload images for smoother switching - with strict validation
            images.forEach(url => {
                if (!url || url === 'undefined' || url === 'null') {
                    console.warn(`[Gallery] Skipping invalid preload URL: ${url}`);
                    return;
                }
                const link = document.createElement('link');
                link.rel = 'preload';
                link.as = 'image';
                link.href = url;
                document.head.appendChild(link);
            });

            // Update thumbnails - with strict validation
            images.forEach((imgUrl, index) => {
                if (!imgUrl || imgUrl === 'undefined' || imgUrl === 'null') {
                    console.warn(`[Gallery] Skipping invalid thumbnail URL: ${imgUrl}`);
                    return;
                }
                const img = document.createElement('img');
                img.src = imgUrl;
                img.className = `thumb-img ${index === 0 ? 'border-emerald-600' : 'border-gray-200'} border-3 rounded-xl cursor-pointer h-20 w-20 object-cover transition-all hover:shadow-lg hover:scale-105 flex-shrink-0`;
                img.dataset.full = imgUrl;
                img.onclick = function() {
                    window.updateMainImage(imgUrl);
                };
                gallery.appendChild(img);
            });

            // Update main image to first valid image of variant
            const firstValidImage = images.find(url => url && url !== 'undefined' && url !== 'null');
            if (firstValidImage) {
                window.updateMainImage(firstValidImage);
            }
        } else {
            console.warn(`[Gallery] No valid images for variant: ${variantId}`);
        }
    }

    window.updateMainImage = function(url) {
        if (!url || url === 'undefined') {
            console.error('[Gallery] Attempted to update main image with invalid URL:', url);
            return;
        }
        
        const mainImg = document.getElementById('main-product-image');
        if (!mainImg) return;
        
        // Update all thumbnails to show which one is selected
        document.querySelectorAll('.thumb-img').forEach(t => {
            if (t.src === url || t.dataset.full === url) {
                t.classList.add('border-emerald-600', 'opacity-100');
                t.classList.remove('border-gray-200', 'opacity-50');
            } else {
                t.classList.remove('border-emerald-600', 'opacity-100');
                t.classList.add('border-gray-200', 'opacity-50');
            }
        });

        // Smooth fade transition
        mainImg.style.transition = 'opacity 0.2s ease-in-out';
        mainImg.style.opacity = '0';
        
        setTimeout(() => {
            mainImg.src = url;
            // Force opacity back even if onload doesn't fire (cached images)
            setTimeout(() => {
                mainImg.style.opacity = '1';
                console.log(`[Gallery] Main image updated: ${url}`);
            }, 50);
        }, 200);
    };

    // Quantity Management
    window.changeQty = function(delta) {
        const input = document.getElementById('purchase-quantity');
        if (!input) return;
        
        let val = parseInt(input.value) + delta;
        const variantId = document.getElementById('selected-variant-id-hidden').value;
        const v = config.variants[variantId];
        
        const maxStock = v ? Math.min(v.stock, 5) : 5;
        
        if (val < 1) val = 1;
        if (val > maxStock) {
            val = maxStock;
            if (window.showNotification) window.showNotification(`Only ${maxStock} items available`, 'info');
        }
        
        input.value = val;
    };

    window.addSelectedToCart = function() {
        const variantId = document.getElementById('selected-variant-id-hidden').value;
        const quantity = parseInt(document.getElementById('purchase-quantity').value);
        
        if (!variantId) {
            if (window.showNotification) window.showNotification('Please select a variant', 'warning');
            return;
        }

        console.log(`[AddToCart] Adding variant ${variantId} with quantity ${quantity}`);
        if (window.globalAddToCart) {
            window.globalAddToCart(config.productId, variantId, quantity);
        } else {
            // Fallback if globalAddToCart is not available
            window.addToCart(variantId);
        }
    };

    // --- Gallery & Zoom ---
    function initGallery() {
        const mainImg = document.getElementById("main-product-image");
        const imageContainer = document.getElementById('image-container');
        
        if (!mainImg || !imageContainer) return;

        // Auto-select a variant on page load
        const bridgeItems = Array.from(document.querySelectorAll('.variant-item[data-has-images="true"]'));
        
        if (bridgeItems.length > 0) {
            const variantId = bridgeItems[0].dataset.variantId;
            console.log(`[Init] Page load: Auto-selecting variant ${variantId} from bridge.`);
            window.selectVariant(variantId);
        } else {
            console.warn('[Init] No bridge items with images found. Checking visual chips...');
            const firstChip = document.querySelector('.variant-chip:not(.opacity-40)');
            if (firstChip) {
                window.selectVariant(firstChip.dataset.variantId);
            }
        }

        imageContainer.onmouseenter = e => {
            if (window.innerWidth < 1024) return;
            mainImg.style.transition = 'transform 0.2s ease-out';
            mainImg.style.transform = 'scale(2.5)';
        };
        imageContainer.onmousemove = e => {
            if (window.innerWidth < 1024) return;
            const rect = imageContainer.getBoundingClientRect();
            const x = ((e.clientX - rect.left) / rect.width) * 100;
            const y = ((e.clientY - rect.top) / rect.height) * 100;
            mainImg.style.transformOrigin = `${x}% ${y}%`;
        };
        imageContainer.onmouseleave = () => {
            mainImg.style.transform = 'scale(1)';
        };
    }

    // --- Page Initialization ---
    function init() {
        initGallery();
        checkInitialization();
        
        const comment = document.getElementById('review-comment');
        if (comment) {
            comment.oninput = function() {
                document.getElementById('char-count').textContent = this.value.length;
            };
        }
        
        const editComment = document.getElementById('edit-review-comment');
        if (editComment) {
            editComment.oninput = function() {
                document.getElementById('edit-char-count').textContent = this.value.length;
            };
        }

        initStarRating('star-rating-input', 'rating-value', 'rating-label', 'star-rating button');
        initStarRating('edit-star-rating-input', 'edit-rating-value', 'edit-rating-label', 'edit-rating-star');

        const reviewsContainer = document.getElementById('reviews-container');
        if (reviewsContainer) {
            reviewsContainer.addEventListener('click', function(e) {
                const btn = e.target.closest('.review-vote-btn');
                if (btn) {
                    e.preventDefault();
                    window.voteReview(btn.dataset.reviewId, btn.dataset.voteType);
                }
            });
        }

        const loadMoreBtn = document.getElementById('load-more-reviews');
        if (loadMoreBtn) {
            let currentPage = 1;
            loadMoreBtn.onclick = function() {
                currentPage++;
                const url = `${config.ajaxReviewsUrl}?page=${currentPage}`;
                fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        window.location.reload(); 
                    }
                });
            };
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();

// Separate function for delete confirmation as used in onclick
window.confirmDeleteReview = function(form) {
    if (!window.showConfirmModal) {
        if (confirm('Are you sure you want to delete your review?')) {
            form.submit();
        }
        return;
    }

    window.showConfirmModal({
        title: 'Delete Review?',
        message: 'Are you sure you want to delete your review? This action cannot be undone.',
        confirmText: 'Delete',
        cancelText: 'Cancel',
        variant: 'danger',
        onConfirm: () => {
            form.submit();
        }
    });
};
