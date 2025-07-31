import base64

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.core.files.base import ContentFile
from django.utils.timezone import now

from .models import AccountInfo
from .forms import UserUpdateForm, ProfileUpdateForm



@never_cache
@login_required(login_url='login')
def account_info(request):
    account, created = AccountInfo.objects.get_or_create(
        user=request.user,
        defaults={
            'address': 'Not set',
            'city': 'Not set',
            'landmark': 'Not set',
            'street': 'Not set',
            'pincode': '000000',
        }
    )
    return render(request, 'registration/account.html', {'account': account})

@login_required
def edit_account(request):
    profile = request.user.accountinfo  # your OneToOne profile

    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)

        cropped_image_data = request.POST.get('cropped_profile')

        if u_form.is_valid() and p_form.is_valid():
            u_form.save()

            # Save profile form fields (except image)
            p_form.save(commit=False)

            # If cropped image is provided
            if cropped_image_data:
                format, imgstr = cropped_image_data.split(';base64,')
                ext = format.split('/')[-1]
                profile.profile.save(
                    f"profile_{request.user.id}.{ext}",
                    ContentFile(base64.b64decode(imgstr)),
                    save=True
                )
            else:
                # Save original uploaded file if no crop
                if request.FILES.get('profile'):
                    profile.profile = request.FILES['profile']
                    profile.save()

            return redirect('account')

    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=profile)

    return render(request, 'registration/edit_account.html', {
        'u_form': u_form,
        'p_form': p_form,
        'timestamp': now().timestamp(),
         'cache_buster': int(now().timestamp()),
    })


@never_cache
@login_required(login_url='admin_login')
def admin_account(request):
	return render(request, 'custom_admin/admin_account.html')

