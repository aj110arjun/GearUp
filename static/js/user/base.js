// Mobile Menu Toggle
const menuBtn = document.getElementById("menu-btn");
const mobileMenu = document.getElementById("mobile-menu");

if (menuBtn && mobileMenu) {
  menuBtn.addEventListener("click", () => {
    mobileMenu.classList.toggle("hidden");
  });
}

// Snackbar Notification System
function showNotification(message, type = 'success') {
  const container = document.getElementById('snackbar-container');
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

  // Slide in
  setTimeout(() => {
    snackbar.classList.remove('translate-x-full', 'opacity-0');
  }, 10);

  // Auto remove
  const removeTimeout = setTimeout(() => {
    removeSnackbar(snackbar);
  }, 5000);

  // Manual close
  snackbar.querySelector('button').onclick = () => {
    clearTimeout(removeTimeout);
    removeSnackbar(snackbar);
  };
}

function removeSnackbar(snackbar) {
  snackbar.classList.add('translate-x-full', 'opacity-0');
  setTimeout(() => {
    snackbar.remove();
  }, 300);
}

// Initialize Django messages on page load
document.addEventListener('DOMContentLoaded', () => {
  // Django messages will be handled by the template
  // This is a placeholder for any additional initialization
});
// Global Confirmation Modal System
window.showConfirmModal = function(options = {}) {
    const {
        title = 'Are you sure?',
        message = 'This action cannot be undone.',
        confirmText = 'Confirm',
        cancelText = 'Cancel',
        variant = 'danger', // 'danger' | 'info' | 'success'
        onConfirm = () => {},
        onCancel = () => {}
    } = options;

    // Debugging
    console.log('showConfirmModal called', options);

    const modal = document.getElementById('global-confirm-modal');
    if (!modal) {
        console.error('Global confirm modal element not found!');
        return;
    }

    const backdrop = document.getElementById('global-confirm-backdrop');
    const content = document.getElementById('global-confirm-content');
    const titleEl = document.getElementById('global-confirm-title');
    const messageEl = document.getElementById('global-confirm-message');
    const confirmBtn = document.getElementById('global-confirm-btn');
    const cancelBtn = document.getElementById('global-cancel-btn');
    const iconEl = document.getElementById('global-confirm-icon');
    const iconBg = document.getElementById('global-confirm-icon-bg');

    // Set Content
    titleEl.textContent = title;
    messageEl.textContent = message;
    confirmBtn.textContent = confirmText;
    cancelBtn.textContent = cancelText;

    // Apply Styling based on variant
    if (variant === 'danger') {
        iconBg.className = 'flex items-center justify-center w-16 h-16 rounded-full bg-red-50 mb-6';
        iconEl.className = 'fas fa-exclamation-triangle text-2xl text-red-600';
        confirmBtn.className = 'w-full inline-flex justify-center items-center rounded-xl border border-transparent shadow-sm px-5 py-3 bg-red-600 text-base font-semibold text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 transition-colors sm:w-1/2';
    } else if (variant === 'info') {
        iconBg.className = 'flex items-center justify-center w-16 h-16 rounded-full bg-blue-50 mb-6';
        iconEl.className = 'fas fa-info-circle text-2xl text-blue-600';
        confirmBtn.className = 'w-full inline-flex justify-center items-center rounded-xl border border-transparent shadow-sm px-5 py-3 bg-blue-600 text-base font-semibold text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors sm:w-1/2';
    } else if (variant === 'success') {
        iconBg.className = 'flex items-center justify-center w-16 h-16 rounded-full bg-emerald-50 mb-6';
        iconEl.className = 'fas fa-check-circle text-2xl text-emerald-600';
        confirmBtn.className = 'w-full inline-flex justify-center items-center rounded-xl border border-transparent shadow-sm px-5 py-3 bg-emerald-600 text-base font-semibold text-white hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-emerald-500 transition-colors sm:w-1/2';
    }

    // Show Modal
    modal.classList.remove('hidden');
    // Animate in
    requestAnimationFrame(() => {
        backdrop.classList.remove('opacity-0');
        content.classList.remove('scale-95', 'opacity-0');
        content.classList.add('scale-100', 'opacity-100');
    });

    // Cleanup helper
    const closeModal = () => {
        backdrop.classList.add('opacity-0');
        content.classList.remove('scale-100', 'opacity-100');
        content.classList.add('scale-95', 'opacity-0');
        
        setTimeout(() => {
            modal.classList.add('hidden');
            // Remove event listeners to prevent duplicates
            confirmBtn.onclick = null;
            cancelBtn.onclick = null;
            backdrop.onclick = null;
        }, 200); // Match transition duration
    };

    // Event Listeners
    confirmBtn.onclick = () => {
        closeModal();
        if (typeof onConfirm === 'function') onConfirm();
    };

    cancelBtn.onclick = () => {
        closeModal();
        if (typeof onCancel === 'function') onCancel();
    };

    // Close on backdrop click
    backdrop.onclick = () => {
        closeModal();
        if (typeof onCancel === 'function') onCancel();
    };
};
console.log('Global Modal System Loaded');
// Helper functions to update counts in navbar
window.updateCartCount = function(count) {
  const cartBadge = document.getElementById('cart-badge');
  if (cartBadge) {
    cartBadge.textContent = count;
    if (count > 0) {
      cartBadge.classList.remove('hidden');
    } else {
      cartBadge.classList.add('hidden');
    }
  }
};

window.updateWishlistCount = function(count) {
  const wishlistBadge = document.getElementById('wishlist-badge');
  if (wishlistBadge) {
    wishlistBadge.textContent = count;
    if (count > 0) {
      wishlistBadge.classList.remove('hidden');
    } else {
      wishlistBadge.classList.add('hidden');
    }
  }
};
