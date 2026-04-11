"""
Enumerate completed billing periods inside an agreement (by primary service cadence).
Each yielded period has period_to < today (mature). Invoice date = day after period end.
"""
from __future__ import annotations

from datetime import date, timedelta
import calendar

from .bill_period import (
    _clip_to_agreement,
    _half_range,
    _quarter_range,
    _one_time_range,
    primary_service_type,
)


def _invoice_date_after_period(period_to: date) -> date:
    return period_to + timedelta(days=1)


def iter_monthly_periods(agreement, today: date):
    start = agreement.start_date
    end_inc = agreement.end_date
    y, m = start.year, start.month
    for _ in range(800):
        first = date(y, m, 1)
        last_day = calendar.monthrange(y, m)[1]
        last = date(y, m, last_day)
        if end_inc and first > end_inc:
            break
        pf = max(start, first)
        pt = min(end_inc, last) if end_inc else last
        if pf <= pt and pt < today:
            yield (pf, pt, _invoice_date_after_period(pt))
        if m == 12:
            y, m = y + 1, 1
        else:
            m += 1
        if y > today.year + 3:
            break


def iter_quarterly_periods(agreement, today: date):
    y_end = today.year
    if agreement.end_date:
        y_end = max(y_end, agreement.end_date.year)
    for y in range(agreement.start_date.year, y_end + 1):
        for q in range(1, 5):
            frm, to = _quarter_range(y, q)
            clipped = _clip_to_agreement(frm, to, agreement)
            pf, pt = clipped
            if pf is None or pt is None:
                continue
            if pt < today:
                yield (pf, pt, _invoice_date_after_period(pt))


def iter_semi_annual_periods(agreement, today: date):
    y_end = today.year
    if agreement.end_date:
        y_end = max(y_end, agreement.end_date.year)
    for y in range(agreement.start_date.year, y_end + 1):
        for h in (1, 2):
            frm, to = _half_range(y, h)
            clipped = _clip_to_agreement(frm, to, agreement)
            pf, pt = clipped
            if pf is None or pt is None:
                continue
            if pt < today:
                yield (pf, pt, _invoice_date_after_period(pt))


def iter_annual_periods(agreement, today: date):
    y_end = today.year
    if agreement.end_date:
        y_end = max(y_end, agreement.end_date.year)
    for y in range(agreement.start_date.year, y_end + 1):
        frm, to = date(y, 1, 1), date(y, 12, 31)
        clipped = _clip_to_agreement(frm, to, agreement)
        pf, pt = clipped
        if pf is None or pt is None:
            continue
        if pt < today:
            yield (pf, pt, _invoice_date_after_period(pt))


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
