from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
from django.db import transaction
from .models import Bill, BillItem
from clients.models import Client, Agreement, Service
from accounts.models import UserProfile
from datetime import date, timedelta


def get_profile(user):
    try:
        return user.profile
    except UserProfile.DoesNotExist:
        return UserProfile.objects.create(user=user)


def _save_bill_from_post(request, bill):
    with transaction.atomic():
        bill.client_id = request.POST.get('client')
        bill.invoice_date = request.POST.get('invoice_date') or date.today()
        bill.po_date = request.POST.get('po_date') or None
        bill.bill_period = request.POST.get('bill_period', '')
        bill.service_period = request.POST.get('service_period', '')
        bill.project_value_yearly = request.POST.get('project_value_yearly') or 0
        bill.project_base_value = request.POST.get('project_base_value') or 0
        bill.excluding_vat_ait = request.POST.get('excluding_vat_ait') or 0
        bill.total_in_bdt = request.POST.get('total_in_bdt') or 0
        bill.remark = request.POST.get('remark', '')
        bill.bank_name = request.POST.get('bank_name', '')
        bill.beneficiary = request.POST.get('beneficiary', '')
        bill.bank_branch = request.POST.get('bank_branch', '')
        bill.bank_address_line1 = request.POST.get('bank_address_line1', '')
        bill.bank_address_line2 = request.POST.get('bank_address_line2', '')
        bill.account_number = request.POST.get('account_number', '')
        bill.swift_code = request.POST.get('swift_code', '')
        bill.branch_routing_code = request.POST.get('branch_routing_code', '')
        bill.bin_number = request.POST.get('bin_number', '')
        bill.tin_number = request.POST.get('tin_number', '')
        bill.status = request.POST.get('status', 'draft')
        if not bill.created_by_id:
            bill.created_by = request.user
        bill.save()

        bill.items.all().delete()
        descriptions = request.POST.getlist('item_description[]')
        quantities = request.POST.getlist('item_quantity[]')
        units = request.POST.getlist('item_unit[]')
        prices = request.POST.getlist('item_price[]')

        for i in range(len(descriptions)):
            desc = descriptions[i].strip() if i < len(descriptions) else ""
            if not desc:
                continue
            try:
                qty = float(quantities[i]) if i < len(quantities) and quantities[i] else 1
            except (ValueError, TypeError):
                qty = 1
            unit = units[i] if i < len(units) else ""
            try:
                price = float(prices[i]) if i < len(prices) and prices[i] else 0
            except (ValueError, TypeError):
                price = 0
            BillItem.objects.create(
                bill=bill,
                description=desc,
                quantity=qty,
                unit=unit,
                unit_price=price,
            )
        bill.calculate_totals()
        bill.save(update_fields=['subtotal'])
    return bill


@login_required
def bill_list(request):
    bills = Bill.objects.select_related('client').all()
    status_filter = request.GET.get('status', '')
    client_filter = request.GET.get('client', '')
    search = request.GET.get('search', '')
    if status_filter:
        bills = bills.filter(status=status_filter)
    if client_filter:
        bills = bills.filter(client_id=client_filter)
    if search:
        bills = bills.filter(bill_number__icontains=search) | bills.filter(client__name__icontains=search)
    paginator = Paginator(bills, 10)
    bills_page = paginator.get_page(request.GET.get('page'))
    profile = get_profile(request.user)
    return render(request, 'bills/bill_list.html', {
        'bills': bills_page,
        'clients': Client.objects.filter(is_active=True),
        'status_filter': status_filter,
        'client_filter': client_filter,
        'search': search,
        'profile': profile,
        'status_choices': Bill._meta.get_field('status').choices,
    })


@login_required
def bill_create(request):
    profile = get_profile(request.user)
    if not profile.can_generate_bill and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to generate bills.')
        return redirect('bill_list')
    clients = Client.objects.filter(is_active=True)
    if request.method == 'POST':
        if not request.POST.get('client'):
            messages.error(request, 'Please select a client.')
        else:
            bill = Bill()
            _save_bill_from_post(request, bill)
            messages.success(request, f'Bill #{bill.bill_number} created successfully.')
            return redirect('bill_detail', pk=bill.pk)
    return render(request, 'bills/bill_form.html', {
        'clients': clients, 'profile': profile,
        'today': date.today(),
        'status_choices': Bill._meta.get_field('status').choices,
        'action': 'Create',
    })


@login_required
def bill_detail(request, pk):
    bill = get_object_or_404(Bill, pk=pk)
    profile = get_profile(request.user)
    return render(request, 'bills/bill_detail.html', {'bill': bill, 'profile': profile})


@login_required
def bill_edit(request, pk):
    profile = get_profile(request.user)
    bill = get_object_or_404(Bill, pk=pk)
    if not profile.can_edit_bill and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to edit bills.')
        return redirect('bill_detail', pk=pk)
    clients = Client.objects.filter(is_active=True)
    if request.method == 'POST':
        _save_bill_from_post(request, bill)
        messages.success(request, f'Bill #{bill.bill_number} updated successfully.')
        return redirect('bill_detail', pk=pk)
    return render(request, 'bills/bill_form.html', {
        'bill': bill, 'clients': clients, 'profile': profile,
        'today': date.today(),
        'status_choices': Bill._meta.get_field('status').choices,
        'action': 'Edit',
    })


