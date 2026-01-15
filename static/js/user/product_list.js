/**
 * Product List logic for GearUp.
 */

(function() {
    function showContent() {
        const skeletons = document.getElementById('product-skeletons');
        const grid = document.getElementById('product-grid');
        
        if (skeletons) {
            skeletons.style.opacity = '0';
            skeletons.style.transition = 'opacity 0.3s ease';
            setTimeout(() => {
                skeletons.style.display = 'none';
            }, 300);
        }
        
        if (grid) {
            grid.style.display = 'block';
            grid.style.opacity = '0';
            setTimeout(() => {
                grid.style.transition = 'opacity 0.5s ease-in-out';
                grid.style.opacity = '1';
            }, 50);
        }
    }
  
    function initSearch() {
        const input = document.getElementById('search-input');
        const clearBtn = document.getElementById('clear-btn');
        if (!input || !clearBtn) return;
        
        const toggleClearBtn = () => clearBtn.classList.toggle('hidden', !input.value);
        input.addEventListener('input', toggleClearBtn);
        clearBtn.addEventListener('click', function() {
            input.value = '';
            toggleClearBtn();
            const form = input.closest('form');
            if (form) form.submit();
        });
        toggleClearBtn();
    }
  
    function initActionButtons() {
        // Wishlist buttons
        document.querySelectorAll('.wishlist-btn').forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                const productId = this.dataset.productId;
                if (window.globalToggleWishlist) window.globalToggleWishlist(productId);
            });
        });
        
        // Cart buttons
        document.querySelectorAll('.cart-btn').forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                const productId = this.dataset.productId;
                const variantId = this.dataset.variantId;
                if (window.globalAddToCart) window.globalAddToCart(productId, variantId);
            });
        });
    }
  
    function init() {
        initSearch();
        initActionButtons();
        setTimeout(showContent, 600);
    }
  
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
