// Auto-redirect to orders page after 5 seconds with countdown
let secondsLeft = 5;
const countdownElement = document.getElementById('countdown');

const timer = setInterval(function() {
  secondsLeft--;
  if (countdownElement) {
    countdownElement.textContent = secondsLeft;
  }
  
  if (secondsLeft <= 0) {
    clearInterval(timer);
    // Get the redirect URL from the data attribute
    const redirectUrl = document.body.dataset.orderListUrl;
    if (redirectUrl) {
      window.location.href = redirectUrl;
    }
  }
}, 1000);

// Add confetti effect (optional)
document.addEventListener('DOMContentLoaded', function() {
  // Simple confetti effect using emojis
  if (typeof confetti === 'function') {
    confetti({
      particleCount: 100,
      spread: 70,
      origin: { y: 0.6 }
    });
  }
});
