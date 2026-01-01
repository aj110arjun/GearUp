/**
 * Shopping Cart logic for GearUp.
 */

(function() {
    const config = window.CART_CONFIG || {};

    document.addEventListener('DOMContentLoaded', function() {
        console.log('Cart initialized...');
        
        // Function to show content and hide skeleton
        function showContent() {
            const skeleton = document.getElementById('cart-skeleton');
            const content = document.getElementById('cart-content');
            
            if (skeleton) {
                skeleton.style.opacity = '0';
                skeleton.style.transition = 'opacity 0.3s ease';
                setTimeout(() => {
                    skeleton.style.display = 'none';
                }, 300);
            }
            
            if (content) {
                content.style.display = 'block';
                content.style.opacity = '0';
                setTimeout(() => {
                    content.style.transition = 'opacity 0.5s ease-in-out';
                    content.style.opacity = '1';
                }, 50);
            }
        }
        
        // Always show content after a short delay
        setTimeout(showContent, 800);
        
        window.addEventListener('load', function() {
            const content = document.getElementById('cart-content');
            if (content && content.style.display === 'none') {
                showContent();
            }
        });

        // Initialize button states
        document.querySelectorAll('.cart-item').forEach(item => {
            const itemId = item.dataset.itemId;
            const qtyText = item.querySelector('.quantity-text');
            if (qtyText) {
                updateButtonStates(itemId, parseInt(qtyText.textContent));
            }
        });

        // Event listeners
        document.querySelectorAll('.increment-btn').forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                incrementQuantity(this.dataset.itemId);
            });
        });
        
        document.querySelectorAll('.decrement-btn').forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                decrementQuantity(this.dataset.itemId);
            });
        });
        
        const moveAllBtn = document.getElementById('move-all-to-wishlist-btn');
        if (moveAllBtn) {
            moveAllBtn.addEventListener('click', moveAllToWishlist);
        }
        
        const checkoutBtn = document.getElementById('checkout-btn');
        if (checkoutBtn) {
            checkoutBtn.addEventListener('click', proceedToCheckout);
        }
    });

    function updateButtonStates(itemId, quantity) {
        const itemEl = document.querySelector(`.cart-item[data-item-id="${itemId}"]`);
        if (!itemEl) return;
        
        const decBtn = itemEl.querySelector('.decrement-btn');
        const incBtn = itemEl.querySelector('.increment-btn');
        const maxQty = parseInt(itemEl.dataset.maxQty || 5);

        if (decBtn) {
            decBtn.disabled = quantity <= 1;
        }

        if (incBtn) {
            incBtn.disabled = quantity >= maxQty;
        }
    }

    function updateOrderSummary(data) {
        const ids = {
            'subtotal-display': data.subtotal,
            'shipping-display': data.shipping_cost,
            'cart-total': data.final_total,
            'discount-display': data.total_discount
        };
        
        for (const [id, value] of Object.entries(ids)) {
            const el = document.getElementById(id);
            if (el && value !== undefined) {
                let prefix = '₹';
                if (id === 'discount-display') prefix = '-₹';
                
                let val = parseFloat(value);
                if (!isNaN(val)) {
                    el.textContent = prefix + val.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
                } else {
                    el.textContent = value;
                }
            }
        }
    }

    function incrementQuantity(itemId) {
        const itemEl = document.querySelector(`.cart-item[data-item-id="${itemId}"]`);
        if (!itemEl) return;
        
        const qtyText = document.getElementById(`quantity-${itemId}`);
        if (!qtyText) return;
        
        const currentQty = parseInt(qtyText.textContent);
        const maxQty = parseInt(itemEl.dataset.maxQty || 5);
        
        if (currentQty >= maxQty) {
            if (window.showNotification) {
                window.showNotification(`Maximum quantity (${maxQty}) reached`, 'warning');
            }
            return;
        }
        
        updateCartItem(itemId, currentQty + 1);
    }

    function decrementQuantity(itemId) {
        const qtyText = document.getElementById(`quantity-${itemId}`);
        if (!qtyText) return;
        
        const currentQty = parseInt(qtyText.textContent);
        if (currentQty <= 1) return;
        
        updateCartItem(itemId, currentQty - 1);
    }

    function updateCartItem(itemId, quantity) {
        const itemEl = document.querySelector(`.cart-item[data-item-id="${itemId}"]`);
        const qtyText = document.getElementById(`quantity-${itemId}`);
        const itemTotal = itemEl?.querySelector('.item-total');
        
        if (!qtyText || !itemEl) return;
        
        qtyText.classList.add('updating');
        itemEl.style.pointerEvents = 'none';

        window.globalApiPOST(config.updateUrl, {
            item_id: itemId,
            quantity: quantity
        })
        .then(data => {
            if (data.success) {
                qtyText.textContent = data.item_quantity || quantity;
                
                if (itemTotal && data.item_total) {
                    itemTotal.textContent = `₹${parseFloat(data.item_total).toFixed(2)}`;
                }
                
                updateButtonStates(itemId, data.item_quantity || quantity);
                updateOrderSummary(data);
                
                if (window.showNotification) {
                    window.showNotification(data.message || 'Cart updated', 'success');
                }
            } else {
                if (window.showNotification) {
                    window.showNotification(data.message || 'Error updating cart', 'error');
                }
            }
        })
        .catch(e => {
            console.error('Cart update error:', e);
            if (window.showNotification) {
                window.showNotification('Connection error', 'error');
            }
        })
        .finally(() => {
            qtyText.classList.remove('updating');
            itemEl.style.pointerEvents = 'auto';
        });
    }

    window.toggleVariantSelector = function(itemId) {
        const selector = document.getElementById(`variant-selector-${itemId}`);
        if (selector) {
            selector.classList.toggle('hidden');
            if (!selector.classList.contains('hidden')) {
                selector.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }
        }
    };

    window.updateVariant = function(itemId, variantId) {
        const itemEl = document.getElementById(`cart-item-${itemId}`);
        if (itemEl) {
            itemEl.style.opacity = '0.7';
            itemEl.style.pointerEvents = 'none';
        }

        window.globalApiPOST(config.updateVariantUrl, {
            item_id: itemId,
            variant_id: variantId
        })
        .then(data => {
            if (data.success) {
                if (window.showNotification) {
                    window.showNotification(data.message, 'success');
                }
                setTimeout(() => location.reload(), 300);
            } else {
                if (window.showNotification) {
                    window.showNotification(data.message || 'Error updating variant', 'error');
                }
                if (itemEl) {
                    itemEl.style.opacity = '1';
                    itemEl.style.pointerEvents = 'auto';
                }
            }
        })
        .catch(e => {
            console.error('Variant update error:', e);
            if (itemEl) {
                itemEl.style.opacity = '1';
                itemEl.style.pointerEvents = 'auto';
            }
        });
    };

    function moveAllToWishlist() {
        if (!window.showConfirmModal) {
            if (confirm('Move all items from your cart to your wishlist?')) {
                performMoveAllToWishlist();
            }
            return;
        }

        window.showConfirmModal({
            title: 'Move All to Wishlist?',
            message: 'Move all items from your cart to your wishlist?',
            confirmText: 'Move All',
            cancelText: 'Cancel',
            variant: 'success',
            onConfirm: performMoveAllToWishlist
        });
    }

    function performMoveAllToWishlist() {
        const container = document.getElementById('cart-items-container');
        if (container) {
            container.style.opacity = '0.5';
            container.style.pointerEvents = 'none';
        }
        
        window.globalApiPOST(config.moveAllToWishlistUrl)
        .then(data => {
            if (data.success) {
                if (window.showNotification) {
                    window.showNotification(data.message, 'success');
                }
                if (container) {
                    container.style.transition = 'all 0.5s ease';
                    container.style.transform = 'translateX(100%)';
                    container.style.opacity = '0';
                }
                setTimeout(() => location.reload(), 500);
            } else {
                if (window.showNotification) {
                    window.showNotification(data.message || 'Error moving items', 'error');
                }
                if (container) {
                    container.style.opacity = '1';
                    container.style.pointerEvents = 'auto';
                }
            }
        })
        .catch(e => {
            console.error('Move all error:', e);
            if (container) {
                container.style.opacity = '1';
                container.style.pointerEvents = 'auto';
            }
        });
    }

    function proceedToCheckout() {
        const outOfStockItems = document.querySelectorAll('.cart-item:has(.out-of-stock-label)');
        if (outOfStockItems.length > 0) {
            if (window.showNotification) {
                window.showNotification('Please remove out-of-stock items before checkout', 'error');
            }
            return;
        }
        
        const cartItems = document.querySelectorAll('.cart-item');
        if (cartItems.length === 0) {
            if (window.showNotification) {
                window.showNotification('Your cart is empty', 'error');
            }
            return;
        }
        
        window.location.href = config.checkoutUrl;
    }

    // Export functions to window for onclick handlers
    window.incrementQuantity = incrementQuantity;
    window.decrementQuantity = decrementQuantity;
    window.moveAllToWishlist = moveAllToWishlist;
    window.proceedToCheckout = proceedToCheckout;
})();
