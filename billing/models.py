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


class BillingTaxSettings(models.Model):
    """Singleton (pk=1): global VAT % and AIT % of base. Edit in Django Admin."""

    class Meta:
        verbose_name = 'Billing tax rates'
        verbose_name_plural = 'Billing tax rates'

    vat_percent = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=10,
        help_text='Default VAT % for new bills; each bill can use its own % on the bill form (0 if no VAT).',
    )
    ait_percent = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=5,
        help_text='Default AIT % for new bills; each bill can use its own % on the bill form (0 if no AIT).',
    )

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        return

    def __str__(self):
        return f'VAT {self.vat_percent}%, AIT {self.ait_percent}%'

    @classmethod
    def get_solo(cls):
        from decimal import Decimal

        obj, _ = cls.objects.get_or_create(
            pk=1,
            defaults={'vat_percent': Decimal('10'), 'ait_percent': Decimal('5')},
        )
        return obj


class BillingBank(models.Model):
    """Multiple bank profiles; one can be marked default for new bills. Managed in Admin."""

    class Meta:
        ordering = ['-is_default', 'label']
        verbose_name = 'Billing bank'
        verbose_name_plural = 'Billing banks'

    label = models.CharField(
        max_length=120,
        help_text='Short name shown in the bill form dropdown (e.g. DBBL Main).',
    )
    is_default = models.BooleanField(default=False, verbose_name='Default for new bills')
    bank_name = models.CharField(max_length=255, blank=True, verbose_name='Bank Name')
    beneficiary = models.CharField(max_length=255, blank=True, verbose_name='Beneficiary')
    bank_branch = models.CharField(max_length=255, blank=True, verbose_name='Branch')
    bank_address_line1 = models.CharField(max_length=255, blank=True, verbose_name='Address Line 1')
    bank_address_line2 = models.CharField(max_length=255, blank=True, verbose_name='Address Line 2')
    account_number = models.CharField(max_length=100, blank=True, verbose_name='Account Number')
    swift_code = models.CharField(max_length=50, blank=True, verbose_name='Swift Code')
    branch_routing_code = models.CharField(max_length=100, blank=True, verbose_name='Branch Code (Routing)')
    bin_number = models.CharField(max_length=50, blank=True, verbose_name='BIN')
    tin_number = models.CharField(max_length=50, blank=True, verbose_name='TIN')

    def __str__(self):
        d = ' (default)' if self.is_default else ''
        return f'{self.label}{d}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_default:
            BillingBank.objects.exclude(pk=self.pk).update(is_default=False)

    def copy_to_bill(self, bill):
        bill.bank_name = self.bank_name or ''
        bill.beneficiary = self.beneficiary or ''
        bill.bank_branch = self.bank_branch or ''
        bill.bank_address_line1 = self.bank_address_line1 or ''
        bill.bank_address_line2 = self.bank_address_line2 or ''
        bill.account_number = self.account_number or ''
        bill.swift_code = self.swift_code or ''
        bill.branch_routing_code = self.branch_routing_code or ''
        bill.bin_number = self.bin_number or ''
        bill.tin_number = self.tin_number or ''

    @classmethod
    def get_default(cls):
        """Only a profile explicitly marked default; no fallback to the first row."""
        return cls.objects.filter(is_default=True).first()

    @staticmethod
    def clear_bill_bank_fields(bill):
        bill.bank_name = ''
        bill.beneficiary = ''
        bill.bank_branch = ''
        bill.bank_address_line1 = ''
        bill.bank_address_line2 = ''
        bill.account_number = ''
        bill.swift_code = ''
        bill.branch_routing_code = ''
        bill.bin_number = ''
        bill.tin_number = ''


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
    vat_rate_percent = models.DecimalField(
        max_digits=6, decimal_places=2, default=10, verbose_name='VAT rate applied (%)',
    )
    ait_rate_percent = models.DecimalField(
        max_digits=6, decimal_places=2, default=5, verbose_name='AIT rate applied (%)',
    )
    vat_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name='VAT')
    ait_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name='AIT')
    excluding_vat_ait = models.DecimalField(
        max_digits=14, decimal_places=2, default=0, verbose_name='Total VAT & AIT',
        help_text='VAT + AIT',
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
    billing_bank = models.ForeignKey(
        'BillingBank',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bills',
        verbose_name='Bank profile',
    )

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
        # Full save only: auto invoice # from client/agreement/date (new bills). Edit form can skip via flag.
        if (
            update_fields is None
            and self.agreement_id
            and self.client_id
            and not getattr(self, '_skip_auto_invoice_number', False)
        ):
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
        vat_p = Decimal(str(self.vat_rate_percent or 0))
        ait_p = Decimal(str(self.ait_rate_percent or 0))
        self.vat_amount = (base * vat_p / Decimal('100')).quantize(q, ROUND_HALF_UP)
        self.ait_amount = (base * ait_p / Decimal('100')).quantize(q, ROUND_HALF_UP)
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

    @property
    def description_lines(self):
        """Non-empty lines for display (bill detail / PDF); single line if no newlines."""
        text = (self.description or '').strip()
        if not text:
            return []
        lines = [ln.strip() for ln in self.description.splitlines() if ln.strip()]
        return lines if lines else [text]
