/**
 * Checkout logic for GearUp.
 */

document.addEventListener('DOMContentLoaded', function() {
    const config = window.CHECKOUT_CONFIG || {};
    const checkoutForm = document.getElementById('checkout-form');
    const loadingOverlay = document.getElementById('loading-overlay');
    const placeOrderBtn = document.getElementById('place-order-btn');
    const selectedPaymentMethod = document.getElementById('selected-payment-method');
    const paymentDetails = document.getElementById('payment-details');
    
    // Variables for totals and coupons
    let appliedCoupon = null;
    let originalTotal = parseFloat(config.finalTotal);
    let currentTotal = originalTotal;
    let originalSubtotal = parseFloat(config.cartTotal);
    
    // Payment method selection
    const paymentOptions = document.querySelectorAll('.payment-radio');
    paymentOptions.forEach(radio => {
        radio.addEventListener('change', function() {
            const method = this.value;
            selectedPaymentMethod.value = method;
            
            // Update visual selection
            document.querySelectorAll('.payment-option').forEach(option => {
                option.style.borderColor = '#e5e7eb';
                option.style.backgroundColor = 'transparent';
            });
            
            const selectedOption = this.closest('.payment-option');
            selectedOption.style.borderColor = '#3b82f6';
            selectedOption.style.backgroundColor = '#dbeafe';
            
            // Update payment details
            updatePaymentDetails(method);
            
            // Update place order button text and state
            if (method === 'wallet') {
                const walletBalance = parseFloat(config.walletBalance || 0);
                updatePlaceOrderButton(method, walletBalance < currentTotal);
            } else {
                updatePlaceOrderButton(method, false);
            }
        });
    });
    
    // Address selection
    const addressOptions = document.querySelectorAll('.shipping-address-radio');
    addressOptions.forEach(radio => {
        radio.addEventListener('change', function() {
            // Update visual selection
            document.querySelectorAll('.address-option').forEach(option => {
                option.style.borderColor = '#e5e7eb';
            });
            
            const selectedOption = this.closest('.address-option');
            selectedOption.style.borderColor = '#3b82f6';
        });
    });
    
    // Initialize first payment method as selected
    const codAvailable = config.codAvailable === true;
    let firstPayment = document.querySelector('.payment-radio:checked');
    
    // If COD is not available and it's currently selected, select Razorpay instead
    if (!codAvailable && firstPayment && firstPayment.value === 'cash_on_delivery') {
        firstPayment.checked = false;
        const razorpayRadio = document.querySelector('.payment-radio[value="razorpay"]');
        if (razorpayRadio) {
            razorpayRadio.checked = true;
            firstPayment = razorpayRadio;
            selectedPaymentMethod.value = 'razorpay';
        }
    }
    
    if (firstPayment) {
        const selectedOption = firstPayment.closest('.payment-option');
        if (selectedOption) {
            selectedOption.style.borderColor = '#3b82f6';
            selectedOption.style.backgroundColor = '#dbeafe';
        }
        updatePaymentDetails(firstPayment.value);
        
        // Initial button state
        if (firstPayment.value === 'wallet') {
            const walletBalance = parseFloat(config.walletBalance || 0);
            updatePlaceOrderButton(firstPayment.value, walletBalance < currentTotal);
        } else {
            updatePlaceOrderButton(firstPayment.value, false);
        }
    }
    
    // Place order button click
    if (placeOrderBtn) {
        placeOrderBtn.addEventListener('click', function() {
            const shippingAddress = document.querySelector('.shipping-address-radio:checked');
            const agreeTerms = document.getElementById('agree_terms');
            const paymentMethod = selectedPaymentMethod.value;
            
            if (!shippingAddress) {
                alert('Please select a shipping address.');
                return;
            }
            
            if (!agreeTerms || !agreeTerms.checked) {
                alert('Please agree to the terms and conditions.');
                return;
            }
            
            // Wallet balance check
            if (paymentMethod === 'wallet') {
                const walletBalance = parseFloat(config.walletBalance || 0);
                if (walletBalance < currentTotal) {
                    alert('Insufficient wallet balance. Please choose another payment method.');
                    return;
                } 
            }
            
            // Handle different payment methods
            if (paymentMethod === 'razorpay') {
                initiateRazorpayPayment();
            } else {
                // For COD and Wallet, submit form directly
                submitOrder();
            }
        });
    }
    
    function updatePaymentDetails(method) {
        if (!paymentDetails) return;
        // Hide all details first
        document.querySelectorAll('#payment-details > div').forEach(detail => {
            detail.classList.add('hidden');
        });
        
        // Show selected method details
        paymentDetails.classList.remove('hidden');
        
        switch(method) {
            case 'razorpay':
                document.getElementById('razorpay-details')?.classList.remove('hidden');
                break;
            case 'wallet':
                document.getElementById('wallet-details')?.classList.remove('hidden');
                break;
            case 'cash_on_delivery':
                document.getElementById('cod-details')?.classList.remove('hidden');
                break;
        }
    }
    
    function updatePlaceOrderButton(method, isInsufficient = false) {
        if (!placeOrderBtn) return;
        if (isInsufficient) {
            placeOrderBtn.disabled = true;
            placeOrderBtn.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Insufficient Wallet Balance';
            placeOrderBtn.classList.remove('bg-emerald-600', 'hover:bg-emerald-700');
            placeOrderBtn.classList.add('bg-red-500', 'hover:bg-red-600');
            return;
        }

        placeOrderBtn.disabled = false;
        placeOrderBtn.classList.remove('bg-red-500', 'hover:bg-red-600');
        placeOrderBtn.classList.add('bg-emerald-600', 'hover:bg-emerald-700');

        switch(method) {
            case 'razorpay':
                placeOrderBtn.innerHTML = '<i class="fas fa-credit-card"></i> Pay with Razorpay';
                break;
            case 'wallet':
                placeOrderBtn.innerHTML = '<i class="fas fa-wallet"></i> Pay with Wallet';
                break;
            case 'cash_on_delivery':
                placeOrderBtn.innerHTML = '<i class="fas fa-lock"></i> Place Order';
                break;
            default:
                placeOrderBtn.innerHTML = '<i class="fas fa-lock"></i> Place Order';
        }
    }
    
    function initiateRazorpayPayment() {
        const orderTotal = currentTotal;
        
        // Get coupon discount if applied
        const couponDiscount = appliedCoupon ? parseFloat(appliedCoupon.discount_amount) : 0;
        
        // Show loading
        if (window.showPageLoader) window.showPageLoader();
        else loadingOverlay?.classList.remove('hidden');
        
        // Create Razorpay order via AJAX
        fetch(config.createRazorpayOrderUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': window.getCookie('csrftoken')
            },
            body: JSON.stringify({
                coupon_discount: couponDiscount
            })
        })
        .then(response => response.json())
        .then(data => {
            if (window.hidePageLoader) window.hidePageLoader();
            else loadingOverlay?.classList.add('hidden');
            
            if (data.success) {
                const options = {
                    key: data.key_id,
                    amount: data.amount,
                    currency: 'INR',
                    name: 'GearUp',
                    description: 'Order Payment',
                    order_id: data.order_id,
                    handler: function(response) {
                        // Payment successful
                        console.log('Payment successful:', response);
                        
                        // Set the hidden fields
                        document.getElementById('razorpay_payment_id').value = response.razorpay_payment_id;
                        document.getElementById('razorpay_order_id').value = response.razorpay_order_id;
                        document.getElementById('razorpay_signature').value = response.razorpay_signature;
                        
                        // Submit the form
                        submitOrder();
                    },
                    prefill: {
                        name: config.userName,
                        email: config.userEmail,
                        contact: config.userPhone
                    },
                    theme: {
                        color: '#10b981'
                    },
                    modal: {
                        ondismiss: function() {
                            console.log('Payment modal closed');
                            alert('Payment was cancelled. Please try again.');
                        }
                    },
                    notes: {
                        order_type: 'cart_checkout',
                        user_id: config.userId
                    }
                };
                
                const rzp = new Razorpay(options);
                rzp.open();
                
                // Handle payment failure
                rzp.on('payment.failed', function(response) {
                    console.error('Payment failed:', response.error);
                    
                    // Mark payment as failed
                    document.getElementById('payment_failed').value = 'true';
                    
                    // Create hidden input for payment failure reason
                    const failureReasonInput = document.createElement('input');
                    failureReasonInput.type = 'hidden';
                    failureReasonInput.name = 'payment_failure_reason';
                    failureReasonInput.value = response.error.description || response.error.reason || 'Payment failed';
                    checkoutForm.appendChild(failureReasonInput);
                    
                    // Show loading and submit form to create order with failed status
                    if (window.showPageLoader) window.showPageLoader();
                    else loadingOverlay?.classList.remove('hidden');
                    
                    // Add slight delay to ensure loading is visible
                    setTimeout(() => {
                        submitOrder();
                    }, 300);
                    
                    // Optional: Show message after a delay
                    setTimeout(() => {
                        alert('Payment failed. Your order has been created with failed payment status. You can retry payment from your order details.');
                    }, 1500);
                });
                
            } else {
                alert('Failed to initialize payment: ' + data.error);
            }
        })
        .catch(error => {
            if (window.hidePageLoader) window.hidePageLoader();
            else loadingOverlay?.classList.add('hidden');
            console.error('Error:', error);
            alert('Failed to initialize payment. Please try again.');
        });
    }
    
    function submitOrder() {
        // Show loading overlay
        if (window.showPageLoader) window.showPageLoader();
        else loadingOverlay?.classList.remove('hidden');
        
        // Submit form
        checkoutForm.submit();
    }
    
    // Select Coupon Function (Globally accessible)
    window.selectCoupon = function(couponCode) {
        if (appliedCoupon && appliedCoupon.coupon_code === couponCode) {
            return; // Already applied
        }
        
        // Show loading
        loadingOverlay?.classList.remove('hidden');
        
        fetch(config.validateCouponUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': window.getCookie('csrftoken')
            },
            body: JSON.stringify({
                coupon_code: couponCode,
                order_amount: originalTotal
            })
        })
        .then(response => response.json())
        .then(data => {
            if (window.hidePageLoader) window.hidePageLoader();
            else loadingOverlay?.classList.add('hidden');
            if (data.success) {
                appliedCoupon = data;
                showAppliedCoupon(data);
                updateOrderTotal(data);
                
                // Hide coupons grid
                const grid = document.getElementById('coupons-grid');
                if (grid) grid.classList.add('hidden');
                
                // Show notification
                if (window.showNotification) {
                    window.showNotification(data.message, 'success');
                }
                
                // Update hidden form fields
                document.getElementById('coupon_code_field').value = data.coupon_code;
                document.getElementById('coupon_discount_field').value = data.discount_amount;
            } else {
                if (window.showNotification) {
                    window.showNotification(data.message, 'error');
                } else {
                    alert(data.message);
                }
            }
        })
        .catch(error => {
            if (window.hidePageLoader) window.hidePageLoader();
            else loadingOverlay?.classList.add('hidden');
            console.error('Coupon error:', error);
            alert('Error applying coupon. Please try again.');
        });
    };
    
    // Remove Coupon Button
    const removeCouponBtn = document.getElementById('remove-coupon-btn');
    if (removeCouponBtn) {
        removeCouponBtn.addEventListener('click', function() {
            appliedCoupon = null;
            currentTotal = originalTotal;
            document.getElementById('applied-coupon').classList.add('hidden');
            document.getElementById('coupon-discount-line').classList.add('hidden');
            document.getElementById('final-total').textContent = '₹' + originalTotal.toFixed(2);
            
            // Update button if wallet is selected
            if (selectedPaymentMethod.value === 'wallet') {
                const walletBalance = parseFloat(config.walletBalance || 0);
                updatePlaceOrderButton('wallet', walletBalance < currentTotal);
            }
            
            // Show coupons grid again
            const couponsGrid = document.getElementById('coupons-grid');
            if (couponsGrid) {
                couponsGrid.classList.remove('hidden');
            }
            
            // Recalculate tax
            const tax = originalSubtotal * 0.1;
            document.getElementById('tax-amount').textContent = '₹' + tax.toFixed(2);
            
            // Clear hidden form fields
            document.getElementById('coupon_code_field').value = '';
            document.getElementById('coupon_discount_field').value = '0';
            
            if (window.showNotification) {
                window.showNotification('Coupon removed', 'info');
            }
        });
    }
    
    function showAppliedCoupon(data) {
        const ad = document.getElementById('applied-coupon');
        if (ad) ad.classList.remove('hidden');
        document.getElementById('applied-coupon-code').textContent = data.coupon_code;
        document.getElementById('applied-coupon-discount').textContent = 
            `${data.discount_percentage}% off - Save ₹${data.discount_amount.toFixed(2)}`;
    }
    
    function updateOrderTotal(data) {
        // Show coupon discount line
        document.getElementById('coupon-discount-line')?.classList.remove('hidden');
        document.getElementById('coupon-discount-amount').textContent = '-₹' + data.discount_amount.toFixed(2);
        
        // Negate discount from the total amount
        currentTotal = originalTotal - data.discount_amount;
        document.getElementById('final-total').textContent = '₹' + currentTotal.toFixed(2);

        // Update button if wallet is selected
        if (selectedPaymentMethod.value === 'wallet') {
            const walletBalance = parseFloat(config.walletBalance || 0);
            updatePlaceOrderButton('wallet', walletBalance < currentTotal);
        }
        
        // Keep tax display consistent with original subtotal
        const originalTax = originalSubtotal * 0.1;
        document.getElementById('tax-amount').textContent = '₹' + originalTax.toFixed(2);
    }
});
