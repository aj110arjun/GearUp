from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required


# @login_required(login_url='user_login')
def home(request):
    if not request.session.get('user_id'):  # fixed key
        return redirect('user_login')
    return render(request, 'user/home.html')
