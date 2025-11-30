import razorpay
from django.conf import settings

client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

def create_razorpay_order(amount, currency='INR', receipt=None):
    """
    Create a Razorpay order
    amount: Amount in paise (so ₹100 = 10000 paise)
    """
    try:
        data = {
            'amount': amount,
            'currency': currency,
            'payment_capture': 1  # Auto capture payment
        }
        
        if receipt:
            data['receipt'] = receipt
            
        order = client.order.create(data=data)
        return order
        
    except Exception as e:
        print(f"Razorpay order creation error: {e}")
        return None

def verify_payment_signature(order_id, payment_id, signature):
    """
    Verify payment signature to prevent fraud
    """
    try:
        params_dict = {
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }
        
        return client.utility.verify_payment_signature(params_dict)
        
    except Exception as e:
        print(f"Payment verification error: {e}")
        return False

def get_payment_details(payment_id):
    """
    Get payment details from Razorpay
    """
    try:
        return client.payment.fetch(payment_id)
    except Exception as e:
        print(f"Error fetching payment details: {e}")
        return None