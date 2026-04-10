from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Sum, Count, Q
from billing.models import Bill
from clients.models import Client
from accounts.models import UserProfile
from datetime import date, timedelta
from django.utils import timezone
import json


def get_profile(user):
    try:
        return user.profile
    except UserProfile.DoesNotExist:
        return UserProfile.objects.create(user=user)


@login_required
def report_dashboard(request):
    profile = get_profile(request.user)
    if not profile.can_view_reports and not request.user.is_superuser:
        from django.contrib import messages
        messages.error(request, 'You do not have permission to view reports.')
        from django.shortcuts import redirect
        return redirect('dashboard')

    today = date.today()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))

    # Monthly revenue for chart (last 12 months)
    monthly_data = []
    for i in range(11, -1, -1):
        d = today.replace(day=1) - timedelta(days=i * 30)
        label = d.strftime('%b %Y')
        total = Bill.objects.filter(
            status='paid',
            invoice_date__year=d.year,
            invoice_date__month=d.month
        ).aggregate(t=Sum('total_in_bdt'))['t'] or 0
        monthly_data.append({'label': label, 'total': float(total)})

    # Status breakdown
    status_data = {
        'paid': Bill.objects.filter(status='paid').count(),
        'unpaid': Bill.objects.filter(status='unpaid').count(),
        'overdue': Bill.objects.filter(status='overdue').count(),
        'draft': Bill.objects.filter(status='draft').count(),
    }

    # Top clients
    top_clients = Bill.objects.filter(status='paid').values(
        'client__name'
    ).annotate(total=Sum('total_in_bdt')).order_by('-total')[:5]

    # Summary
    total_revenue = Bill.objects.filter(status='paid').aggregate(t=Sum('total_in_bdt'))['t'] or 0
    pending_amount = Bill.objects.filter(status__in=['unpaid', 'overdue']).aggregate(t=Sum('total_in_bdt'))['t'] or 0
    this_month_revenue = Bill.objects.filter(
        status='paid', invoice_date__year=today.year, invoice_date__month=today.month
    ).aggregate(t=Sum('total_in_bdt'))['t'] or 0

    context = {
        'profile': profile,
        'monthly_data_json': json.dumps(monthly_data),
        'status_data_json': json.dumps(status_data),
        'top_clients': top_clients,
        'total_revenue': total_revenue,
        'pending_amount': pending_amount,
        'this_month_revenue': this_month_revenue,
        'total_clients': Client.objects.filter(is_active=True).count(),
        'total_bills': Bill.objects.count(),
        'year': year,
    }
    return render(request, 'reports/report_dashboard.html', context)


@login_required
def export_bills_csv(request):
    profile = get_profile(request.user)
    if not profile.can_export_reports and not request.user.is_superuser:
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.error(request, 'Permission denied.')
        return redirect('report_dashboard')

    import csv
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="bills-report-{date.today()}.csv"'
    writer = csv.writer(response)
    writer.writerow(['Bill Number', 'Client', 'Bill Date', 'Due Date',
                     'Period From', 'Period To', 'Subtotal', 'Discount',
                     'Total VAT & AIT', 'Total', 'Status', 'Payment Date'])

    bills = Bill.objects.select_related('client').all()
    status_filter = request.GET.get('status', '')
    if status_filter:
        bills = bills.filter(status=status_filter)

    for bill in bills:
        writer.writerow([
            bill.bill_number, bill.client.name, bill.invoice_date,
            bill.po_date or '', bill.bill_period or '', bill.service_period or '',
            bill.subtotal, 0, bill.excluding_vat_ait,
            bill.total_in_bdt, bill.get_status_display(), bill.payment_date or ''
        ])
    return response


@login_required
def export_bills_excel(request):
    profile = get_profile(request.user)
    if not profile.can_export_reports and not request.user.is_superuser:
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.error(request, 'Permission denied.')
        return redirect('report_dashboard')

    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Bills Report"

        headers = ['Bill Number', 'Client', 'Bill Date', 'Due Date',
                   'Period From', 'Period To', 'Subtotal', 'Discount',
                   'Total VAT & AIT', 'Total', 'Status', 'Payment Date']
        ws.append(headers)

        hfill = PatternFill('solid', fgColor='1565C0')
        hfont = Font(bold=True, color='FFFFFF')
        for col in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col)
            cell.fill = hfill
            cell.font = hfont
            cell.alignment = Alignment(horizontal='center')

        bills = Bill.objects.select_related('client').all()
        for bill in bills:
            ws.append([
                bill.bill_number, bill.client.name, str(bill.invoice_date),
                str(bill.po_date) if bill.po_date else '',
                str(bill.bill_period or ''),
                str(bill.service_period or ''),
                float(bill.subtotal), 0.0, float(bill.excluding_vat_ait),
                float(bill.total_in_bdt), bill.get_status_display(),
                str(bill.payment_date) if bill.payment_date else ''
            ])

        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width = 18

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="bills-report-{date.today()}.xlsx"'
        wb.save(response)
        return response
    except ImportError:
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.error(request, 'openpyxl not installed.')
        return redirect('report_dashboard')
