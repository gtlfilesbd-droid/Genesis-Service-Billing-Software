from django.db import models
from django.contrib.auth.models import User


class Company(models.Model):
    """
    Your organization's companies (billing entity profiles).
    Managed only via Django admin — not exposed in the app sidebar or dashboard.
    """
    name = models.CharField(max_length=255, verbose_name='Company Name')
    short_form = models.CharField(max_length=50, default='', verbose_name='Company Name Short Form')
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(verbose_name='Address')
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, default='Bangladesh')
    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='companies_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Company'
        verbose_name_plural = 'Companies'

    def __str__(self):
        return f"{self.name}" + (f" ({self.short_form})" if self.short_form else "")


class Client(models.Model):
    name = models.CharField(max_length=255, verbose_name='Client Name')
    short_form = models.CharField(max_length=50, default='', verbose_name='Client Name Short Form')
    company = models.CharField(max_length=255, blank=True, null=True, verbose_name='Company')
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(verbose_name='Address')
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, default='Bangladesh')
    tax_id = models.CharField(max_length=50, blank=True, null=True, verbose_name='Tax ID / BIN')
    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='clients_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'

    def __str__(self):
        return f"{self.name}" + (f" ({self.short_form})" if self.short_form else "")

    @property
    def active_agreements(self):
        return self.agreements.filter(is_active=True)


class AgreementTitlePreset(models.Model):
    """Predefined agreement titles — managed in Django admin; users pick from the app form."""

    title = models.CharField(max_length=255)
    sort_order = models.PositiveIntegerField(default=0, help_text='Lower numbers appear first in the dropdown.')
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'title']
        verbose_name = 'Agreement title (preset)'
        verbose_name_plural = 'Agreement title presets'

    def __str__(self):
        return self.title


SERVICE_TYPE_CHOICES = [
    ('monthly', 'Monthly'),
    ('quarterly', 'Quarterly (3 Months)'),
    ('semi_annual', 'Semi-Annual (6 Months)'),
    ('annual', 'Annual (12 Months)'),
    ('one_time', 'One Time'),
]


class Agreement(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='agreements')
    agreement_with = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        related_name='agreements',
        null=True,
        blank=True,
        verbose_name='Agreement With',
    )
    title = models.CharField(max_length=255, verbose_name='Agreement Title')
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)
    attachment = models.FileField(upload_to='agreements/', blank=True, null=True)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Agreement'

    def __str__(self):
        return f"{self.client.name} - {self.title}"

    @staticmethod
    def _months_in_period(start_date, end_date):
        """
        Returns the number of chargeable months between start_date and end_date.
        Rounds up partial months (e.g. Jan 1–Dec 31 => 12, Jan 15–Feb 14 => 1).
        """
        if not start_date or not end_date or end_date <= start_date:
            return 0
        months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
        if end_date.day >= start_date.day:
            months += 1
        return max(months, 0)

    @staticmethod
    def _years_in_period(start_date, end_date):
        """
        Returns the number of chargeable years between start_date and end_date.
        Rounds up partial years (e.g. 2026-01-01 to 2027-12-31 => 2).
        """
        if not start_date or not end_date or end_date <= start_date:
            return 0
        years = end_date.year - start_date.year
        if (end_date.month, end_date.day) >= (start_date.month, start_date.day):
            years += 1
        return max(years, 0)

    @property
    def total_value(self):
        """
        AMC total based on service type + agreement period.

        Rules:
        - monthly: charge * total_months
        - annual/yearly: charge * total_years          (charge is treated as yearly)
        - quarterly/semi_annual: charge * ceil(total_months / N)
        - one_time: charge
        """
        from decimal import Decimal, InvalidOperation
        total = Decimal('0')
        months = self._months_in_period(self.start_date, self.end_date) if self.end_date else 0
        years = self._years_in_period(self.start_date, self.end_date) if self.end_date else 0

        for s in self.services.all():
            try:
                charge = Decimal(str(s.charge or 0))
            except (InvalidOperation, TypeError, ValueError):
                charge = Decimal('0')

            st = (s.service_type or '').lower()
            if st in ('annual', 'yearly'):
                total += charge * Decimal(years or 0)
            elif st == 'monthly':
                total += charge * Decimal(months or 0)
            elif st == 'quarterly':
                periods = (months + 2) // 3 if months else 0
                total += charge * Decimal(periods)
            elif st == 'semi_annual':
                periods = (months + 5) // 6 if months else 0
                total += charge * Decimal(periods)
            elif st == 'one_time':
                total += charge
            else:
                total += charge

        return total


class Service(models.Model):
    agreement = models.ForeignKey(Agreement, on_delete=models.CASCADE, related_name='services')
    # Can contain multiple service names (one per line) when a single charge applies to all.
    name = models.TextField(verbose_name='Service Name')
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPE_CHOICES, default='monthly')
    charge = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Charge (BDT)')
    description = models.TextField(blank=True, null=True, verbose_name='Service Description')
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Service'

    def __str__(self):
        return f"{self.name} - {self.get_service_type_display()} - {self.charge}"

    @property
    def billing_months(self):
        mapping = {
            'monthly': 1,
            'quarterly': 3,
            'semi_annual': 6,
            'annual': 12,
            'one_time': 0,
        }
        return mapping.get(self.service_type, 1)
