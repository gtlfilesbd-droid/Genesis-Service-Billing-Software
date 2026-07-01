"""
Enumerate completed billing periods inside an agreement (by primary service cadence).
Each yielded period has period_to < today (mature). Invoice date = day after period end.
"""
from __future__ import annotations

from datetime import date, timedelta

from .bill_period import (
    _clip_to_agreement,
    _one_time_range,
    add_months,
    primary_service_type,
)


def _invoice_date_after_period(period_to: date) -> date:
    return period_to + timedelta(days=1)


def iter_anniversary_periods(agreement, today: date, months_per_period: int):
    """
    Fixed N-month blocks from agreement start_date (anniversary cadence).
    Period k: [add_months(start, k*N), add_months(start, (k+1)*N) - 1 day].
    Yield when bill_period_to < today.
    """
    start = agreement.start_date
    if not start or not months_per_period or months_per_period < 1:
        return
    k = 0
    while k < 5000:
        pf = add_months(start, k * months_per_period)
        pt = add_months(start, (k + 1) * months_per_period) - timedelta(days=1)
        clipped = _clip_to_agreement(pf, pt, agreement)
        c_pf, c_pt = clipped
        if c_pf is None or c_pt is None:
            break
        if c_pt < today:
            yield (c_pf, c_pt, _invoice_date_after_period(c_pt))
        else:
            break
        k += 1


def iter_monthly_periods(agreement, today: date):
    """Anniversary months (months_per_period=1)."""
    yield from iter_anniversary_periods(agreement, today, 1)


def iter_quarterly_periods(agreement, today: date):
    """Anniversary 3-month blocks from start_date."""
    yield from iter_anniversary_periods(agreement, today, 3)


def iter_semi_annual_periods(agreement, today: date):
    """Anniversary 6-month blocks from start_date."""
    yield from iter_anniversary_periods(agreement, today, 6)


def iter_annual_periods(agreement, today: date):
    """Anniversary 12-month blocks from start_date."""
    yield from iter_anniversary_periods(agreement, today, 12)


def iter_one_time_period(agreement, today: date):
    frm, to = _one_time_range(agreement)
    if frm is None:
        return
    clipped = _clip_to_agreement(frm, to, agreement)
    pf, pt = clipped
    if pf is None or pt is None:
        return
    if pt < today:
        yield (pf, pt, _invoice_date_after_period(pt))


def iter_mature_periods_for_agreement(agreement, today: date):
    st = primary_service_type(agreement).lower().replace('-', '_')
    if st == 'monthly':
        yield from iter_monthly_periods(agreement, today)
    elif st == 'quarterly':
        yield from iter_quarterly_periods(agreement, today)
    elif st == 'semi_annual':
        yield from iter_semi_annual_periods(agreement, today)
    elif st in ('annual', 'yearly'):
        yield from iter_annual_periods(agreement, today)
    elif st == 'one_time':
        yield from iter_one_time_period(agreement, today)
    else:
        yield from iter_monthly_periods(agreement, today)
