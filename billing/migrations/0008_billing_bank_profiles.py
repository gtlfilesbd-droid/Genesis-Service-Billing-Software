from django.db import migrations, models
import django.db.models.deletion


def migrate_singleton_to_banks(apps, schema_editor):
    Old = apps.get_model('billing', 'BillingBankSettings')
    New = apps.get_model('billing', 'BillingBank')
    try:
        old = Old.objects.get(pk=1)
    except Old.DoesNotExist:
        return
    label = (old.bank_name or 'Default')[:120] if old.bank_name else 'Default'
    New.objects.create(
        label=label,
        is_default=True,
        bank_name=old.bank_name or '',
        beneficiary=old.beneficiary or '',
        bank_branch=old.bank_branch or '',
        bank_address_line1=old.bank_address_line1 or '',
        bank_address_line2=old.bank_address_line2 or '',
        account_number=old.account_number or '',
        swift_code=old.swift_code or '',
        branch_routing_code=old.branch_routing_code or '',
        bin_number=old.bin_number or '',
        tin_number=old.tin_number or '',
    )


def assign_bill_fk(apps, schema_editor):
    Bill = apps.get_model('billing', 'Bill')
    BillingBank = apps.get_model('billing', 'BillingBank')
    first = BillingBank.objects.order_by('-is_default', 'pk').first()
    if first:
        Bill.objects.all().update(billing_bank_id=first.pk)


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0007_billing_bank_settings'),
    ]

    operations = [
        migrations.CreateModel(
            name='BillingBank',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(help_text='Short name shown in the bill form dropdown (e.g. DBBL Main).', max_length=120)),
                ('is_default', models.BooleanField(default=False, verbose_name='Default for new bills')),
                ('bank_name', models.CharField(blank=True, max_length=255, verbose_name='Bank Name')),
                ('beneficiary', models.CharField(blank=True, max_length=255, verbose_name='Beneficiary')),
                ('bank_branch', models.CharField(blank=True, max_length=255, verbose_name='Branch')),
                ('bank_address_line1', models.CharField(blank=True, max_length=255, verbose_name='Address Line 1')),
                ('bank_address_line2', models.CharField(blank=True, max_length=255, verbose_name='Address Line 2')),
                ('account_number', models.CharField(blank=True, max_length=100, verbose_name='Account Number')),
                ('swift_code', models.CharField(blank=True, max_length=50, verbose_name='Swift Code')),
                ('branch_routing_code', models.CharField(blank=True, max_length=100, verbose_name='Branch Code (Routing)')),
                ('bin_number', models.CharField(blank=True, max_length=50, verbose_name='BIN')),
                ('tin_number', models.CharField(blank=True, max_length=50, verbose_name='TIN')),
            ],
            options={
                'verbose_name': 'Billing bank',
                'verbose_name_plural': 'Billing banks',
                'ordering': ['-is_default', 'label'],
            },
        ),
        migrations.AddField(
            model_name='bill',
            name='billing_bank',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='bills',
                to='billing.billingbank',
                verbose_name='Bank profile',
            ),
        ),
        migrations.RunPython(migrate_singleton_to_banks, migrations.RunPython.noop),
        migrations.RunPython(assign_bill_fk, migrations.RunPython.noop),
        migrations.DeleteModel(name='BillingBankSettings'),
    ]
