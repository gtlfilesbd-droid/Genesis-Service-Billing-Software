from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import UserProfile
from django.contrib.auth.models import User


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'registration/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def profile_view(request):
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)

    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.save()

        profile.phone = request.POST.get('phone', '')
        profile.department = request.POST.get('department', '')
        if 'profile_picture' in request.FILES:
            profile.profile_picture = request.FILES['profile_picture']
        profile.save()

        messages.success(request, 'Profile updated successfully.')
        return redirect('profile')

    perms_list = [
        (profile.can_add_client, 'Add Client'),
        (profile.can_edit_client, 'Edit Client'),
        (profile.can_delete_client, 'Delete Client'),
        (profile.can_generate_bill, 'Generate Bill'),
        (profile.can_edit_bill, 'Edit Bill'),
        (profile.can_view_reports, 'View Reports'),
        (profile.can_export_reports, 'Export Reports'),
    ]
    return render(request, 'registration/profile.html', {'profile': profile, 'perms_list': perms_list})
