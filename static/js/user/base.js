/**
 * Core UI logic for the GearUp user portal.
 */

// Snackbar Notification System
window.showNotification = function(message, type = 'success') {
    const container = document.getElementById('snackbar-container');
    if (!container) return;

    const snackbar = document.createElement('div');
    
    const bgClass = type === 'success' ? 'bg-emerald-600' : 
                    type === 'error' ? 'bg-red-600' : 
                    type === 'warning' ? 'bg-amber-500' : 'bg-blue-600';
    
    const iconClass = type === 'success' ? 'fa-check-circle' : 
                      type === 'error' ? 'fa-exclamation-circle' : 
                      type === 'warning' ? 'fa-exclamation-triangle' : 'fa-info-circle';

    snackbar.className = `pointer-events-auto flex items-center gap-3 ${bgClass} text-white px-6 py-4 rounded-xl shadow-2xl transform transition-all duration-300 translate-x-full opacity-0 max-w-md`;
    snackbar.innerHTML = `
        <i class="fas ${iconClass} text-xl"></i>
        <p class="font-medium">${message}</p>
        <button class="ml-auto hover:text-white/80 transition-colors">
            <i class="fas fa-times"></i>
        </button>
    `;

    container.appendChild(snackbar);
    setTimeout(() => snackbar.classList.remove('translate-x-full', 'opacity-0'), 10);
    const removeTimeout = setTimeout(() => removeSnackbar(snackbar), 5000);
    snackbar.querySelector('button').onclick = () => {
        clearTimeout(removeTimeout);
        removeSnackbar(snackbar);
    };
};

function removeSnackbar(snackbar) {
    snackbar.classList.add('translate-x-full', 'opacity-0');
    setTimeout(() => snackbar.remove(), 300);
}

// Global Confirmation Modal System
window.showConfirmModal = function(options = {}) {
    const {
        title = 'Are you sure?',
        message = 'This action cannot be undone.',
        confirmText = 'Confirm',
        cancelText = 'Cancel',
        variant = 'danger',
        onConfirm = () => {},
        onCancel = () => {}
    } = options;

    const modal = document.getElementById('global-confirm-modal');
    if (!modal) return;

    const backdrop = document.getElementById('global-confirm-backdrop');
    const content = document.getElementById('global-confirm-content');
    const titleEl = document.getElementById('global-confirm-title');
    const messageEl = document.getElementById('global-confirm-message');
    const confirmBtn = document.getElementById('global-confirm-btn');
    const cancelBtn = document.getElementById('global-cancel-btn');
    const iconEl = document.getElementById('global-confirm-icon');
    const iconBg = document.getElementById('global-confirm-icon-bg');

    titleEl.textContent = title;
    messageEl.textContent = message;
    confirmBtn.textContent = confirmText;
    cancelBtn.textContent = cancelText;

    if (variant === 'danger') {
        if (iconBg) iconBg.className = 'flex items-center justify-center w-16 h-16 rounded-full bg-red-50 mb-6';
        if (iconEl) iconEl.className = 'fas fa-exclamation-triangle text-2xl text-red-600';
        if (confirmBtn) confirmBtn.className = 'w-full inline-flex justify-center items-center rounded-xl border border-transparent shadow-sm px-5 py-3 bg-red-600 text-base font-semibold text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 transition-colors sm:w-1/2';
    } else if (variant === 'success') {
        if (iconBg) iconBg.className = 'flex items-center justify-center w-16 h-16 rounded-full bg-emerald-50 mb-6';
        if (iconEl) iconEl.className = 'fas fa-check-circle text-2xl text-emerald-600';
        if (confirmBtn) confirmBtn.className = 'w-full inline-flex justify-center items-center rounded-xl border border-transparent shadow-sm px-5 py-3 bg-emerald-600 text-base font-semibold text-white hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-emerald-500 transition-colors sm:w-1/2';
    }

    modal.classList.remove('hidden');
    requestAnimationFrame(() => {
        backdrop.classList.remove('opacity-0');
        content.classList.remove('scale-95', 'opacity-0');
    });

    const closeModal = () => {
        backdrop.classList.add('opacity-0');
        content.classList.add('scale-95', 'opacity-0');
        setTimeout(() => modal.classList.add('hidden'), 200);
    };

    confirmBtn.onclick = () => { closeModal(); onConfirm(); };
    cancelBtn.onclick = () => { closeModal(); onCancel(); };
    backdrop.onclick = closeModal;
};

