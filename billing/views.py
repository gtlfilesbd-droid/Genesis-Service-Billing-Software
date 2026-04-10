from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
from django.db import transaction
from django.db.models import Prefetch

from .models import Bill, BillItem, BillingBank, BillingTaxSettings
from .invoice_number import build_invoice_number_base
from .bill_period import compute_bill_period_window, format_bill_period_line
from clients.models import Client, Agreement, Service
from accounts.models import UserProfile
from datetime import date, timedelta

from django.utils.dateparse import parse_date


def _bill_form_extra_context(bill=None):
    s = BillingTaxSettings.get_solo()
    banks = list(BillingBank.objects.all().order_by('-is_default', 'label'))
    payload = [
        {
            'id': b.pk,
            'label': b.label,
            'bank_name': b.bank_name or '',
            'beneficiary': b.beneficiary or '',
            'bank_branch': b.bank_branch or '',
            'bank_address_line1': b.bank_address_line1 or '',
            'bank_address_line2': b.bank_address_line2 or '',
            'account_number': b.account_number or '',
            'swift_code': b.swift_code or '',
            'branch_routing_code': b.branch_routing_code or '',
            'bin_number': b.bin_number or '',
            'tin_number': b.tin_number or '',
        }
        for b in banks
    ]
    initial = None
    if bill and getattr(bill, 'billing_bank_id', None):
        initial = bill.billing_bank_id
    else:
        for b in banks:
            if b.is_default:
                initial = b.pk
                break
    return {
        'tax_vat_percent': float(s.vat_percent),
        'tax_ait_percent': float(s.ait_percent),
        'billing_banks': banks,
        'billing_banks_payload': payload,
        'initial_billing_bank_id': initial,
    }


def _apply_billing_bank_from_post(request, bill):
    raw = request.POST.get('billing_bank')
    bb = None
    if raw is not None and str(raw).strip() != '':
        bb = BillingBank.objects.filter(pk=raw).first()
    elif raw is not None and str(raw).strip() == '':
        bb = None
    else:
        bb = BillingBank.get_default()
    bill.billing_bank = bb
    if bb:
        bb.copy_to_bill(bill)
    else:
        BillingBank.clear_bill_bank_fields(bill)


def get_profile(user):
    try:
        return user.profile
    except UserProfile.DoesNotExist:
        return UserProfile.objects.create(user=user)


def _validate_bill_invoice_prerequisites(client_id, agreement_id):
    if not client_id or not agreement_id:
        return False, 'Please select a client and an agreement.'
    ag = Agreement.objects.select_related('agreement_with').filter(pk=agreement_id).first()
    if not ag:
        return False, 'Invalid agreement.'
    if not ag.agreement_with_id:
        return False, 'Selected agreement must have an Agreement With company.'
    cl = Client.objects.filter(pk=client_id).first()
    if not cl:
        return False, 'Invalid client.'
    if not (cl.short_form or '').strip():
        return False, 'Client must have a short form before creating a bill.'
    return True, None


