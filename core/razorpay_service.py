# core/razorpay_service.py
import razorpay
from django.conf import settings
from django.utils import timezone

class RazorpayService:
    def __init__(self):
        self.client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    
    def create_order(self, amount, currency='INR', receipt=None):
        """Create Razorpay order"""
        try:
            # Convert amount to paise (Indian currency smallest unit)
            amount_in_paise = int(amount * 100)
            
            # Create receipt if not provided
            if not receipt:
                receipt = f"receipt_{int(timezone.now().timestamp())}"
            
            data = {
                'amount': amount_in_paise,
                'currency': currency,
                'receipt': receipt,
                'payment_capture': '1'  # Auto capture payment
            }
            
            order = self.client.order.create(data=data)
            return order
            
        except Exception as e:
            raise Exception(f"Failed to create Razorpay order: {str(e)}")
    
    def verify_payment(self, razorpay_payment_id, razorpay_order_id, razorpay_signature):
        """Verify payment signature"""
        try:
            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            }
            
            # Verify the signature
            self.client.utility.verify_payment_signature(params_dict)
            return True
            
        except razorpay.errors.SignatureVerificationError:
            return False
        except Exception as e:
            raise Exception(f"Payment verification error: {str(e)}")
    
    def fetch_payment(self, payment_id):
        """Fetch payment details from Razorpay"""
        try:
            payment = self.client.payment.fetch(payment_id)
            return payment
        except Exception as e:
            raise Exception(f"Failed to fetch payment: {str(e)}")