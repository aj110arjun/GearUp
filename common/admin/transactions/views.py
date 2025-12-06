from django.shortcuts import render, get_object_or_404
from .models import AdminTransaction


def transaction_list(request):
    transactions = AdminTransaction.objects.all()
    context={
        'transactions': transactions
    }
    return render(request, 'admin/transactions/transaction_list.html', context)

def transaction_detail(request, transaction_id):
    transaction = get_object_or_404(AdminTransaction, transaction_id=transaction_id)
    context = {
        'transaction': transaction
    }
    return render(request, 'admin/transactions/transaction_detail.html', context)
