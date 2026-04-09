from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('clients', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Bill',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bill_number', models.CharField(max_length=50, unique=True, verbose_name='Bill Number')),
                ('invoice_date', models.DateField(default=django.utils.timezone.now, verbose_name='Invoice Date')),
                ('po_date', models.DateField(blank=True, null=True, verbose_name='PO Date')),
                ('bill_period', models.CharField(blank=True, max_length=255, null=True, verbose_name='Bill Period')),
                ('service_period', models.CharField(blank=True, max_length=255, null=True, verbose_name='Service Period')),
                ('project_value_yearly', models.DecimalField(decimal_places=2, default=0, max_digits=14, verbose_name='Project Value Yearly')),
                ('project_base_value', models.DecimalField(decimal_places=2, default=0, max_digits=14, verbose_name='Project Base Value')),
                ('excluding_vat_ait', models.DecimalField(decimal_places=2, default=0, max_digits=14, verbose_name='Excluding VAT & AIT')),
                ('total_in_bdt', models.DecimalField(decimal_places=2, default=0, max_digits=14, verbose_name='Total In BDT')),
                ('subtotal', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('remark', models.TextField(blank=True, null=True, verbose_name='Remark')),
                ('bank_name', models.CharField(blank=True, max_length=255, null=True, verbose_name='Bank Name')),
                ('beneficiary', models.CharField(blank=True, max_length=255, null=True, verbose_name='Beneficiary')),
                ('bank_branch', models.CharField(blank=True, max_length=255, null=True, verbose_name='Branch')),
                ('bank_address_line1', models.CharField(blank=True, max_length=255, null=True, verbose_name='Address Line 1')),
                ('bank_address_line2', models.CharField(blank=True, max_length=255, null=True, verbose_name='Address Line 2')),
                ('account_number', models.CharField(blank=True, max_length=100, null=True, verbose_name='Account Number')),
                ('swift_code', models.CharField(blank=True, max_length=50, null=True, verbose_name='Swift Code')),
                ('branch_routing_code', models.CharField(blank=True, max_length=100, null=True, verbose_name='Branch Code (Routing)')),
                ('bin_number', models.CharField(blank=True, max_length=50, null=True, verbose_name='BIN')),
                ('tin_number', models.CharField(blank=True, max_length=50, null=True, verbose_name='TIN')),
                ('status', models.CharField(choices=[('draft','Draft'),('unpaid','Unpaid'),('paid','Paid'),('overdue','Overdue'),('cancelled','Cancelled')], default='draft', max_length=20)),
                ('payment_date', models.DateField(blank=True, null=True)),
                ('payment_method', models.CharField(blank=True, max_length=100, null=True)),
                ('payment_reference', models.CharField(blank=True, max_length=100, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('agreement', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='clients.agreement')),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bills', to='clients.client')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='bills_created', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-invoice_date', '-created_at'], 'verbose_name': 'Bill', 'verbose_name_plural': 'Bills'},
        ),
        migrations.CreateModel(
            name='BillItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.TextField(verbose_name='Description')),
                ('quantity', models.DecimalField(decimal_places=2, default=1, max_digits=10, verbose_name='Qty')),
                ('unit', models.CharField(blank=True, max_length=100, null=True, verbose_name='Unit')),
                ('unit_price', models.DecimalField(decimal_places=2, default=0, max_digits=14, verbose_name='Price')),
                ('amount', models.DecimalField(decimal_places=2, default=0, max_digits=14, verbose_name='Amount')),
                ('bill', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='billing.bill')),
            ],
            options={'verbose_name': 'Bill Item'},
        ),
    ]