// Navbar Updates
window.updateCartCount = function(count) {
    const badge = document.getElementById('cart-badge');
    if (badge) {
        badge.textContent = count;
        badge.classList.toggle('hidden', count <= 0);
    }
};

window.updateWishlistCount = function(count) {
    const badge = document.getElementById('wishlist-badge');
    if (badge) {
        badge.textContent = count;
        badge.classList.toggle('hidden', count <= 0);
    }
};

// --- CORE PRODUCT ACTIONS ---
window.syncProductUI = function(productId, state, variantId = null) {
    if (state.inWishlist !== undefined) {
        document.querySelectorAll(`.wishlist-btn[data-product-id="${productId}"]`).forEach(btn => {
            const icon = btn.querySelector('i');
            if (state.inWishlist) {
                icon?.classList.replace('far', 'fas');
                icon?.classList.add('text-red-500');
                btn.classList.add('border-red-300', 'bg-red-50');
            } else {
                icon?.classList.replace('fas', 'far');
                icon?.classList.remove('text-red-500');
                btn.classList.remove('border-red-300', 'bg-red-50');
            }
        });
    }

    if (state.inCart !== undefined) {
        let selector = `.cart-btn[data-product-id="${productId}"]`;
        if (variantId) {
            selector += `[data-variant-id="${variantId}"]`;
        }
        
        document.querySelectorAll(selector).forEach(btn => {
            if (state.inCart) {
                btn.classList.replace('bg-emerald-600', 'bg-green-600');
                btn.innerHTML = '<i class="fas fa-check-circle"></i> In Cart';
            } else {
                btn.classList.replace('bg-green-600', 'bg-emerald-600');
                btn.innerHTML = '<i class="fas fa-shopping-cart"></i> Add to Cart';
            }
        });
    }
};

window.globalToggleWishlist = async function(productId) {
    const btn = document.querySelector(`.wishlist-btn[data-product-id="${productId}"]`);
    if (btn) btn.disabled = true;

    try {
        const data = await window.globalApiPOST(window.GEAR_UP_CONFIG.toggleWishlistUrl, { product_id: productId });
        if (data.success) {
            let uiState = { inWishlist: data.status === 'added' };
            if (data.in_cart !== undefined) uiState.inCart = data.in_cart;
            window.syncProductUI(productId, uiState);
            if (data.wishlist_count !== undefined) window.updateWishlistCount(data.wishlist_count);
            if (data.cart_count !== undefined) window.updateCartCount(data.cart_count);
            window.showNotification(data.message, 'success');
            if (document.getElementById('product-grid-container')) {
                setTimeout(() => {
                    window.location.reload();
                }, 500);
            }
        } else {
            window.showNotification(data.message, 'error');
        }
    } catch (e) {
        window.showNotification('Connection error', 'error');
    } finally {
        if (btn) btn.disabled = false;
    }
};

