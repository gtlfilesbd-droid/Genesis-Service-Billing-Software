from django.db import models
from django.contrib.auth.models import User


class Client(models.Model):
    name = models.CharField(max_length=255, verbose_name='Client Name')
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
        return f"{self.name}" + (f" ({self.company})" if self.company else "")

    @property
    def active_agreements(self):
        return self.agreements.filter(is_active=True)


SERVICE_TYPE_CHOICES = [
    ('monthly', 'Monthly'),
    ('quarterly', 'Quarterly (3 Months)'),
    ('semi_annual', 'Semi-Annual (6 Months)'),
    ('annual', 'Annual (12 Months)'),
    ('one_time', 'One Time'),
]


class Agreement(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='agreements')
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

    @property
    def total_value(self):
        return sum(s.charge for s in self.services.all())


class Service(models.Model):
    agreement = models.ForeignKey(Agreement, on_delete=models.CASCADE, related_name='services')
    name = models.CharField(max_length=255, verbose_name='Service Name')
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
