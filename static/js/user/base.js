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
