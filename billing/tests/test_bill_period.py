"""Tests for bill period window computation."""
from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from billing.bill_period import compute_bill_period_window


def _mock_agreement(start, end, service_type):
  return SimpleNamespace(start_date=start, end_date=end)


class BillPeriodWindowTests(SimpleTestCase):
  END = date(2027, 12, 31)

  def _window(self, start, service_type, invoice_date):
    ag = _mock_agreement(start, self.END, service_type)
    with patch(
        'billing.bill_period.primary_service_type',
        return_value=service_type,
    ):
      return compute_bill_period_window(ag, invoice_date)

  def test_quarterly_jun1_invoice_sep1(self):
    got = self._window(date(2026, 6, 1), 'quarterly', date(2026, 9, 1))
    self.assertEqual(got, (date(2026, 6, 1), date(2026, 8, 31)))

  def test_quarterly_jan1_invoice_jul1(self):
    got = self._window(date(2026, 1, 1), 'quarterly', date(2026, 7, 1))
    self.assertEqual(got, (date(2026, 4, 1), date(2026, 6, 30)))

  def test_monthly_apr1_invoice_jul1(self):
    got = self._window(date(2026, 4, 1), 'monthly', date(2026, 7, 1))
    self.assertEqual(got, (date(2026, 6, 1), date(2026, 6, 30)))

  def test_semi_annual_apr1_invoice_oct1(self):
    got = self._window(date(2026, 4, 1), 'semi_annual', date(2026, 10, 1))
    self.assertEqual(got, (date(2026, 4, 1), date(2026, 9, 30)))

  def test_annual_apr1_invoice_apr1_next_year(self):
    got = self._window(date(2026, 4, 1), 'annual', date(2027, 4, 1))
    self.assertEqual(got, (date(2026, 4, 1), date(2027, 3, 31)))
