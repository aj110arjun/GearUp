import json
import razorpay

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db import transaction, models
from django.core.paginator import Paginator
from django.conf import settings
from decimal import Decimal

from .models import Wallet, WalletTransaction
from .forms import AddMoneyForm, WithdrawalForm

# Initialize Razorpay client
try:
    razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
except Exception as e:
    print(f"Razorpay initialization error: {e}")
    razorpay_client = None

@login_required
def wallet_dashboard(request):
    """Main wallet dashboard"""
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    
    # Get recent transactions
    recent_transactions = wallet.transactions.all().order_by('-created_at')[:5]
    
    # Statistics
    total_credited = wallet.transactions.filter(
        transaction_type='credit', 
        status='completed'
    ).aggregate(total=models.Sum('amount'))['total'] or 0
    
    total_debited = wallet.transactions.filter(
        transaction_type='debit', 
        status='completed'
    ).aggregate(total=models.Sum('amount'))['total'] or 0
    
    context = {
        'wallet': wallet,
        'recent_transactions': recent_transactions,
        'total_credited': total_credited,
        'total_debited': total_debited,
    }
    return render(request, 'user/wallet/wallet_dashboard.html', context)

@login_required
def wallet_transactions(request):
    """Transaction history with pagination and filters"""
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    
    # Filter parameters
    transaction_type = request.GET.get('type', '')
    category = request.GET.get('category', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    transactions = wallet.transactions.all()
    
    # Apply filters
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)
    if category:
        transactions = transactions.filter(category=category)
    if date_from:
        transactions = transactions.filter(created_at__date__gte=date_from)
    if date_to:
        transactions = transactions.filter(created_at__date__lte=date_to)
    
    # Statistics for the sidebar
    total_credited = wallet.transactions.filter(
        transaction_type='credit', 
        status='completed'
    ).aggregate(total=models.Sum('amount'))['total'] or 0
    
    total_debited = wallet.transactions.filter(
        transaction_type='debit', 
        status='completed'
    ).aggregate(total=models.Sum('amount'))['total'] or 0
    
    total_transactions = transactions.count()
    
    # Get last transactions for quick stats
    last_credit = wallet.transactions.filter(
        transaction_type='credit'
    ).order_by('-created_at').first()
    
    last_debit = wallet.transactions.filter(
        transaction_type='debit'
    ).order_by('-created_at').first()
    
    # Monthly total
    from django.utils import timezone
    from django.db.models import Sum
    current_month = timezone.now().month
    current_year = timezone.now().year
    
    monthly_total = wallet.transactions.filter(
        created_at__month=current_month,
        created_at__year=current_year
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Pagination
    paginator = Paginator(transactions.order_by('-created_at'), 15)  # 15 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'wallet': wallet,
        'page_obj': page_obj,
        'transaction_type': transaction_type,
        'category': category,
        'date_from': date_from,
        'date_to': date_to,
        'total_credited': total_credited,
        'total_debited': total_debited,
        'total_transactions': total_transactions,
        'last_credit': last_credit,
        'last_debit': last_debit,
        'monthly_total': monthly_total,
        'current_date': timezone.now(),
    }
    
    return render(request, 'user/wallet/transaction_history.html', context)

