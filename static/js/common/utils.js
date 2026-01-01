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

window.globalApiPOST = async function(url, data = {}) {
    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': window.getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify(data)
    });
    return response.json();
};

// Initialize common behaviors
document.addEventListener('DOMContentLoaded', () => {
    // Disable browser validation globally
    document.querySelectorAll('form').forEach(form => {
        form.setAttribute('novalidate', 'true');
    });

    // Highlight fields with errors
    document.querySelectorAll('.form-error-text').forEach(errorMsg => {
        const container = errorMsg.parentElement;
        const input = container.querySelector('input, select, textarea');
        if (input) {
            input.classList.add('field-error');
        }
    });
});
