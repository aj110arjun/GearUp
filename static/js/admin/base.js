/**
 * Core UI logic for the GearUp admin portal.
 */

window.showSnackbar = function(message, type = 'success') {
    const snackbar = document.getElementById('snackbar');
    if (!snackbar) return;

    const messageElement = snackbar.querySelector('.snackbar-message');
    const iconElement = snackbar.querySelector('.snackbar-icon i');
    const contentElement = snackbar.querySelector('.snackbar-content');
    
    // Set message
    messageElement.textContent = message;
    
    // Set icon and colors based on type
    if (type === 'success') {
        iconElement.className = 'fas fa-check-circle text-2xl';
        contentElement.className = 'flex items-center gap-4 px-6 py-4 rounded-xl shadow-2xl border max-w-md snackbar-content bg-gradient-to-r from-green-50 to-emerald-50 border-green-200';
        iconElement.style.color = '#10b981';
        messageElement.style.color = '#065f46';
    } else if (type === 'error') {
        iconElement.className = 'fas fa-exclamation-circle text-2xl';
        contentElement.className = 'flex items-center gap-4 px-6 py-4 rounded-xl shadow-2xl border max-w-md snackbar-content bg-gradient-to-r from-red-50 to-rose-50 border-red-200';
        iconElement.style.color = '#ef4444';
        messageElement.style.color = '#991b1b';
    } else if (type === 'warning') {
        iconElement.className = 'fas fa-exclamation-triangle text-2xl';
        contentElement.className = 'flex items-center gap-4 px-6 py-4 rounded-xl shadow-2xl border max-w-md snackbar-content bg-gradient-to-r from-yellow-50 to-amber-50 border-yellow-200';
        iconElement.style.color = '#f59e0b';
        messageElement.style.color = '#92400e';
    } else if (type === 'info') {
        iconElement.className = 'fas fa-info-circle text-2xl';
        contentElement.className = 'flex items-center gap-4 px-6 py-4 rounded-xl shadow-2xl border max-w-md snackbar-content bg-gradient-to-r from-blue-50 to-sky-50 border-blue-200';
        iconElement.style.color = '#3b82f6';
        messageElement.style.color = '#1e40af';
    }
    
    // Show snackbar with animation
    snackbar.classList.remove('translate-y-32', 'opacity-0');
    snackbar.classList.add('translate-y-0', 'opacity-100');
    
    // Auto-hide after 4 seconds
    setTimeout(() => {
        window.hideSnackbar();
    }, 4000);
};

window.hideSnackbar = function() {
    const snackbar = document.getElementById('snackbar');
    if (snackbar) {
        snackbar.classList.remove('translate-y-0', 'opacity-100');
        snackbar.classList.add('translate-y-32', 'opacity-0');
    }
};

// Admin DOM ready basic handlers
document.addEventListener('DOMContentLoaded', () => {
    // Add hover effects to all interactive elements
    const interactiveElements = document.querySelectorAll('.nav-item, .stats-card, button');
    interactiveElements.forEach(element => {
        element.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
        });
        element.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
    
    // Update current page indicator
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-item');
    navLinks.forEach(link => {
        if (link.href && link.href.includes(currentPath)) {
            link.classList.add('active-link');
        }
    });
});