@login_required
def add_money(request):
    """Add money to wallet with Razorpay integration"""
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    
    # Check if Razorpay is configured
    if not razorpay_client or not hasattr(settings, 'RAZORPAY_KEY_ID') or not settings.RAZORPAY_KEY_ID:
        messages.error(request, 'Payment system is currently unavailable. Please try again later.')
        return render(request, 'user/wallet/add_money.html', {'form': AddMoneyForm(), 'wallet': wallet})
    
    if request.method == 'POST':
        form = AddMoneyForm(request.POST)
        if form.is_valid():
            custom_amount = form.cleaned_data.get('custom_amount')
            selected_amount = form.cleaned_data.get('amount')
            
            # Use custom amount if provided, otherwise use selected amount
            if custom_amount:
                amount = float(custom_amount)
            elif selected_amount:
                amount = float(selected_amount)
            else:
                messages.error(request, 'Please select or enter an amount')
                return render(request, 'user/wallet/add_money.html', {'form': form, 'wallet': wallet})
            
            # Validate amount
            if amount < 10:
                messages.error(request, 'Minimum amount to add is ₹10')
                return render(request, 'user/wallet/add_money.html', {'form': form, 'wallet': wallet})
            
            if amount > 10000:
                messages.error(request, 'Maximum amount to add is ₹10,000')
                return render(request, 'user/wallet/add_money.html', {'form': form, 'wallet': wallet})
            
            try:
                # Create Razorpay order
                razorpay_amount = int(amount * 100)  # Convert to paise
                
                order_data = {
                    'amount': razorpay_amount,
                    'currency': 'INR',
                    'payment_capture': 1,  # Auto capture payment
                    'notes': {
                        'user_id': str(request.user.id),
                        'purpose': 'wallet_topup',
                        'amount': str(amount)
                    }
                }
                
                # Create order in Razorpay
                razorpay_order = razorpay_client.order.create(data=order_data)
                
                # Store order details in session for verification
                request.session['razorpay_order_id'] = razorpay_order['id']
                request.session['wallet_topup_amount'] = amount
                
                context = {
                    'form': form,
                    'wallet': wallet,
                    'razorpay_order_id': razorpay_order['id'],
                    'razorpay_amount': razorpay_amount,
                    'razorpay_currency': 'INR',
                    'razorpay_key_id': settings.RAZORPAY_KEY_ID,
                    'callback_url': request.build_absolute_uri('/wallet/payment-success/'),
                    'amount': amount,
                }
                
                return render(request, 'user/wallet/add_money.html', context)
                
            except Exception as e:
                print(f"Razorpay order creation error: {str(e)}")
                messages.error(request, f'Error creating payment order: {str(e)}')
                return render(request, 'user/wallet/add_money.html', {'form': form, 'wallet': wallet})
    else:
        form = AddMoneyForm()
    
    context = {
        'form': form,
        'wallet': wallet,
    }
    return render(request, 'user/wallet/add_money.html', context)

@login_required
@require_POST
def verify_payment(request):
    """Verify Razorpay payment and add money to wallet"""
    try:
        data = json.loads(request.body)
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_signature = data.get('razorpay_signature')
        
        print(f"🔍 Payment verification started")
        print(f"   Order ID: {razorpay_order_id}")
        print(f"   Payment ID: {razorpay_payment_id}")
        
        # Check if we have the required data
        if not all([razorpay_payment_id, razorpay_order_id, razorpay_signature]):
            return JsonResponse({
                'success': False,
                'message': 'Missing payment data.'
            })
        
        # Verify payment signature
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }
        
        razorpay_client.utility.verify_payment_signature(params_dict)
        print("✅ Payment signature verified")
        
        # Get order details from Razorpay
        razorpay_order = razorpay_client.order.fetch(razorpay_order_id)
        
        # Verify order amount matches session amount
        session_amount = request.session.get('wallet_topup_amount')
        if not session_amount:
            return JsonResponse({
                'success': False,
                'message': 'Session expired. Please try again.'
            })
        
        # Convert amounts for comparison
        razorpay_amount = float(razorpay_order['amount']) / 100
        session_amount_float = float(session_amount)
        
        print(f"💰 Amount check - Session: ₹{session_amount_float}, Razorpay: ₹{razorpay_amount}")
        
        if razorpay_amount != session_amount_float:
            return JsonResponse({
                'success': False,
                'message': f'Payment amount mismatch. Expected: ₹{session_amount}, Got: ₹{razorpay_amount}'
            })
        
        # Payment successful - add money to wallet
        wallet, created = Wallet.objects.get_or_create(user=request.user)
        print(f"👛 Wallet found - Balance before: ₹{wallet.balance}")
        
        with transaction.atomic():
            # Convert to Decimal for wallet operation
            amount_to_add = Decimal(str(session_amount))
            
            # Credit the wallet
            success = wallet.credit(
                amount=amount_to_add,
                category='promotional',
                description=f'Wallet top-up via Razorpay - Payment ID: {razorpay_payment_id}'
            )
            
            if not success:
                raise Exception("Failed to credit amount to wallet")
        
        # Refresh and verify
        wallet.refresh_from_db()
        print(f"💳 Wallet after credit: ₹{wallet.balance}")
        
        # Verify transaction was created
        recent_transaction = wallet.transactions.filter(
            amount=amount_to_add,
            transaction_type='credit'
        ).first()
        
        if not recent_transaction:
            raise Exception("Transaction record was not created")
        
        print(f"📝 Transaction created: {recent_transaction.id}")
        
        # Clear session data
        request.session.pop('razorpay_order_id', None)
        request.session.pop('wallet_topup_amount', None)
        
        return JsonResponse({
            'success': True,
            'message': f'₹{session_amount} has been successfully added to your wallet!',
            'new_balance': float(wallet.balance)
        })
        
    except razorpay.errors.SignatureVerificationError:
        print("❌ Signature verification failed")
        return JsonResponse({
            'success': False,
            'message': 'Payment verification failed. Please contact support.'
        })
    except Exception as e:
        print(f"💥 Payment verification error: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return JsonResponse({
            'success': False,
            'message': f'Error processing payment: {str(e)}'
        })
    

