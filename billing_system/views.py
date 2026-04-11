from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from clients.models import Client
from billing.models import Bill
from billing.sync_auto_bills import sync_billing_queues
from accounts.models import UserProfile
from django.utils import timezone


def _dashboard_profile(user):
    try:
        return user.profile
    except UserProfile.DoesNotExist:
        return UserProfile.objects.create(user=user)


@login_required
def dashboard(request):
    profile = _dashboard_profile(request.user)
    if not profile.can_access_dashboard and not request.user.is_superuser:
        messages.info(request, 'You do not have access to the dashboard. Use the menu to open Bills or other pages.')
        return redirect('bill_list')

    sync_billing_queues()
    today = timezone.now().date()
    this_month_start = today.replace(day=1)

    total_clients = Client.objects.filter(is_active=True).count()
    total_bills = Bill.objects.count()
    paid_bills = Bill.objects.filter(status='paid').count()
    pending_queue_count = Bill.objects.filter(
        status='pending',
        bill_period_to__isnull=False,
        bill_period_to__lt=today,
    ).count()
    submitted_queue_count = Bill.objects.filter(status='submitted').count()

    monthly_revenue = Bill.objects.filter(
        status='paid',
        invoice_date__gte=this_month_start
    ).aggregate(total=Sum('total_in_bdt'))['total'] or 0

    total_revenue = Bill.objects.filter(
        status='paid'
    ).aggregate(total=Sum('total_in_bdt'))['total'] or 0

    outstanding_amount = Bill.objects.filter(
        status__in=['pending', 'submitted']
    ).aggregate(total=Sum('total_in_bdt'))['total'] or 0

    recent_bills = Bill.objects.select_related('client').order_by('-created_at')[:5]
    recent_clients = Client.objects.order_by('-created_at')[:5]

    submitted_watch_list = Bill.objects.filter(
        status='submitted'
    ).select_related('client').order_by('invoice_date')[:5]

    context = {
        'profile': profile,
        'total_clients': total_clients,
        'total_bills': total_bills,
        'paid_bills': paid_bills,
        'pending_queue_count': pending_queue_count,
        'submitted_queue_count': submitted_queue_count,
        'monthly_revenue': monthly_revenue,
        'total_revenue': total_revenue,
        'outstanding_amount': outstanding_amount,
        'recent_bills': recent_bills,
        'recent_clients': recent_clients,
        'submitted_watch_list': submitted_watch_list,
    }
    return render(request, 'dashboard/dashboard.html', context)