window.globalAddToCart = async function(productId, variantId) {
    const btn = document.querySelector(`.cart-btn[data-variant-id="${variantId}"]`);
    const originalContent = btn?.innerHTML;
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    }

    try {
        const data = await window.globalApiPOST(window.GEAR_UP_CONFIG.addToCartUrl, { 
            product_id: productId, 
            variant_id: variantId, 
            quantity: 1 
        });
        if (data.success) {
            let uiState = { inCart: data.added };
            if (data.in_wishlist !== undefined) uiState.inWishlist = data.in_wishlist;
            window.syncProductUI(productId, uiState, variantId);
            if (data.cart_count !== undefined) window.updateCartCount(data.cart_count);
            if (data.wishlist_count !== undefined) window.updateWishlistCount(data.wishlist_count);
            window.showNotification(data.message, 'success');
            if (document.getElementById('product-grid-container')) {
                setTimeout(() => {
                    window.location.reload();
                }, 500);
            }
        } else {
            window.showNotification(data.message, 'error');
            if (btn) btn.innerHTML = originalContent;
        }
    } catch (e) {
        window.showNotification('Connection error', 'error');
        if (btn) btn.innerHTML = originalContent;
    } finally {
        if (btn) btn.disabled = false;
    }
};

window.globalRemoveFromWishlist = async function(itemId, element) {
    window.showConfirmModal({
        title: 'Remove from Wishlist?',
        message: 'Are you sure you want to remove this item?',
        onConfirm: async () => {
            if (element) element.style.opacity = '0.5';
            const url = window.GEAR_UP_CONFIG.removeWishlistUrl.replace('00000000-0000-0000-0000-000000000000', itemId);
            const data = await window.globalApiPOST(url);
            if (data.success) {
                if (element) {
                    element.style.transition = 'all 0.3s';
                    element.style.opacity = '0';
                    setTimeout(() => {
                        element.remove();
                        if (data.wishlist_count === 0) location.reload();
                    }, 300);
                } else location.reload();
                window.updateWishlistCount(data.wishlist_count);
                window.showNotification(data.message, 'success');
            } else {
                window.showNotification(data.message, 'error');
                if (element) element.style.opacity = '1';
            }
        }
    });
};

window.globalMoveToCart = async function(itemId, element, variantId = null) {
    if (element) element.style.opacity = '0.5';
    const url = window.GEAR_UP_CONFIG.moveToCartUrl.replace('00000000-0000-0000-0000-000000000000', itemId);
    const body = variantId ? { variant_id: variantId } : {};
    const data = await window.globalApiPOST(url, body);
    if (data.success) {
        if (element) {
            element.style.transition = 'all 0.3s';
            element.style.opacity = '0';
            setTimeout(() => {
                element.remove();
                if (data.wishlist_count === 0) location.reload();
            }, 300);
        } else location.reload();
        window.updateCartCount(data.cart_count);
        window.updateWishlistCount(data.wishlist_count);
        window.showNotification(data.message, 'success');
    } else {
        window.showNotification(data.message, 'error');
        if (element) element.style.opacity = '1';
    }
};

window.globalClearWishlist = async function() {
    window.showConfirmModal({
        title: 'Clear Wishlist?',
        message: 'Are you sure you want to remove ALL items from your wishlist?',
        confirmText: 'Clear All',
        onConfirm: async () => {
            const data = await window.globalApiPOST(window.GEAR_UP_CONFIG.clearWishlistUrl);
            if (data.success) {
                window.updateWishlistCount(0);
                location.reload();
            }
        }
    });
};

window.globalMoveAllToCart = async function() {
    window.showConfirmModal({
        title: 'Move All to Cart?',
        message: 'Move all available items from your wishlist to your cart?',
        variant: 'success',
        onConfirm: async () => {
            const data = await window.globalApiPOST(window.GEAR_UP_CONFIG.moveAllToCartUrl);
            if (data.success) {
                location.reload();
            }
        }
    });
};

// DOM ready basic handlers
document.addEventListener('DOMContentLoaded', () => {
    // Mobile Menu Toggle
    const menuBtn = document.getElementById("menu-btn");
    const mobileMenu = document.getElementById("mobile-menu");
    if (menuBtn && mobileMenu) {
        menuBtn.onclick = () => mobileMenu.classList.toggle("hidden");
    }
});
