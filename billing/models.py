from datetime import date, datetime

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.dateparse import parse_date

from clients.models import Client, Agreement, Service


BILL_STATUS_CHOICES = [
    ('draft', 'Draft'),
    ('unpaid', 'Unpaid'),
    ('paid', 'Paid'),
    ('overdue', 'Overdue'),
    ('cancelled', 'Cancelled'),
]


class Bill(models.Model):
    bill_number = models.CharField(max_length=50, unique=True, verbose_name='Bill Number')
    invoice_number = models.CharField(
        max_length=150,
        unique=True,
        blank=True,
        null=True,
        verbose_name='Invoice Number',
    )
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='bills')
    agreement = models.ForeignKey(Agreement, on_delete=models.SET_NULL, null=True, blank=True)

    # Date fields
    invoice_date = models.DateField(default=timezone.now, verbose_name='Invoice Date')
    po_date = models.DateField(null=True, blank=True, verbose_name='PO Date')

    # Period fields
    bill_period_from = models.DateField(blank=True, null=True, verbose_name='Bill From')
    bill_period_to = models.DateField(blank=True, null=True, verbose_name='Bill To')
    bill_period = models.CharField(max_length=255, blank=True, null=True, verbose_name='Bill Period')
    service_period = models.CharField(max_length=255, blank=True, null=True, verbose_name='Service Period')

    # Financial fields (VAT/AIT derived from items subtotal in calculate_totals)
    project_value_yearly = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name='Project Value Yearly')
    project_base_value = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name='Base Value (BDT)')
    vat_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name='VAT (10%)')
    ait_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name='AIT (5%)')
    excluding_vat_ait = models.DecimalField(
        max_digits=14, decimal_places=2, default=0, verbose_name='Total VAT & AIT',
        help_text='VAT + AIT (15% of base)',
    )
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

    def _coerce_invoice_date(self):
        d = self.invoice_date
        if d is None:
            return date.today()
        if isinstance(d, datetime):
            return d.date()
        if isinstance(d, date):
            return d
        if isinstance(d, str):
            p = parse_date(d)
            return p if p else date.today()
        return date.today()

    def save(self, *args, **kwargs):
        if not self.bill_number:
            self.bill_number = self.generate_bill_number()
        update_fields = kwargs.get('update_fields')
        # Full save only: invoice_number follows invoice_date / client / agreement (create & edit).
        # Partial saves (e.g. subtotal only) skip this so invoice_number is not dropped from the UPDATE.
        if update_fields is None and self.agreement_id and self.client_id:
            from .invoice_number import build_invoice_number_base, allocate_invoice_number

            ag = Agreement.objects.select_related('agreement_with').get(pk=self.agreement_id)
            client = Client.objects.get(pk=self.client_id)
            inv_d = self._coerce_invoice_date()
            base = build_invoice_number_base(ag, client, inv_d)
            self.invoice_number = allocate_invoice_number(base, exclude_bill_pk=self.pk)
        if self.pk:
            self.calculate_totals()
        super().save(*args, **kwargs)

    def generate_bill_number(self):
        from datetime import datetime
        prefix = datetime.now().strftime('INV-%Y%m-')
        last = Bill.objects.filter(bill_number__startswith=prefix).count()
        return f"{prefix}{str(last + 1).zfill(4)}"

    def calculate_totals(self):
        from decimal import Decimal, ROUND_HALF_UP

        q = Decimal('0.01')
        if self.pk:
            base = sum((item.amount for item in self.items.all()), Decimal('0'))
        else:
            base = Decimal('0')
        self.subtotal = base
        self.project_base_value = base
        self.vat_amount = (base * Decimal('0.10')).quantize(q, ROUND_HALF_UP)
        self.ait_amount = (base * Decimal('0.05')).quantize(q, ROUND_HALF_UP)
        self.excluding_vat_ait = self.vat_amount + self.ait_amount
        self.total_in_bdt = base + self.excluding_vat_ait

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
