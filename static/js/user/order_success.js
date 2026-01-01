/**
 * Order Success logic for GearUp.
 */

(function() {
    let secondsLeft = 5;
    const countdownElement = document.getElementById('countdown');
    
    const timer = setInterval(function() {
        secondsLeft--;
        if (countdownElement) {
            countdownElement.textContent = secondsLeft;
        }
        
        if (secondsLeft <= 0) {
            clearInterval(timer);
            const container = document.querySelector('[data-order-list-url]');
            const redirectUrl = container ? container.dataset.orderListUrl : null;
            if (redirectUrl) {
                window.location.href = redirectUrl;
            }
        }
    }, 1000);

    // If canvas-confetti is loaded, use it
    document.addEventListener('DOMContentLoaded', function() {
        if (typeof confetti === 'function') {
            confetti({
                particleCount: 150,
                spread: 80,
                origin: { y: 0.6 },
                colors: ['#10b981', '#3b82f6', '#8b5cf6']
            });
        }
    });
})();