def _save_bill_from_post(request, bill):
    with transaction.atomic():
        bill.client_id = request.POST.get('client')
        bill.agreement_id = request.POST.get('agreement') or None
        inv_raw = request.POST.get('invoice_date')
        if inv_raw:
            bill.invoice_date = parse_date(inv_raw) or date.today()
        else:
            bill.invoice_date = date.today()
        inv = bill.invoice_date

        if bill.agreement_id:
            try:
                ag = Agreement.objects.prefetch_related(
                    Prefetch('services', queryset=Service.objects.filter(is_active=True).order_by('id'))
                ).get(pk=bill.agreement_id)
                bill.po_date = ag.start_date
                bf, bt = compute_bill_period_window(ag, inv)
                bill.bill_period_from = bf
                bill.bill_period_to = bt
                bill.bill_period = format_bill_period_line(bf, bt)
            except Agreement.DoesNotExist:
                bill.po_date = None
                bill.bill_period_from = None
                bill.bill_period_to = None
                bill.bill_period = ''
        else:
            bill.po_date = None
            bill.bill_period_from = None
            bill.bill_period_to = None
            bill.bill_period = ''
        bill.service_period = ''
        if 'project_value_yearly' in request.POST:
            bill.project_value_yearly = request.POST.get('project_value_yearly') or 0
        bill.remark = request.POST.get('remark', '')
        _apply_billing_bank_from_post(request, bill)
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
        bill.save(
            update_fields=[
                'subtotal',
                'project_base_value',
                'vat_rate_percent',
                'ait_rate_percent',
                'vat_amount',
                'ait_amount',
                'excluding_vat_ait',
                'total_in_bdt',
            ]
        )
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
        bills = bills.filter(bill_number__icontains=search) | bills.filter(
            client__name__icontains=search
        ) | bills.filter(invoice_number__icontains=search)
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
        elif not request.POST.get('agreement'):
            messages.error(request, 'Please select an agreement.')
        else:
            ok, err = _validate_bill_invoice_prerequisites(
                request.POST.get('client'), request.POST.get('agreement')
            )
            if not ok:
                messages.error(request, err)
            else:
                bill = Bill()
                _save_bill_from_post(request, bill)
                inv = bill.invoice_number or bill.bill_number
                messages.success(request, f'Invoice {inv} created successfully.')
                return redirect('bill_detail', pk=bill.pk)
    ctx = {
        'clients': clients, 'profile': profile,
        'today': date.today(),
        'status_choices': Bill._meta.get_field('status').choices,
        'action': 'Create',
    }
    ctx.update(_bill_form_extra_context())
    return render(request, 'bills/bill_form.html', ctx)


@login_required
def bill_detail(request, pk):
    bill = get_object_or_404(
        Bill.objects.select_related('client', 'agreement', 'agreement__agreement_with'),
        pk=pk,
    )
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
        if not request.POST.get('agreement'):
            messages.error(request, 'Please select an agreement.')
            return redirect('bill_edit', pk=pk)
        ok, err = _validate_bill_invoice_prerequisites(
            request.POST.get('client'), request.POST.get('agreement')
        )
        if not ok:
            messages.error(request, err)
            ctx = {
                'bill': bill, 'clients': clients, 'profile': profile,
                'today': date.today(),
                'status_choices': Bill._meta.get_field('status').choices,
                'action': 'Edit',
            }
            ctx.update(_bill_form_extra_context(bill))
            return render(request, 'bills/bill_form.html', ctx)
        _save_bill_from_post(request, bill)
        inv = bill.invoice_number or bill.bill_number
        messages.success(request, f'Invoice {inv} updated successfully.')
        return redirect('bill_detail', pk=pk)
    ctx = {
        'bill': bill, 'clients': clients, 'profile': profile,
        'today': date.today(),
        'status_choices': Bill._meta.get_field('status').choices,
        'action': 'Edit',
    }
    ctx.update(_bill_form_extra_context(bill))
    return render(request, 'bills/bill_form.html', ctx)


@login_required
def get_client_agreements(request, client_id):
    client = get_object_or_404(Client, pk=client_id)
    agreements = client.agreements.filter(is_active=True).prefetch_related(
        Prefetch('services', queryset=Service.objects.filter(is_active=True).order_by('id'))
    ).order_by('-start_date', '-id')
    payload = [{
        'id': a.id,
        'title': a.title,
        'start_date': a.start_date.isoformat() if a.start_date else '',
        'end_date': a.end_date.isoformat() if a.end_date else '',
    } for a in agreements]
    return JsonResponse({'agreements': payload})


@login_required
def preview_bill_period(request):
    agreement_id = request.GET.get('agreement')
    inv_raw = request.GET.get('invoice_date')
    if not agreement_id:
        return JsonResponse({'bill_period_from': '', 'bill_period_to': '', 'summary': ''})
    inv = parse_date(inv_raw) if inv_raw else date.today()
    if inv is None:
        inv = date.today()
    ag = get_object_or_404(
        Agreement.objects.prefetch_related(
            Prefetch('services', queryset=Service.objects.filter(is_active=True).order_by('id'))
        ),
        pk=agreement_id,
    )
    bf, bt = compute_bill_period_window(ag, inv)
    return JsonResponse({
        'bill_period_from': bf.isoformat() if bf else '',
        'bill_period_to': bt.isoformat() if bt else '',
        'summary': format_bill_period_line(bf, bt),
    })


