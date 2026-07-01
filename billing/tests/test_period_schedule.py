"""Tests for mature billing period enumeration."""
from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from billing.period_schedule import iter_mature_periods_for_agreement


def _mock_agreement(start, end, service_type):
  return SimpleNamespace(start_date=start, end_date=end, _service_type=service_type)


def _patch_primary(st):
  return patch(
      'billing.period_schedule.primary_service_type',
      return_value=st,
  )


class MaturePeriodScheduleTests(SimpleTestCase):
  END = date(2027, 12, 31)

  def _periods(self, start, service_type, today):
    ag = _mock_agreement(start, self.END, service_type)
    with _patch_primary(service_type):
      return list(iter_mature_periods_for_agreement(ag, today))

  def test_monthly_apr1_jul1(self):
    got = self._periods(date(2026, 4, 1), 'monthly', date(2026, 7, 1))
    self.assertEqual(got, [
        (date(2026, 4, 1), date(2026, 4, 30), date(2026, 5, 1)),
        (date(2026, 5, 1), date(2026, 5, 31), date(2026, 6, 1)),
        (date(2026, 6, 1), date(2026, 6, 30), date(2026, 7, 1)),
    ])

  def test_quarterly_jan1_aligned_jul1(self):
    got = self._periods(date(2026, 1, 1), 'quarterly', date(2026, 7, 1))
    self.assertEqual(got, [
        (date(2026, 1, 1), date(2026, 3, 31), date(2026, 4, 1)),
        (date(2026, 4, 1), date(2026, 6, 30), date(2026, 7, 1)),
    ])

  def test_quarterly_jun1_misaligned_jul1_no_bill(self):
    got = self._periods(date(2026, 6, 1), 'quarterly', date(2026, 7, 1))
    self.assertEqual(got, [])

  def test_quarterly_jun1_mature_sep1(self):
    got = self._periods(date(2026, 6, 1), 'quarterly', date(2026, 9, 1))
    self.assertEqual(got, [
        (date(2026, 6, 1), date(2026, 8, 31), date(2026, 9, 1)),
    ])

  def test_quarterly_jul1_aligned_jul1_no_bill(self):
    got = self._periods(date(2026, 7, 1), 'quarterly', date(2026, 7, 1))
    self.assertEqual(got, [])

  def test_quarterly_feb15_jul1(self):
    got = self._periods(date(2026, 2, 15), 'quarterly', date(2026, 7, 1))
    self.assertEqual(got, [
        (date(2026, 2, 15), date(2026, 5, 14), date(2026, 5, 15)),
    ])

  def test_semi_annual_apr1_jul1_no_bill(self):
    got = self._periods(date(2026, 4, 1), 'semi_annual', date(2026, 7, 1))
    self.assertEqual(got, [])

  def test_semi_annual_apr1_oct1(self):
    got = self._periods(date(2026, 4, 1), 'semi_annual', date(2026, 10, 1))
    self.assertEqual(got, [
        (date(2026, 4, 1), date(2026, 9, 30), date(2026, 10, 1)),
    ])

  def test_annual_jan1_jul1_no_bill(self):
    got = self._periods(date(2026, 1, 1), 'annual', date(2026, 7, 1))
    self.assertEqual(got, [])

  def test_annual_apr1_jul1_no_bill(self):
    got = self._periods(date(2026, 4, 1), 'annual', date(2026, 7, 1))
    self.assertEqual(got, [])

  def test_annual_apr1_apr1_next_year(self):
    got = self._periods(date(2026, 4, 1), 'annual', date(2027, 4, 1))
    self.assertEqual(got, [
        (date(2026, 4, 1), date(2027, 3, 31), date(2027, 4, 1)),
    ])

  def test_one_time_not_mature_before_end(self):
    start = date(2026, 6, 1)
    end = date(2026, 12, 31)
    ag = _mock_agreement(start, end, 'one_time')
    with _patch_primary('one_time'):
      got = list(iter_mature_periods_for_agreement(ag, date(2026, 7, 1)))
    self.assertEqual(got, [])

  def test_one_time_mature_after_end(self):
    start = date(2026, 6, 1)
    end = date(2026, 6, 30)
    ag = _mock_agreement(start, end, 'one_time')
    with _patch_primary('one_time'):
      got = list(iter_mature_periods_for_agreement(ag, date(2026, 7, 1)))
    self.assertEqual(got, [
        (date(2026, 6, 1), date(2026, 6, 30), date(2026, 7, 1)),
    ])
