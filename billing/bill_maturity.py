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


def promote_mature_drafts() -> int:
    """Move draft bills whose service period has ended into Pending. Returns rows updated."""
    from .models import Bill

    today = timezone.localdate()
    return Bill.objects.filter(
        status='draft',
        bill_period_to__isnull=False,
        bill_period_to__lt=today,
    ).update(status='pending')
