/**
 * Order Details logic for GearUp.
 */

(function() {
    const config = window.ORDER_DETAILS_CONFIG || {};
    const csrftoken = window.getCookie ? window.getCookie('csrftoken') : null;

    window.retryRazorpayPayment = function(orderId) {
        const loadingOverlay = document.getElementById('loading-overlay');
        if (loadingOverlay) loadingOverlay.classList.remove('hidden');
        
        fetch(config.retryPaymentUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({})
        })
        .then(response => response.json())
        .then(data => {
            if (loadingOverlay) loadingOverlay.classList.add('hidden');
            
            if (data.success) {
                const options = {
                    key: data.key_id,
                    amount: data.amount,
                    currency: data.currency,
                    name: 'GearUp - Retry Payment',
                    description: `Payment for Order #${config.orderNumber}`,
                    order_id: data.order_id,
                    handler: function(response) {
                        verifyPayment(response);
                    },
                    prefill: {
                        name: data.user_name || '',
                        email: data.user_email || '',
                        contact: data.user_contact || ''
                    },
                    theme: {
                        color: '#10b981'
                    },
                    modal: {
                        ondismiss: function() {
                            console.log('Payment modal closed');
                        }
                    }
                };
                
                const rzp = new Razorpay(options);
                rzp.open();
                
                rzp.on('payment.failed', function(response) {
                    console.error('Payment failed:', response.error);
                    window.location.href = config.paymentFailedUrl;
                });
                
            } else {
                alert('Failed to initialize payment: ' + data.error);
            }
        })
        .catch(error => {
            if (loadingOverlay) loadingOverlay.classList.add('hidden');
            console.error('Error:', error);
            alert('Failed to initialize payment. Please try again.');
        });
    };

    function verifyPayment(paymentResponse) {
        const loadingOverlay = document.getElementById('loading-overlay');
        if (loadingOverlay) loadingOverlay.classList.remove('hidden');
        
        const formData = new FormData();
        formData.append('razorpay_payment_id', paymentResponse.razorpay_payment_id);
        formData.append('razorpay_order_id', paymentResponse.razorpay_order_id);
        formData.append('razorpay_signature', paymentResponse.razorpay_signature);
        formData.append('csrfmiddlewaretoken', csrftoken);
        
        fetch(config.verifyRetryPaymentUrl, {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (loadingOverlay) loadingOverlay.classList.add('hidden');
            if (response.ok) {
                window.location.href = config.orderSuccessUrl;
            } else {
                alert('Payment verification failed. Please try again.');
                window.location.reload();
            }
        })
        .catch(error => {
            if (loadingOverlay) loadingOverlay.classList.add('hidden');
            console.error('Verification error:', error);
            alert('Payment verification failed. Please try again.');
            window.location.reload();
        });
    }
})();
