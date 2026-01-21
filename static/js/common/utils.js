/**
 * Common utilities used across the GearUp application.
 */

window.getCookie = function(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
};

window.showPageLoader = function() {
    let loader = document.getElementById('global-page-loader');
    if (!loader) {
        loader = document.createElement('div');
        loader.id = 'global-page-loader';
        // Use z-[10000] to ensure it's above everything
        loader.className = 'fixed inset-0 z-[10000] flex flex-col items-center justify-center bg-gray-900/60 backdrop-blur-md transition-all duration-300 opacity-0';
        loader.innerHTML = `
            <div class="relative flex flex-col items-center">
                <div class="w-20 h-20 rounded-full border-4 border-white/20 border-t-emerald-500 animate-spin mb-4"></div>
                <div class="absolute top-6">
                    <i class="fas fa-mountain text-white text-2xl animate-pulse"></i>
                </div>
                <div class="text-white font-bold text-lg tracking-widest animate-pulse mt-2 uppercase">
                    Processing
                </div>
                <div class="flex gap-1 mt-2">
                    <div class="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                    <div class="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                    <div class="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-bounce"></div>
                </div>
            </div>
        `;
        document.body.appendChild(loader);
    }
    loader.classList.remove('hidden');
    requestAnimationFrame(() => {
        loader.classList.remove('opacity-0');
        loader.classList.add('opacity-100');
    });
};

window.hidePageLoader = function() {
    const loader = document.getElementById('global-page-loader');
    if (loader) {
        loader.classList.replace('opacity-100', 'opacity-0');
        setTimeout(() => {
            loader.classList.add('hidden');
        }, 300);
    }
};

window.globalApiPOST = async function(url, data = {}, options = {}) {
    if (options.showLoader) window.showPageLoader();
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': window.getCookie('csrftoken'),
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify(data)
        });
        return await response.json();
    } catch (error) {
        console.error('API POST Error:', error);
        throw error;
    } finally {
        if (options.showLoader) window.hidePageLoader();
    }
};

// Initialize common behaviors
document.addEventListener('DOMContentLoaded', () => {
    // Global form behaviors
    document.querySelectorAll('form').forEach(form => {
        // Only attach to forms that don't have 'no-loader' class
        if (form.classList.contains('no-loader')) return;

        form.addEventListener('submit', function(e) {
            // Check if form is valid if it has native validation
            if (form.checkValidity()) {
                // For standard form submissions (not AJAX)
                // We show the loader. If it's AJAX, the specific script should handle it,
                // but many of ours use standard submits that result in page reload.
                
                // Delay slightly to allow any validation UI to show if needed
                setTimeout(() => {
                    // Check if it's already submitted to prevent double clicks
                    if (form.dataset.submitted === 'true') {
                        e.preventDefault();
                        return;
                    }
                    form.dataset.submitted = 'true';
                    window.showPageLoader();
                }, 10);
            }
        });
    });

    // Handle back button or cancellation
    window.addEventListener('pageshow', (event) => {
        if (event.persisted) {
            window.hidePageLoader();
            document.querySelectorAll('form').forEach(f => delete f.dataset.submitted);
        }
    });

    // Global click behaviors for links/buttons that should show loader
    document.addEventListener('click', (e) => {
        const target = e.target.closest('.show-loader');
        if (target && e.button === 0 && !e.ctrlKey && !e.shiftKey && !e.metaKey && !e.altKey) {
            if (target.tagName === 'A' && (target.target === '_blank' || target.href.startsWith('javascript:'))) return;
            window.showPageLoader();
        }
    });
});
