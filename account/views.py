import base64

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.core.files.base import ContentFile
from django.utils.timezone import now
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta
from django.contrib import messages


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
    profile = request.user.accountinfo
    original_email = request.user.email  # store old email

    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)

        cropped_image_data = request.POST.get('cropped_profile')

        if u_form.is_valid() and p_form.is_valid():
            new_email = u_form.cleaned_data.get('email')

            # Case 1: Email changed -> trigger OTP
            if new_email != original_email:
                otp = profile.generate_email_otp()
                profile.pending_email = new_email
                profile.save()

                # Send OTP Email
                send_mail(
                    subject='Verify your new email',
                    message=f'Your OTP for email verification is: {otp}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[new_email],
                )

                # Save other details temporarily (without updating email)
                p_form.save(commit=False)
                # handle cropped image
                if cropped_image_data:
                    format, imgstr = cropped_image_data.split(';base64,')
                    ext = format.split('/')[-1]
                    profile.profile.save(
                        f"profile_{request.user.id}.{ext}",
                        ContentFile(base64.b64decode(imgstr)),
                        save=True
                    )
                else:
                    if request.FILES.get('profile'):
                        profile.profile = request.FILES['profile']
                        profile.save()

                return redirect('verify_email_otp')  # new page for OTP verification

            # Case 2: Email not changed -> normal update
            u_form.save()
            p_form.save()

            # Handle cropped image
            if cropped_image_data:
                format, imgstr = cropped_image_data.split(';base64,')
                ext = format.split('/')[-1]
                profile.profile.save(
                    f"profile_{request.user.id}.{ext}",
                    ContentFile(base64.b64decode(imgstr)),
                    save=True
                )

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

@login_required
def verify_email_otp(request):
    profile = request.user.accountinfo
    message = None

    if request.method == 'POST':
        entered_otp = request.POST.get('otp', '')

        if entered_otp == profile.email_otp:
            # Update email permanently
            request.user.email = profile.pending_email
            request.user.save()

            # Clear pending fields
            profile.pending_email = None
            profile.email_otp = None
            profile.otp_created_at = None
            profile.save()

            messages.success(request, "Email verified and updated successfully!")
            return redirect('account')
        else:
            message = "Invalid OTP. Please try again."

    return render(request, 'registration/otp/verify_email_otp.html', {'message': message})

