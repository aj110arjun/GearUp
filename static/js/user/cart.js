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

        // Variant Selection Event Listeners
        document.querySelectorAll('.change-variant-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                toggleVariantSelector(this.dataset.itemId);
            });
        });

        document.querySelectorAll('.close-variant-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                toggleVariantSelector(this.dataset.itemId);
            });
        });

        document.querySelectorAll('.variant-option-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                updateVariant(this.dataset.itemId, this.dataset.variantId);
            });
        });
    });

    function updateButtonStates(itemId, quantity) {
        // Disabling logic removed as per user request.
        // Buttons remain enabled at all times.
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
        const itemEl = document.getElementById(`cart-item-${itemId}`) || 
                       document.querySelector(`.cart-item[data-item-id="${itemId}"]`);
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
        
        // Store current quantity for potential rollback
        itemEl.dataset.originalQty = currentQty;
        updateCartItem(itemId, currentQty + 1);
    }

    function decrementQuantity(itemId) {
        const itemEl = document.getElementById(`cart-item-${itemId}`) || 
                       document.querySelector(`.cart-item[data-item-id="${itemId}"]`);
        if (!itemEl) return;

        const qtyText = document.getElementById(`quantity-${itemId}`);
        if (!qtyText) return;
        
        const currentQty = parseInt(qtyText.textContent);
        
        if (currentQty <= 1) {
            // If decreasing from 1, ask to remove the item
            if (window.showConfirmModal) {
                window.showConfirmModal({
                    title: 'Remove Item?',
                    message: 'Do you want to remove this item from your cart?',
                    confirmText: 'Remove',
                    cancelText: 'Cancel',
                    onConfirm: () => {
                        itemEl.dataset.originalQty = currentQty;
                        updateCartItem(itemId, 0); // Backend deletes if quantity <= 0
                        // Since it's being removed, we should reload or hide the element
                        setTimeout(() => location.reload(), 500);
                    }
                });
            } else if (confirm('Remove item from cart?')) {
                itemEl.dataset.originalQty = currentQty;
                updateCartItem(itemId, 0);
                setTimeout(() => location.reload(), 500);
            }
            return;
        }
        
        // Store current quantity for potential rollback
        itemEl.dataset.originalQty = currentQty;
        updateCartItem(itemId, currentQty - 1);
    }

    function updateCartItem(itemId, quantity) {
        const itemEl = document.getElementById(`cart-item-${itemId}`) || 
                       document.querySelector(`.cart-item[data-item-id="${itemId}"]`);
        const qtyText = document.getElementById(`quantity-${itemId}`);
        const itemTotal = document.getElementById(`item-total-${itemId}`);
        
        if (!qtyText || !itemEl) return;

        const originalQty = parseInt(itemEl.dataset.originalQty || qtyText.textContent);
        const unitPrice = parseFloat(itemEl.dataset.unitPrice || 0);

        // --- OPTIMISTIC UPDATE START ---
        // Update quantity text immediately
        qtyText.textContent = quantity;
        qtyText.classList.add('updating', 'scale-110');
        
        // Update item total immediately (client-side calc)
        if (itemTotal) {
            const tempTotal = unitPrice * quantity;
            itemTotal.textContent = `₹${tempTotal.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
            itemTotal.classList.add('text-emerald-500', 'scale-105', 'transition-all');
        }

        // Update button states immediately
        updateButtonStates(itemId, quantity);
        
        // Disable interactions during bounce
        itemEl.style.pointerEvents = 'none';
        // --- OPTIMISTIC UPDATE END ---

        window.globalApiPOST(config.updateUrl, {
            item_id: itemId,
            quantity: quantity
        })
        .then(data => {
            if (data.success) {
                // Confirm with server data
                const finalQty = data.item_quantity !== undefined ? data.item_quantity : quantity;
                qtyText.textContent = finalQty;
                
                if (itemTotal) {
                    const finalTotal = data.item_total !== undefined ? 
                                 parseFloat(data.item_total) : 
                                 (unitPrice * finalQty);
                    itemTotal.textContent = `₹${finalTotal.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
                }
                
                // Update button states again to be sure
                updateButtonStates(itemId, finalQty);
                // Update summary with real server data
                updateOrderSummary(data);
                
                // Success visual splash
                qtyText.classList.replace('updating', 'success-update');
                setTimeout(() => {
                    qtyText.classList.remove('success-update', 'scale-110');
                    if (itemTotal) itemTotal.classList.remove('text-emerald-500', 'scale-105');
                }, 400);

                if (window.showNotification) {
                    window.showNotification(data.message || 'Cart updated', 'success');
                }
            } else {
                // ROLLBACK on backend error
                if (window.showNotification) {
                    window.showNotification(data.message || 'Error updating cart', 'error');
                }
                rollbackUI(itemId, originalQty, unitPrice);
            }
        })
        .catch(e => {
            console.error('Cart update error:', e);
            if (window.showNotification) {
                window.showNotification('Connection error', 'error');
            }
            // ROLLBACK on connection error
            rollbackUI(itemId, originalQty, unitPrice);
        })
        .finally(() => {
            setTimeout(() => {
                qtyText.classList.remove('updating', 'scale-110');
                itemEl.style.pointerEvents = 'auto';
            }, 300);
        });
    }

    function rollbackUI(itemId, originalQty, unitPrice) {
        const qtyText = document.getElementById(`quantity-${itemId}`);
        const itemTotal = document.getElementById(`item-total-${itemId}`);
        
        if (qtyText) {
            qtyText.textContent = originalQty;
            qtyText.classList.add('bg-red-50', 'text-red-600');
            setTimeout(() => qtyText.classList.remove('bg-red-50', 'text-red-600'), 1000);
        }
        
        if (itemTotal) {
            const total = unitPrice * originalQty;
            itemTotal.textContent = `₹${total.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        }
        
        updateButtonStates(itemId, originalQty);
    }

    function toggleVariantSelector(itemId) {
        console.log('Toggling variant selector for item:', itemId);
        const selector = document.getElementById(`variant-selector-${itemId}`);
        if (selector) {
            selector.classList.toggle('hidden');
            if (!selector.classList.contains('hidden')) {
                selector.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }
        } else {
            console.error('Variant selector not found for itemId:', itemId);
        }
    }

    function updateVariant(itemId, variantId) {
        console.log(`Updating variant for item ${itemId} to variant ${variantId}`);
        const itemEl = document.getElementById(`cart-item-${itemId}`);
        if (itemEl) {
            itemEl.classList.add('opacity-50', 'pointer-events-none');
            const selector = document.getElementById(`variant-selector-${itemId}`);
            if (selector) selector.classList.add('hidden');
        }

        window.globalApiPOST(config.updateVariantUrl, {
            item_id: itemId,
            variant_id: variantId
        })
        .then(data => {
            console.log('Variant update response:', data);
            if (data.success) {
                if (window.showNotification) {
                    window.showNotification(data.message, 'success');
                }
                
                if (data.merged) {
                    console.log('Item merged, removing old element');
                    // Item merged into another one
                    if (itemEl) {
                        itemEl.style.transition = 'all 0.4s ease';
                        itemEl.style.transform = 'scale(0.9)';
                        itemEl.style.opacity = '0';
                        setTimeout(() => itemEl.remove(), 400);
                    }
                    setTimeout(() => location.reload(), 500);
                } else {
                    console.log('Simple update, reloading page');
                    setTimeout(() => location.reload(), 300);
                }
            } else {
                if (window.showNotification) {
                    window.showNotification(data.message || 'Error updating variant', 'error');
                }
                if (itemEl) {
                    itemEl.classList.remove('opacity-50', 'pointer-events-none');
                }
            }
        })
        .catch(e => {
            console.error('Variant update error:', e);
            if (itemEl) {
                itemEl.classList.remove('opacity-50', 'pointer-events-none');
            }
        });
    }

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

    // Export functions to window for onclick handlers (though we use event listeners now)
    window.incrementQuantity = incrementQuantity;
    window.decrementQuantity = decrementQuantity;
    window.moveAllToWishlist = moveAllToWishlist;
    window.proceedToCheckout = proceedToCheckout;
    window.toggleVariantSelector = toggleVariantSelector;
    window.updateVariant = updateVariant;
})();
