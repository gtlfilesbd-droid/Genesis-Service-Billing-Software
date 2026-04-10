"""
Shared logic for auto-generated invoice numbers:
{AgreementWith.short}/{DDMMMYY}/{Client.short}/{agreement title initials}
"""
import re
from datetime import date

from django.utils.dateparse import parse_date


def sanitize_segment(value, default='X'):
    if value is None:
        return default
    t = re.sub(r'[^A-Za-z0-9]', '', str(value).strip())
    return t.upper() if t else default


def agreement_title_initials(title):
    if not title or not str(title).strip():
        return 'X'
    words = re.findall(r'[A-Za-z0-9]+', str(title))
    if not words:
        return 'X'
    return ''.join(w[0].upper() for w in words)


def format_invoice_date_segment(d):
    if d is None:
        d = date.today()
    if isinstance(d, str):
        parsed = parse_date(d)
        d = parsed if parsed else date.today()
    return d.strftime('%d%b%y').upper()


def build_invoice_number_base(agreement, client, invoice_date):
    aw = getattr(agreement, 'agreement_with', None)
    if not aw:
        raise ValueError('Agreement With company is required.')
    co = sanitize_segment(aw.short_form)
    cl = sanitize_segment(getattr(client, 'short_form', None))
    dt = format_invoice_date_segment(invoice_date)
    ti = agreement_title_initials(agreement.title)
    return f'{co}/{dt}/{cl}/{ti}'


def allocate_invoice_number(base, exclude_bill_pk=None):
    from .models import Bill

    qs = Bill.objects.filter(invoice_number=base)
    if exclude_bill_pk:
        qs = qs.exclude(pk=exclude_bill_pk)
    if not qs.exists():
        return base
    n = 2
    while True:
        candidate = f'{base}-{n}'
        qs2 = Bill.objects.filter(invoice_number=candidate)
        if exclude_bill_pk:
            qs2 = qs2.exclude(pk=exclude_bill_pk)
        if not qs2.exists():
            return candidate
        n += 1