@login_required
def payment_success(request):
    """Payment success page"""
    messages.success(request, 'Payment completed successfully! Your wallet has been updated.')
    return redirect('wallet:dashboard')

@login_required
def payment_failed(request):
    """Payment failed page"""
    messages.error(request, 'Payment failed. Please try again.')
    return redirect('wallet:add_money')

@login_required
def withdraw_money(request):
    """Withdraw money from wallet"""
    wallet = get_object_or_404(Wallet, user=request.user)
    
    if request.method == 'POST':
        form = WithdrawalForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            bank_account = form.cleaned_data['bank_account']
            ifsc_code = form.cleaned_data['ifsc_code']
            
            try:
                with transaction.atomic():
                    wallet.debit(
                        amount=amount,
                        category='withdrawal',
                        description=f'Withdrawal to bank account {bank_account}'
                    )
                
                messages.success(request, f'Withdrawal request for ₹{amount} has been submitted successfully! It will be processed within 3-5 business days.')
                return redirect('wallet:dashboard')
                
            except ValueError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f'Error processing withdrawal: {str(e)}')
    else:
        form = WithdrawalForm()
    
    context = {
        'form': form,
        'wallet': wallet,
    }
    return render(request, 'user/wallet/withdraw_money.html', context)

@login_required
@require_POST
def ajax_wallet_balance(request):
    """AJAX endpoint to get current wallet balance"""
    wallet = get_object_or_404(Wallet, user=request.user)
    return JsonResponse({
        'balance': float(wallet.balance),
        'formatted_balance': f'₹{wallet.balance}'
    })

# Utility functions for other apps to use
def add_wallet_credit(user, amount, category='promotional', description=''):
    """Utility function to add credit to user's wallet"""
    try:
        wallet, created = Wallet.objects.get_or_create(user=user)
        wallet.credit(amount, category=category, description=description)
        return True
    except Exception as e:
        print(f"Error adding wallet credit: {e}")
        return False

def deduct_wallet_amount(user, amount, category='purchase', description=''):
    """Utility function to deduct amount from user's wallet"""
    try:
        wallet, created = Wallet.objects.get_or_create(user=user)
        wallet.debit(amount, category=category, description=description)
        return True
    except ValueError as e:
        # Insufficient balance
        return False
    except Exception as e:
        print(f"Error deducting wallet amount: {e}")
        return False