@login_required
def preview_invoice_number(request):
    client_id = request.GET.get('client')
    agreement_id = request.GET.get('agreement')
    invoice_date = request.GET.get('invoice_date')
    if not client_id or not agreement_id or not invoice_date:
        return JsonResponse({'preview': '', 'error': None})
    ok, err = _validate_bill_invoice_prerequisites(client_id, agreement_id)
    if not ok:
        return JsonResponse({'preview': '', 'error': err})
    try:
        ag = Agreement.objects.select_related('agreement_with').get(pk=agreement_id)
        client = Client.objects.get(pk=client_id)
        preview = build_invoice_number_base(ag, client, invoice_date)
    except (Agreement.DoesNotExist, Client.DoesNotExist, ValueError) as e:
        return JsonResponse({'preview': '', 'error': str(e) or 'Could not build invoice number.'})
    return JsonResponse({'preview': preview, 'error': None})


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
        fname = (bill.invoice_number or bill.bill_number).replace('/', '-')
        response['Content-Disposition'] = f'attachment; filename="Invoice-{fname}.pdf"'
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
        inv_disp = bill.invoice_number or bill.bill_number
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = f"Inv-{inv_disp}"[:31]
        blue = PatternFill('solid', fgColor='1565C0')
        wf = Font(bold=True, color='FFFFFF')
        bf = Font(bold=True)

        ws.merge_cells('A1:F1')
        ws['A1'] = 'INVOICE'
        ws['A1'].font = Font(size=18, bold=True, color='1565C0')
        ws['A1'].alignment = Alignment(horizontal='center')
        ws.merge_cells('A2:F2')
        ws['A2'] = f'Invoice #: {inv_disp}'
        ws['A2'].alignment = Alignment(horizontal='center')
        ws.append([])
        ws.append(['Bill To:', '', '', 'Invoice Details:', '', ''])
        ws['A4'].font = bf; ws['D4'].font = bf
        ws.append([bill.client.name, '', '', 'Invoice Date:', str(bill.invoice_date), ''])
        ws.append([bill.client.address, '', '', 'PO Date:', str(bill.po_date or ''), ''])
        if bill.bill_period_from or bill.bill_period_to:
            ws.append([bill.client.phone or '', '', '', 'Bill From:', str(bill.bill_period_from or ''), ''])
            ws.append([bill.client.email or '', '', '', 'Bill To:', str(bill.bill_period_to or ''), ''])
        else:
            ws.append([bill.client.phone or '', '', '', 'Bill Period:', bill.bill_period or '', ''])
            ws.append([bill.client.email or '', '', '', '', '', ''])
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
        ws.append(['', '', '', '', 'Items Subtotal:', float(bill.subtotal)])
        ws.append([])
        ws.append(['VAT & AIT Details']); ws[f'A{ws.max_row}'].font = bf
        ws.append(['Base Value (BDT):', '', '', '', '', float(bill.project_base_value)])
        ws.append([f'VAT ({bill.vat_rate_percent}%):', '', '', '', '', float(bill.vat_amount)])
        ws.append([f'AIT ({bill.ait_rate_percent}%):', '', '', '', '', float(bill.ait_amount)])
        ws.append(['Total VAT & AIT:', '', '', '', '', float(bill.excluding_vat_ait)])
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
        fname = (bill.invoice_number or bill.bill_number).replace('/', '-')
        response['Content-Disposition'] = f'attachment; filename="Invoice-{fname}.xlsx"'
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
    inv = bill.invoice_number or bill.bill_number
    messages.success(request, f'Invoice {inv} marked as paid.')
    return redirect('bill_detail', pk=pk)
