"""
Bill From / Bill To: the last *completed* billing cycle before the invoice month,
clipped to agreement dates. Anchor = invoice date (billing month).

- Monthly: previous calendar month (e.g. invoice Apr 2026 → 01 Mar – 31 Mar 2026).
- Quarterly: previous calendar quarter (e.g. invoice Apr 2026 → 01 Jan – 31 Mar 2026).
- Semi-annual: previous Jan–Jun or Jul–Dec block (e.g. invoice Apr 2026 → 01 Jul – 31 Dec 2025).
- Annual: previous calendar year (e.g. invoice 2026 → 01 Jan – 31 Dec 2025).
- One-time: agreement start_date through end_date (or start if open-ended).

If multiple active services exist, the first by id sets the cadence (same as single-row convention).
"""
from datetime import date, timedelta
import calendar

from django.utils.dateparse import parse_date


def _first_day_month(d: date) -> date:
    return date(d.year, d.month, 1)


def _prev_month_closed_range(ref: date) -> tuple[date, date]:
    first = _first_day_month(ref)
    last_prev = first - timedelta(days=1)
    first_prev = date(last_prev.year, last_prev.month, 1)
    return first_prev, last_prev


def _quarter_index(month: int) -> int:
    return (month - 1) // 3 + 1


def _quarter_range(year: int, q: int) -> tuple[date, date]:
    start_month = 3 * (q - 1) + 1
    end_month = start_month + 2
    start = date(year, start_month, 1)
    last_day = calendar.monthrange(year, end_month)[1]
    end = date(year, end_month, last_day)
    return start, end


def _prev_quarter_closed_range(ref: date) -> tuple[date, date]:
    q = _quarter_index(ref.month)
    y = ref.year
    if q == 1:
        pq, py = 4, y - 1
    else:
        pq, py = q - 1, y
    return _quarter_range(py, pq)


def _half_index(month: int) -> int:
    return 1 if month <= 6 else 2


def _half_range(year: int, h: int) -> tuple[date, date]:
    if h == 1:
        return date(year, 1, 1), date(year, 6, 30)
    return date(year, 7, 1), date(year, 12, 31)


def _prev_half_closed_range(ref: date) -> tuple[date, date]:
    h = _half_index(ref.month)
    y = ref.year
    if h == 1:
        ph, py = 2, y - 1
    else:
        ph, py = 1, y
    return _half_range(py, ph)


def _prev_year_closed_range(ref: date) -> tuple[date, date]:
    y = ref.year - 1
    return date(y, 1, 1), date(y, 12, 31)


def _one_time_range(agreement) -> tuple[date, date]:
    s = agreement.start_date
    if not s:
        return None, None  # type: ignore
    e = agreement.end_date or s
    return s, e


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
        frm, to = _prev_month_closed_range(ref)
    elif st == 'quarterly':
        frm, to = _prev_quarter_closed_range(ref)
    elif st == 'semi_annual':
        frm, to = _prev_half_closed_range(ref)
    elif st in ('annual', 'yearly'):
        frm, to = _prev_year_closed_range(ref)
    elif st == 'one_time':
        frm, to = _one_time_range(agreement)
        if frm is None:
            return None, None
        return _clip_to_agreement(frm, to, agreement)
    else:
        frm, to = _prev_month_closed_range(ref)

    return _clip_to_agreement(frm, to, agreement)


def format_bill_period_line(frm: date | None, to: date | None) -> str:
    if frm and to:
        return f'{frm.strftime("%d %b %Y")} — {to.strftime("%d %b %Y")}'
    return ''
