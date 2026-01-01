/**
 * Wishlist logic for GearUp.
 */

(function() {
    let currentWishlistItemId = null;

    document.addEventListener('DOMContentLoaded', () => {
        // Reveal content
        const skeleton = document.getElementById('skeleton-loader');
        const main = document.getElementById('main-content');
        if (skeleton) skeleton.style.display = 'none';
        if (main) {
            main.style.display = 'block';
        }

        // Bulk actions
        document.getElementById('clearAllBtn')?.addEventListener('click', () => {
            if (window.globalClearWishlist) window.globalClearWishlist();
        });

        document.getElementById('addAllToCartBtn')?.addEventListener('click', () => {
            if (window.globalMoveAllToCart) window.globalMoveAllToCart();
        });

        // Initialize variant confirm btn
        document.getElementById('confirm-variant-btn')?.addEventListener('click', () => {
            const selected = document.querySelector('input[name="variant-choice"]:checked');
            if (!selected) {
                if (window.showNotification) window.showNotification('Please select an option', 'warning');
                return;
            }
            const element = document.querySelector(`.wishlist-item[data-item-id="${currentWishlistItemId}"]`);
            if (window.globalMoveToCart) window.globalMoveToCart(currentWishlistItemId, element, selected.value);
            closeVariantModal();
        });
    });

    window.removeFromWishlist = function(itemId) {
        const element = document.querySelector(`.wishlist-item[data-item-id="${itemId}"]`);
        if (window.globalRemoveFromWishlist) window.globalRemoveFromWishlist(itemId, element);
    };

    window.moveToCart = function(itemId) {
        const element = document.querySelector(`.wishlist-item[data-item-id="${itemId}"]`);
        if (window.globalMoveToCart) window.globalMoveToCart(itemId, element);
    };

    window.openVariantSelection = function(itemId) {
        const dataContainer = document.getElementById(`variants-data-${itemId}`);
        if (!dataContainer) return;
        
        const variants = Array.from(dataContainer.querySelectorAll('.variant-option')).map(el => el.dataset);
        
        if (variants.length === 1) {
            const element = document.querySelector(`.wishlist-item[data-item-id="${itemId}"]`);
            if (window.globalMoveToCart) window.globalMoveToCart(itemId, element, variants[0].id);
            return;
        }
        
        if (variants.length === 0) {
            if (window.showNotification) window.showNotification('No available variants in stock', 'error');
            return;
        }
        
        currentWishlistItemId = itemId;
        const container = document.getElementById('variant-options-container');
        container.innerHTML = '';
        
        variants.forEach((v) => {
            const div = document.createElement('div');
            div.className = 'flex items-center p-3 border border-gray-200 rounded-lg cursor-pointer hover:bg-emerald-50 transition-colors';
            div.onclick = function() {
                const radio = this.querySelector('input[type="radio"]');
                radio.checked = true;
                document.querySelectorAll('#variant-options-container > div').forEach(d => d.classList.remove('border-emerald-500', 'bg-emerald-50'));
                this.classList.add('border-emerald-500', 'bg-emerald-50');
            };
            
            div.innerHTML = `
                <input type="radio" name="variant-choice" value="${v.id}" id="v-${v.id}" class="h-4 w-4 border-gray-300 text-emerald-600 focus:ring-emerald-600 cursor-pointer">
                <label for="v-${v.id}" class="ml-3 block text-sm font-medium text-gray-900 cursor-pointer w-full flex justify-between">
                    <span>${v.name}</span>
                    <span class="font-bold text-emerald-600">₹${parseFloat(v.price).toLocaleString('en-IN', {minimumFractionDigits: 2})}</span>
                </label>
            `;
            container.appendChild(div);
        });
        
        // Show modal
        const modal = document.getElementById('variant-modal');
        if (modal) {
            modal.classList.remove('hidden');
            const inner = modal.querySelector('.bg-white.relative') || modal.querySelector('[role="dialog"] > div > div');
            if (inner) {
                setTimeout(() => {
                    inner.classList.remove('opacity-0', 'scale-95');
                    inner.classList.add('opacity-100', 'scale-100');
                }, 10);
            }
        }
    };

    window.closeVariantModal = function() {
        const modal = document.getElementById('variant-modal');
        if (!modal) return;
        const inner = modal.querySelector('.bg-white.relative') || modal.querySelector('[role="dialog"] > div > div');
        if (inner) {
            inner.classList.remove('opacity-100', 'scale-100');
            inner.classList.add('opacity-0', 'scale-95');
        }
        setTimeout(() => {
            modal.classList.add('hidden');
            currentWishlistItemId = null;
        }, 200);
    };
})();
