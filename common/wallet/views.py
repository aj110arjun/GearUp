import razorpay
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Wallet, Transaction
from .forms import DepositForm, PaymentForm
from core.services import WalletService
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from decimal import Decimal

# Initialize Razorpay client
try:
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
except Exception as e:
    print(f"Razorpay client initialization failed: {e}")
    client = None

@login_required
def wallet_dashboard(request):
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    transactions = WalletService.get_transaction_history(wallet, 5)
    
    context = {
        'wallet': wallet,
        'transactions': transactions,
    }
    return render(request, 'user/wallet/dashboard.html', context)

@login_required
def deposit_funds(request):
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = DepositForm(request.POST)
        if form.is_valid():
            try:
                # Auto-generate description for deposit
                description = f"Wallet deposit via Razorpay - ₹{form.cleaned_data['amount']}"
                transaction = WalletService.deposit(
                    wallet,
                    form.cleaned_data['amount'],
                    description
                )
                messages.success(request, f'Successfully deposited ₹{form.cleaned_data["amount"]}')
                return redirect('wallet:wallet_dashboard')
            except Exception as e:
                messages.error(request, f'Deposit failed: {str(e)}')
    else:
        form = DepositForm()
    
    return render(request, 'user/wallet/deposit.html', {'form': form, 'wallet': wallet})

@login_required
def make_payment(request):
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            try:
                transaction = WalletService.make_payment(
                    wallet,
                    form.cleaned_data['amount'],
                    form.cleaned_data['description']
                )
                admin_transaction = AdminTransaction.objects.create(
                    transaction_type='credit',
                    user=request.user,
                    amount=form.cleaned_data['amount'],
                    description=form.cleaned_data['description'],
                    status='completed',
                    payment_method='wallet'


                )
                messages.success(request, f'Payment of ₹{form.cleaned_data["amount"]} completed successfully')
                return redirect('wallet:wallet_dashboard')
            except ValueError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f'Payment failed: {str(e)}')
    else:
        form = PaymentForm()
    
    return render(request, 'user/wallet/payment.html', {'form': form, 'wallet': wallet})

@login_required
def transaction_history(request):
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    transactions_list = Transaction.objects.filter(wallet=wallet).order_by('-created_at')
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(transactions_list, 8)  # 8 transactions per page
    
    try:
        transactions = paginator.page(page)
    except PageNotAnInteger:
        transactions = paginator.page(1)
    except EmptyPage:
        transactions = paginator.page(paginator.num_pages)
    
    return render(request, 'user/wallet/transaction_history.html', {
        'transactions': transactions,
        'wallet': wallet
    })

@login_required
def transaction_detail(request, transaction_id):
    # Get transaction and ensure it belongs to the current user
    transaction = get_object_or_404(
        Transaction, 
        transaction_id=transaction_id,
        wallet__user=request.user
    )
    
    # Get related transactions (same reference for refunds, etc.)
    related_transactions = Transaction.objects.filter(
        wallet__user=request.user
    ).exclude(id=transaction.id)
    
    context = {
        'transaction': transaction,
        'related_transactions': related_transactions,
    }
    return render(request, 'user/wallet/transaction_detail.html', context)

@login_required
@require_http_methods(["POST"])
def create_razorpay_order(request):
    """Create Razorpay order"""
    try:
        data = json.loads(request.body)
        amount = int(data.get('amount', 0))  # Amount in paise
        
        if amount < 100:  # Minimum ₹1
            return JsonResponse({'success': False, 'error': 'Amount must be at least ₹1'})
        
        # Auto-generate description
        description = f"Wallet deposit - ₹{amount/100}"
        
        # Create order data
        order_data = {
            'amount': amount,
            'currency': 'INR',
            'payment_capture': 1,  # Auto capture payment
            'notes': {
                'description': description,
                'user_id': str(request.user.id),
                'purpose': 'wallet_deposit'
            }
        }
        
        # Create order
        order = client.order.create(data=order_data)
        
        return JsonResponse({
            'success': True,
            'order_id': order['id'],
            'amount': order['amount'],
            'currency': order['currency'],
            'key_id': settings.RAZORPAY_KEY_ID
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_http_methods(["POST"])
def verify_razorpay_payment(request):
    """Verify Razorpay payment signature"""
    try:
        data = json.loads(request.body)
        print(f"Payment verification data: {data}")  # Debug log
        
        # Check if client is initialized
        if not client:
            return JsonResponse({
                'success': False, 
                'error': 'Payment service not configured properly'
            })
        
        # Verify payment signature
        params_dict = {
            'razorpay_order_id': data['razorpay_order_id'],
            'razorpay_payment_id': data['razorpay_payment_id'],
            'razorpay_signature': data['razorpay_signature']
        }
        
        print(f"Verifying signature with params: {params_dict}")  # Debug log
        
        # Verify signature
        client.utility.verify_payment_signature(params_dict)
        print("Signature verification successful")  # Debug log
        
        # If signature is valid, process the deposit
        amount = Decimal(data['amount'])
        print(f"Processing deposit amount: {amount}")  # Debug log
        
        # Auto-generate description
        description = f"Wallet deposit via Razorpay - ₹{amount}"
        
        # Get user's wallet
        wallet, created = Wallet.objects.get_or_create(user=request.user)
        print(f"Wallet found: {wallet}, created: {created}")  # Debug log
        
        # Process deposit
        transaction = WalletService.deposit(wallet, amount, description)
        print(f"Transaction created: {transaction.transaction_id}")  # Debug log
        
        return JsonResponse({
            'success': True,
            'transaction_id': transaction.transaction_id,
            'amount': amount,
            'new_balance': float(wallet.balance)
        })
        
    except razorpay.errors.SignatureVerificationError as e:
        print(f"Signature verification failed: {e}")  # Debug log
        return JsonResponse({
            'success': False, 
            'error': 'Invalid payment signature. Please contact support.'
        })
    except Exception as e:
        print(f"Unexpected error in verify_razorpay_payment: {e}")  # Debug log
        return JsonResponse({
            'success': False, 
            'error': f'Payment verification failed: {str(e)}'
        })

@csrf_exempt
def razorpay_webhook(request):
    """Handle Razorpay webhooks for payment status updates"""
    if request.method == 'POST':
        webhook_body = request.body.decode('utf-8')
        webhook_signature = request.headers.get('X-Razorpay-Signature', '')
        
        try:
            # Verify webhook signature
            client.utility.verify_webhook_signature(webhook_body, webhook_signature, settings.RAZORPAY_WEBHOOK_SECRET)
            
            webhook_data = json.loads(webhook_body)
            event = webhook_data.get('event')
            
            if event == 'payment.captured':
                # Handle successful payment
                payment_data = webhook_data.get('payload', {}).get('payment', {}).get('entity', {})
                order_id = payment_data.get('order_id')
                # You can update transaction status here if needed
                
            return JsonResponse({'status': 'success'})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    return JsonResponse({'status': 'error'}, status=405)