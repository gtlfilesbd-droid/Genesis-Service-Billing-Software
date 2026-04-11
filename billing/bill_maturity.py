"""
Bill maturity: service period (Bill To) has ended — bill is ready for the Pending queue.

Uses bill_period_to vs today (strictly after end date), same period rules as bill_period.py.
"""
from django.utils import timezone


def bill_is_mature(bill, today=None) -> bool:
    if today is None:
        today = timezone.localdate()
    if bill.bill_period_to is None:
        return False
    return today > bill.bill_period_to
