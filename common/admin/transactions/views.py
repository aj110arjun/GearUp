from django.shortcuts import render, get_object_or_404
from .models import AdminTransaction
from django.db.models import Sum, Q
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.cache import never_cache
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

@staff_member_required
@never_cache
def transaction_list(request):
    # Base queryset for statistics (global stats)
    all_transactions = AdminTransaction.objects.all()

    # Calculate statistics (Global)
    total_transactions = all_transactions.count()
    total_credits = all_transactions.filter(payment_type='credit').aggregate(total=Sum('amount'))['total'] or 0
    total_debits = all_transactions.filter(payment_type='debit').aggregate(total=Sum('amount'))['total'] or 0
    pending_count = all_transactions.filter(payment_status='pending').count()

    # Queryset for listing (Filtered)
    transactions = AdminTransaction.objects.all().order_by('-created_at')

    # Get filter parameters
    payment_method = request.GET.get('payment_method', '')
    payment_status = request.GET.get('payment_status', '')
    payment_type = request.GET.get('payment_type', '')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    search_query = request.GET.get('search', '')

    # Apply filters
    if payment_method:
        transactions = transactions.filter(payment_method=payment_method)
    
    if payment_status:
        transactions = transactions.filter(payment_status=payment_status)
        
    if payment_type:
        transactions = transactions.filter(payment_type=payment_type)
        
    if start_date:
        transactions = transactions.filter(created_at__date__gte=start_date)
        
    if end_date:
        transactions = transactions.filter(created_at__date__lte=end_date)
        
    if search_query:
        transactions = transactions.filter(
            Q(transaction_id__icontains=search_query) |
            Q(order__order_number__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(transactions, 8)  # 8 transactions per page

    try:
        transactions_page = paginator.page(page)
    except PageNotAnInteger:
        transactions_page = paginator.page(1)
    except EmptyPage:
        transactions_page = paginator.page(paginator.num_pages)
    
    context={
        'transactions': transactions_page,
        'total_transactions': total_transactions,
        'total_credits': total_credits,
        'total_debits': total_debits,
        'pending_count': pending_count,
        # Filter context for template preservation
        'filter_payment_method': payment_method,
        'filter_payment_status': payment_status,
        'filter_payment_type': payment_type,
        'filter_start_date': start_date,
        'filter_end_date': end_date,
        'search_query': search_query,
        # Choices for filters
        'payment_method_choices': AdminTransaction.PAYMENT_METHOD,
        'payment_status_choices': AdminTransaction.PAYMENT_STATUS,
        'payment_type_choices': AdminTransaction.PAYMENT_TYPE,
    }
    return render(request, 'admin/transactions/transaction_list.html', context)

@staff_member_required
@never_cache
def transaction_detail(request, transaction_id):
    transaction = get_object_or_404(AdminTransaction, transaction_id=transaction_id)
    context = {
        'transaction': transaction
    }
    return render(request, 'admin/transactions/transaction_detail.html', context)
