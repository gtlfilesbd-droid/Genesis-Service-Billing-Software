from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from clients.models import Client
from billing.models import Bill
from datetime import datetime, timedelta
from django.utils import timezone


@login_required
def dashboard(request):
    today = timezone.now().date()
    this_month_start = today.replace(day=1)

    total_clients = Client.objects.filter(is_active=True).count()
    total_bills = Bill.objects.count()
    paid_bills = Bill.objects.filter(status='paid').count()
    unpaid_bills = Bill.objects.filter(status='unpaid').count()
    overdue_bills = Bill.objects.filter(status='overdue').count()

    monthly_revenue = Bill.objects.filter(
        status='paid',
        invoice_date__gte=this_month_start
    ).aggregate(total=Sum('total_in_bdt'))['total'] or 0

    total_revenue = Bill.objects.filter(
        status='paid'
    ).aggregate(total=Sum('total_in_bdt'))['total'] or 0

    pending_amount = Bill.objects.filter(
        status__in=['unpaid', 'overdue']
    ).aggregate(total=Sum('total_in_bdt'))['total'] or 0

    recent_bills = Bill.objects.select_related('client').order_by('-created_at')[:5]
    recent_clients = Client.objects.order_by('-created_at')[:5]

    overdue_list = Bill.objects.filter(
        status='overdue'
    ).select_related('client').order_by('invoice_date')[:5]

    context = {
        'total_clients': total_clients,
        'total_bills': total_bills,
        'paid_bills': paid_bills,
        'unpaid_bills': unpaid_bills,
        'overdue_bills': overdue_bills,
        'monthly_revenue': monthly_revenue,
        'total_revenue': total_revenue,
        'pending_amount': pending_amount,
        'recent_bills': recent_bills,
        'recent_clients': recent_clients,
        'overdue_list': overdue_list,
    }
    return render(request, 'dashboard/dashboard.html', context)
