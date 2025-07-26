from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.contrib.auth import logout


def user_view(request):
	users = User.objects.filter(is_superuser=False)
	context={
	'users': users
	}
	return render(request, 'custom_admin/users.html', context)

@staff_member_required
@require_POST
def toggle_user_status(request, id):
    user = get_object_or_404(User, pk=id)
    user.is_active = not user.is_active
    user.save()
    status = "unblocked" if user.is_active else "blocked"
    messages.success(request, f"User has been {status}.")
    return redirect('admin_user_detail', id=user.id)

@staff_member_required
def admin_user_detail(request, id):
    user = get_object_or_404(User, pk=id)
    return render(request, 'custom_admin/user_details.html', {'user_obj': user})