@login_required
def get_client_agreements(request, client_id):
    client = get_object_or_404(Client, pk=client_id)
    agreements = client.agreements.filter(is_active=True).values('id', 'title')
    return JsonResponse({'agreements': list(agreements)})


@login_required
def get_agreement_services(request, agreement_id):
    agreement = get_object_or_404(Agreement, pk=agreement_id)
    services = [{'id': s.id, 'name': s.name, 'service_type': s.get_service_type_display(),
                 'charge': str(s.charge), 'description': s.description or ''}
                for s in agreement.services.filter(is_active=True)]
    return JsonResponse({'services': services, 'agreement_title': agreement.title})


@login_required
def bill_pdf(request, pk):
    from django.template.loader import render_to_string
    try:
        import weasyprint
        bill = get_object_or_404(Bill, pk=pk)
        html_string = render_to_string('bills/bill_pdf.html', {'bill': bill})
        pdf_file = weasyprint.HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()
        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Invoice-{bill.bill_number}.pdf"'
        return response
    except ImportError:
        messages.error(request, 'WeasyPrint is not installed.')
        return redirect('bill_detail', pk=pk)


@login_required
def bill_print(request, pk):
    bill = get_object_or_404(Bill, pk=pk)
    return render(request, 'bills/bill_pdf.html', {'bill': bill, 'print_mode': True})


@login_required
def bill_excel(request, pk):
    try:
        import openpyxl
        from openpyxl.styles import Font, Alignment, PatternFill
        bill = get_object_or_404(Bill, pk=pk)
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = f"Invoice-{bill.bill_number}"
        blue = PatternFill('solid', fgColor='1565C0')
        wf = Font(bold=True, color='FFFFFF')
        bf = Font(bold=True)

        ws.merge_cells('A1:F1')
        ws['A1'] = 'INVOICE'
        ws['A1'].font = Font(size=18, bold=True, color='1565C0')
        ws['A1'].alignment = Alignment(horizontal='center')
        ws.merge_cells('A2:F2')
        ws['A2'] = f'Invoice #: {bill.bill_number}'
        ws['A2'].alignment = Alignment(horizontal='center')
        ws.append([])
        ws.append(['Bill To:', '', '', 'Invoice Details:', '', ''])
        ws['A4'].font = bf; ws['D4'].font = bf
        ws.append([bill.client.name, '', '', 'Invoice Date:', str(bill.invoice_date), ''])
        ws.append([bill.client.address, '', '', 'PO Date:', str(bill.po_date or ''), ''])
        ws.append([bill.client.phone or '', '', '', 'Bill Period:', bill.bill_period or '', ''])
        ws.append([bill.client.email or '', '', '', 'Service Period:', bill.service_period or '', ''])
        ws.append([])
        headers = ['#', 'Description', 'Qty', 'Unit', 'Unit Price (BDT)', 'Amount (BDT)']
        ws.append(headers)
        hr = ws.max_row
        for col in range(1, 7):
            c = ws.cell(row=hr, column=col)
            c.fill = blue; c.font = wf; c.alignment = Alignment(horizontal='center')
        for idx, item in enumerate(bill.items.all(), 1):
            ws.append([idx, item.description, float(item.quantity), item.unit or '', float(item.unit_price), float(item.amount)])
        ws.append([])
        ws.append(['', '', '', '', 'Subtotal:', float(bill.subtotal)])
        ws.append([])
        ws.append(['Financial Summary']); ws[f'A{ws.max_row}'].font = bf
        ws.append(['Project Value Yearly:', '', '', '', '', float(bill.project_value_yearly)])
        ws.append(['Project Base Value:', '', '', '', '', float(bill.project_base_value)])
        ws.append(['Excluding VAT & AIT:', '', '', '', '', float(bill.excluding_vat_ait)])
        ws.append(['Total In BDT:', '', '', '', '', float(bill.total_in_bdt)])
        if bill.bank_name:
            ws.append([])
            ws.append(['Bank Information']); ws[f'A{ws.max_row}'].font = bf
            ws.append(['Bank Name:', bill.bank_name])
            ws.append(['Beneficiary:', bill.beneficiary or ''])
            ws.append(['Branch:', bill.bank_branch or ''])
            ws.append(['Address Line 1:', bill.bank_address_line1 or ''])
            ws.append(['Address Line 2:', bill.bank_address_line2 or ''])
            ws.append(['Account No:', bill.account_number or ''])
            ws.append(['Swift Code:', bill.swift_code or ''])
            ws.append(['Branch Code (Routing):', bill.branch_routing_code or ''])
            ws.append(['BIN:', bill.bin_number or ''])
            ws.append(['TIN:', bill.tin_number or ''])
        for col, w in zip('ABCDEF', [28, 40, 10, 14, 22, 22]):
            ws.column_dimensions[col].width = w
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="Invoice-{bill.bill_number}.xlsx"'
        wb.save(response)
        return response
    except ImportError:
        messages.error(request, 'openpyxl not installed.')
        return redirect('bill_detail', pk=pk)


@login_required
def mark_paid(request, pk):
    profile = get_profile(request.user)
    if not profile.can_edit_bill and not request.user.is_superuser:
        messages.error(request, 'Permission denied.')
        return redirect('bill_detail', pk=pk)
    bill = get_object_or_404(Bill, pk=pk)
    bill.status = 'paid'
    bill.payment_date = date.today()
    bill.save()
    messages.success(request, f'Bill #{bill.bill_number} marked as paid.')
    return redirect('bill_detail', pk=pk)
