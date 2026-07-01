"""
Bill From / Bill To + auto-bill periods (monthly): **anniversary months** from
agreement start_date.

  Period k:  pf = add_months(start, k)
             pt = add_months(start, k+1) - 1 day
  Mature / Invoice date = pt + 1 day = add_months(start, k+1)

  Example  start 15 Mar 2026:
    period 0 → 15 Mar – 14 Apr 2026,  mature 15 Apr 2026
    period 1 → 15 Apr – 14 May 2026,  mature 15 May 2026

  Example  start 1 Apr 2026:
    period 0 → 1 Apr – 30 Apr 2026,   mature 1 May 2026

  AMC: 15 Mar 2026 – 15 Mar 2027 = 12 complete periods (pt ≤ end_date) = 12 × charge.

Quarterly / semi-annual / annual: same anniversary blocks as AMC
  (3 / 6 / 12 months from start_date, same formula with months_per_period).

One-time: agreement start_date through end_date (or start if open-ended).

If multiple active services exist, the first by id sets the cadence.
"""
from datetime import date, timedelta
import calendar

from django.utils.dateparse import parse_date


def _one_time_range(agreement) -> tuple[date, date]:
    s = agreement.start_date
    if not s:
        return None, None  # type: ignore
    e = agreement.end_date or s
    return s, e


def add_months(d: date, months: int) -> date:
    """Add whole calendar months; day clamped to last day of target month (e.g. 31 Jan +1 → 28/29 Feb)."""
    y = d.year + (d.month - 1 + months) // 12
    m = (d.month - 1 + months) % 12 + 1
    last = calendar.monthrange(y, m)[1]
    day = min(d.day, last)
    return date(y, m, day)


def count_anniversary_periods(start: date, end: date, months_per_period: int) -> int:
    """
    Count completed periods of fixed `months_per_period` months, starting at `start`.

    For period k:
      Bill To = add_months(start, (k+1) * months_per_period) - 1 day
    Count while Bill To <= end.
    """
    if not start or not end or end < start:
        return 0
    if not months_per_period or months_per_period < 1:
        return 0
    n = 0
    k = 0
    while k < 5000:
        pt = add_months(start, (k + 1) * months_per_period) - timedelta(days=1)
        if pt > end:
            break
        n += 1
        k += 1
    return n


def count_monthly_anniversary_periods(start: date, end: date) -> int:
    """
    Number of completed monthly anniversary periods whose Bill To falls within [start, end].
    Bill To of period k = add_months(start, k+1) - 1 day.
    Count k while Bill To <= end.
    Example: 15 Mar 2026 – 15 Mar 2027 → 12 periods (Bill To of period 11 = 14 Mar 2027 ≤ 15 Mar 2027).
    """
    return count_anniversary_periods(start, end, 1)


def _clip_to_agreement(frm: date, to: date, agreement) -> tuple[date | None, date | None]:
    if not agreement.start_date:
        return None, None
    start = max(frm, agreement.start_date)
    if agreement.end_date:
        end = min(to, agreement.end_date)
    else:
        end = to
    if start > end:
        return None, None
    return start, end


def _anniversary_period_for_invoice(
    agreement, ref: date, months_per_period: int,
) -> tuple[date | None, date | None]:
    """
    Latest completed N-month anniversary period whose Bill To is strictly before ref
    (invoice date = mature date = Bill To + 1 day), clipped to the agreement.
    """
    anchor = agreement.start_date
    if not anchor or ref <= anchor or not months_per_period or months_per_period < 1:
        return None, None
    best: tuple[date | None, date | None] = (None, None)
    k = 0
    while k < 5000:
        pf = add_months(anchor, k * months_per_period)
        pt = add_months(anchor, (k + 1) * months_per_period) - timedelta(days=1)
        cpf, cpt = _clip_to_agreement(pf, pt, agreement)
        if cpf is None or cpt is None:
            break
        if ref > cpt:
            best = (cpf, cpt)
        else:
            break
        k += 1
    return best


def _monthly_anniversary_period_for_invoice(agreement, ref: date) -> tuple[date | None, date | None]:
    return _anniversary_period_for_invoice(agreement, ref, 1)


def _quarterly_period_for_invoice(agreement, ref: date) -> tuple[date | None, date | None]:
    return _anniversary_period_for_invoice(agreement, ref, 3)


def _semi_annual_period_for_invoice(agreement, ref: date) -> tuple[date | None, date | None]:
    return _anniversary_period_for_invoice(agreement, ref, 6)


def _annual_period_for_invoice(agreement, ref: date) -> tuple[date | None, date | None]:
    return _anniversary_period_for_invoice(agreement, ref, 12)


def primary_service_type(agreement) -> str:
    s = agreement.services.filter(is_active=True).order_by('id').first()
    return (s.service_type if s else 'monthly') or 'monthly'


def coerce_invoice_date(invoice_date):
    if invoice_date is None:
        return None
    if isinstance(invoice_date, date):
        return invoice_date
    if isinstance(invoice_date, str):
        return parse_date(invoice_date)
    return None


def compute_bill_period_window(agreement, invoice_date) -> tuple[date | None, date | None]:
    if not agreement.start_date:
        return None, None
    ref = coerce_invoice_date(invoice_date)
    if not ref:
        return None, None

    st = primary_service_type(agreement).lower().replace('-', '_')

    if st == 'monthly':
        return _monthly_anniversary_period_for_invoice(agreement, ref)
    if st == 'quarterly':
        return _quarterly_period_for_invoice(agreement, ref)
    if st == 'semi_annual':
        return _semi_annual_period_for_invoice(agreement, ref)
    if st in ('annual', 'yearly'):
        return _annual_period_for_invoice(agreement, ref)
    if st == 'one_time':
        frm, to = _one_time_range(agreement)
        if frm is None:
            return None, None
        return _clip_to_agreement(frm, to, agreement)
    return _monthly_anniversary_period_for_invoice(agreement, ref)


def format_bill_period_line(frm: date | None, to: date | None) -> str:
    if frm and to:
        return f'{frm.strftime("%d %b %Y")} — {to.strftime("%d %b %Y")}'
    return ''
