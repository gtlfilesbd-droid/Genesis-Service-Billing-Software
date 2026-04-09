from django.db import models
from django.contrib.auth.models import User
from clients.models import Client, Agreement, Service
from django.utils import timezone


BILL_STATUS_CHOICES = [
    ('draft', 'Draft'),
    ('unpaid', 'Unpaid'),
    ('paid', 'Paid'),
    ('overdue', 'Overdue'),
    ('cancelled', 'Cancelled'),
]


class Bill(models.Model):
    bill_number = models.CharField(max_length=50, unique=True, verbose_name='Bill Number')
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='bills')
    agreement = models.ForeignKey(Agreement, on_delete=models.SET_NULL, null=True, blank=True)

    # Date fields
    invoice_date = models.DateField(default=timezone.now, verbose_name='Invoice Date')
    po_date = models.DateField(null=True, blank=True, verbose_name='PO Date')

    # Period fields (plain text)
    bill_period = models.CharField(max_length=255, blank=True, null=True, verbose_name='Bill Period')
    service_period = models.CharField(max_length=255, blank=True, null=True, verbose_name='Service Period')

    # Financial fields
    project_value_yearly = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name='Project Value Yearly')
    project_base_value = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name='Project Base Value')
    excluding_vat_ait = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name='Excluding VAT & AIT')
    total_in_bdt = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name='Total In BDT')

    # Calculated totals (from items)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    # Remark
    remark = models.TextField(blank=True, null=True, verbose_name='Remark')

    # Bank Information
    bank_name = models.CharField(max_length=255, blank=True, null=True, verbose_name='Bank Name')
    beneficiary = models.CharField(max_length=255, blank=True, null=True, verbose_name='Beneficiary')
    bank_branch = models.CharField(max_length=255, blank=True, null=True, verbose_name='Branch')
    bank_address_line1 = models.CharField(max_length=255, blank=True, null=True, verbose_name='Address Line 1')
    bank_address_line2 = models.CharField(max_length=255, blank=True, null=True, verbose_name='Address Line 2')
    account_number = models.CharField(max_length=100, blank=True, null=True, verbose_name='Account Number')
    swift_code = models.CharField(max_length=50, blank=True, null=True, verbose_name='Swift Code')
    branch_routing_code = models.CharField(max_length=100, blank=True, null=True, verbose_name='Branch Code (Routing)')
    bin_number = models.CharField(max_length=50, blank=True, null=True, verbose_name='BIN')
    tin_number = models.CharField(max_length=50, blank=True, null=True, verbose_name='TIN')

    # Status & meta
    status = models.CharField(max_length=20, choices=BILL_STATUS_CHOICES, default='draft')
    payment_date = models.DateField(blank=True, null=True)
    payment_method = models.CharField(max_length=100, blank=True, null=True)
    payment_reference = models.CharField(max_length=100, blank=True, null=True)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='bills_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-invoice_date', '-created_at']
        verbose_name = 'Bill'
        verbose_name_plural = 'Bills'

    def __str__(self):
        return f"Bill #{self.bill_number} - {self.client.name}"

    def save(self, *args, **kwargs):
        if not self.bill_number:
            self.bill_number = self.generate_bill_number()
        if self.pk:
            self.calculate_totals()
        super().save(*args, **kwargs)

    def generate_bill_number(self):
        from datetime import datetime
        prefix = datetime.now().strftime('INV-%Y%m-')
        last = Bill.objects.filter(bill_number__startswith=prefix).count()
        return f"{prefix}{str(last + 1).zfill(4)}"

    def calculate_totals(self):
        if self.pk:
            self.subtotal = sum(item.amount for item in self.items.all())
        else:
            self.subtotal = 0

    @property
    def is_overdue(self):
        from datetime import date
        return self.status == 'unpaid' and self.invoice_date < date.today()


class BillItem(models.Model):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='items')
    description = models.TextField(verbose_name='Description')
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1, verbose_name='Qty')
    unit = models.CharField(max_length=100, blank=True, null=True, verbose_name='Unit')
    unit_price = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name='Price')
    amount = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name='Amount')

    class Meta:
        verbose_name = 'Bill Item'

    def __str__(self):
        return f"{self.description[:50]} - {self.amount}"

    def save(self, *args, **kwargs):
        from decimal import Decimal
        qty = Decimal(str(self.quantity or 0))
        price = Decimal(str(self.unit_price or 0))
        self.amount = qty * price
        super().save(*args, **kwargs)
