"""
Create missing Bills for each mature billing period of active agreements.
Idempotent: (agreement, bill_period_from, bill_period_to) must not already exist.
"""
from __future__ import annotations

import calendar
from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from clients.models import Agreement
from .models import Bill, BillItem, BillingBank, BillingTaxSettings
from .bill_period import format_bill_period_line
from .period_schedule import iter_mature_periods_for_agreement


def _agreement_eligible(ag) -> bool:
    if not ag.is_active or not ag.start_date:
        return False
    if not ag.agreement_with_id:
        return False
    if not ag.client_id or not ag.client.is_active:
        return False
    if not (ag.client.short_form or '').strip():
        return False
    return ag.services.filter(is_active=True).exists()


def _create_auto_bill(ag: Agreement, period_from, period_to, invoice_date) -> Bill | None:
    if Bill.objects.filter(
        agreement_id=ag.pk,
        bill_period_from=period_from,
        bill_period_to=period_to,
    ).exists():
        return None

    tax = BillingTaxSettings.get_solo()
    co = ag.agreement_with if ag.agreement_with_id else None
    bb = BillingBank.get_default_for_company(co) if co else None

    with transaction.atomic():
        bill = Bill(
            client_id=ag.client_id,
            agreement_id=ag.pk,
            invoice_date=invoice_date,
            po_date=ag.start_date,
            bill_period_from=period_from,
            bill_period_to=period_to,
            bill_period=format_bill_period_line(period_from, period_to),
            status='pending',
            auto_generated=True,
            vat_rate_percent=tax.vat_percent,
            ait_rate_percent=tax.ait_percent,
        )
        if bb:
            bill.billing_bank = bb
            bb.copy_to_bill(bill)
        bill.save()

        for svc in ag.services.filter(is_active=True).order_by('id'):
            BillItem.objects.create(
                bill=bill,
                description=(svc.name or 'Service').strip() or 'Service',
                quantity=Decimal('1'),
                unit='Job',
                unit_price=svc.charge or Decimal('0'),
            )

        bill.calculate_totals()
        bill.save(
            update_fields=[
                'subtotal',
                'project_base_value',
                'vat_amount',
                'ait_amount',
                'excluding_vat_ait',
                'total_in_bdt',
            ]
        )
        return bill


def sync_automatic_bills() -> int:
    """Returns number of new bills created."""
    today = timezone.localdate()
    created = 0

    agreements = (
        Agreement.objects.filter(is_active=True)
        .select_related('client', 'agreement_with')
        .prefetch_related('services')
    )

    for ag in agreements:
        if not _agreement_eligible(ag):
            continue
        for pf, pt, inv_date in iter_mature_periods_for_agreement(ag, today):
            b = _create_auto_bill(ag, pf, pt, inv_date)
            if b is not None:
                created += 1
    return created


def refresh_pending_maturity_dates() -> int:
    """
    Align invoice_date for pending bills to (bill_period_to + 1 day) when set.
    Updates invoice_number via full save. Returns count updated.
    """
    updated = 0
    for bill in Bill.objects.filter(
        status='pending',
        auto_generated=True,
        bill_period_to__isnull=False,
    ).select_related('agreement'):
        expected = bill.bill_period_to + timedelta(days=1)
        if bill.invoice_date != expected:
            bill.invoice_date = expected
            bill.save()
            updated += 1
    return updated


def group_bills_by_invoice_month(bills):
    """
    Group bills by (invoice_date year, month). Newest month first.
    `bills` may be a QuerySet (will be evaluated ordered by -invoice_date, -id).
    """
    if hasattr(bills, 'order_by'):
        bills = list(bills.order_by('-invoice_date', '-id'))

    buckets: dict[tuple[int, int], list] = {}
    for b in bills:
        key = (b.invoice_date.year, b.invoice_date.month)
        buckets.setdefault(key, []).append(b)

    def sort_key(k):
        return (k[0], k[1])

    out = []
    for y, m in sorted(buckets.keys(), key=sort_key, reverse=True):
        label = f'{calendar.month_name[m]} {y}'
        out.append({'year': y, 'month': m, 'label': label, 'bills': buckets[(y, m)]})
    return out


def year_choices_for_filter(bills_qs):
    """Years spanning invoice_date for filter dropdown."""
    from django.db.models import Min, Max

    agg = bills_qs.aggregate(mi=Min('invoice_date'), ma=Max('invoice_date'))
    if not agg['mi'] or not agg['ma']:
        y = timezone.localdate().year
        return list(range(y, y - 6, -1))
    y1, y2 = agg['mi'].year, agg['ma'].year
    return list(range(y2, y1 - 1, -1))


def sync_billing_queues():
    """Create missing period bills and refresh pending invoice dates from maturity."""
    sync_automatic_bills()
    refresh_pending_maturity_dates()
